"""
Tests para el CRUD de staff del rubro RECYCLING (compra/venta de catalíticos
y chatarra electrónica) — taller/reciclaje/views_staff.py.

Catalitico y ProductoChatarra son SKU con cantidad_stock (no una fila por
unidad física). Comprar incrementa cantidad_stock (crea el SKU si el código
es nuevo); vender decrementa cantidad_stock y marca el Catalitico como
VENDIDO cuando llega a 0. Cubre:
    - Control de acceso (login + role_required Owner/Admin).
    - Compra: crea catalítico nuevo, hace restock de uno existente,
      incrementa stock de chatarra, rechaza envíos vacíos/códigos duplicados.
    - Venta: decrementa stock, marca VENDIDO al agotar, rechaza stock
      insuficiente sin dejar filas parciales (atomicidad).
    - Aislamiento multi-tenant en todas las vistas (listar/detalle/editar/
      eliminar/crear).
"""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import Client, RequestFactory

from taller.models.reciclaje import (
    Catalitico,
    CategoriaChatarra,
    CompraReciclaje,
    DetalleCompraCatalitico,
    DetalleCompraChatarra,
    ProductoChatarra,
    VentaReciclaje,
)
from taller.models.team_member import TeamMember
from taller.reciclaje.views_staff import resumen_stock
from taller.tests.factories import CataliticoFactory, EmpresaFactory, ProductoChatarraFactory


@pytest.fixture
def empresa_a(db):
    owner = User.objects.create_user("rec_owner_a", "rec_a@example.com", "pass1234")
    return EmpresaFactory(user=owner, nombre_taller="Reciclaje A", pais="CL")


@pytest.fixture
def empresa_b(db):
    owner = User.objects.create_user("rec_owner_b", "rec_b@example.com", "pass1234")
    return EmpresaFactory(user=owner, nombre_taller="Reciclaje B", pais="CL")


@pytest.fixture
def cliente_owner(empresa_a):
    client = Client()
    client.force_login(empresa_a.user)
    return client


@pytest.fixture
def vendedor_user(db, empresa_a):
    """Rol que NO está en role_required('Owner', 'Admin') -> debe recibir 403."""
    user = User.objects.create_user("rec_vendedor", "rec_vend@example.com", "pass1234")
    TeamMember.objects.create(user=user, empresa=empresa_a, rol="Vendedor")
    return user


# ── Control de acceso ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_dashboard_requiere_login():
    response = Client().get("/cl/es/reciclaje/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_dashboard_bloquea_rol_no_autorizado(vendedor_user):
    client = Client()
    client.force_login(vendedor_user)
    response = client.get("/cl/es/reciclaje/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_dashboard_permite_owner(cliente_owner):
    response = cliente_owner.get("/cl/es/reciclaje/")
    assert response.status_code == 200


# ── Dashboard: gráficas y agregados ───────────────────────────────────────────


@pytest.mark.django_db
def test_dashboard_incluye_chart_data_json(cliente_owner):
    response = cliente_owner.get("/cl/es/reciclaje/")
    assert response.status_code == 200
    data = response.context["chart_data_json"]
    assert '"compras_diarias"' in data
    assert '"compras_mensuales"' in data
    assert '"rangos_precio"' in data
    assert '"top_cataliticos"' in data
    content = response.content.decode()
    assert 'id="chart-compras-7d"' in content
    assert 'id="chart-top-cataliticos"' in content


@pytest.mark.django_db
def test_dashboard_top_clientes_suma_correctamente_compra_multilinea(cliente_owner, empresa_a):
    """Regresión: el dashboard original (PythonAnywhere) calculaba el gasto
    de cada cliente multiplicando dos Sum() agregados entre sí
    (Sum(cantidad) * Sum(precio_unitario)), lo que da un total incorrecto
    apenas una compra tiene más de una línea. Debe sumarse por línea."""
    cat1 = CataliticoFactory(empresa=empresa_a, codigo="CAT-X1", precio_venta=Decimal("10000"))
    cat2 = CataliticoFactory(empresa=empresa_a, codigo="CAT-X2", precio_venta=Decimal("20000"))
    compra = CompraReciclaje.objects.create(empresa=empresa_a, cliente=None)
    DetalleCompraCatalitico.objects.create(
        compra=compra, catalitico=cat1, cantidad=2, precio_unitario=Decimal("5000")
    )
    DetalleCompraCatalitico.objects.create(
        compra=compra, catalitico=cat2, cantidad=1, precio_unitario=Decimal("30000")
    )
    # Total correcto: (2*5000) + (1*30000) = 40000.
    # El bug original habría dado Sum(cantidad)=3 * Sum(precio_unitario)=35000 = 105000.

    response = cliente_owner.get("/cl/es/reciclaje/")

    top_clientes = response.context["top_clientes"]
    assert len(top_clientes) == 1
    assert top_clientes[0]["total"] == Decimal("40000")


@pytest.mark.django_db
def test_dashboard_rangos_precio_y_extremos(cliente_owner, empresa_a):
    CataliticoFactory(empresa=empresa_a, codigo="BARATO", precio_venta=Decimal("5000"))
    CataliticoFactory(empresa=empresa_a, codigo="CARO", precio_venta=Decimal("60000"))

    response = cliente_owner.get("/cl/es/reciclaje/")

    assert response.context["catalitico_mas_caro"].codigo == "CARO"
    assert response.context["catalitico_mas_barato"].codigo == "BARATO"


@pytest.mark.django_db
def test_dashboard_formatea_montos_como_clp(cliente_owner, empresa_a):
    CataliticoFactory(empresa=empresa_a, codigo="CLP-1", precio_venta=Decimal("1234567"))

    response = cliente_owner.get("/cl/es/reciclaje/")
    content = response.content.decode()

    assert "$1.234.567" in content
    assert "$1.234.567 CLP" not in content


@pytest.mark.django_db
def test_dashboard_no_mezcla_datos_de_otra_empresa(cliente_owner, empresa_a, empresa_b):
    CataliticoFactory(empresa=empresa_b, codigo="OTRA-EMPRESA", precio_venta=Decimal("999999"))

    response = cliente_owner.get("/cl/es/reciclaje/")

    assert "OTRA-EMPRESA" not in response.content.decode()
    if response.context["catalitico_mas_caro"] is not None:
        assert response.context["catalitico_mas_caro"].empresa_id == empresa_a.pk


# ── Stock: catálogo de materiales ─────────────────────────────────────────────


@pytest.mark.django_db
def test_stock_muestra_accion_nuevo_producto(cliente_owner):
    response = cliente_owner.get("/cl/es/reciclaje/stock/")

    assert response.status_code == 200
    content = response.content.decode()
    assert ">+ Nuevo producto<" in content
    assert ">+ Nueva categoría<" in content
    assert 'href="productos/nuevo/"' in content
    assert 'href="categorias/nueva/"' in content


@pytest.mark.django_db
def test_stock_respeta_empresa_resuelta_por_qa_context(empresa_a, empresa_b):
    """QA Control reemplaza request.empresa. Las vistas de reciclaje deben
    consultar ese tenant, no la empresa propietaria del usuario superadmin."""
    categoria_a = CategoriaChatarra.objects.create(empresa=empresa_a, nombre="Metales QA")
    categoria_b = CategoriaChatarra.objects.create(empresa=empresa_b, nombre="Metales ocultos")
    ProductoChatarraFactory(
        empresa=empresa_a,
        categoria=categoria_a,
        nombre="Cobre QA",
        codigo="COBRE-QA",
    )
    ProductoChatarraFactory(
        empresa=empresa_b,
        categoria=categoria_b,
        nombre="Producto oculto",
        codigo="OTRO-QA",
    )

    request = RequestFactory().get(f"/cl/es/reciclaje/stock/?categoria={categoria_a.pk}")
    request.user = empresa_b.user
    request.empresa = empresa_a
    request.company = empresa_a

    response = resumen_stock(request)
    content = response.content.decode()

    assert response.status_code == 200
    assert "Cobre QA" in content
    assert "Producto oculto" not in content


@pytest.mark.django_db
def test_crear_producto_chatarra_crea_material_para_empresa(cliente_owner, empresa_a):
    response = cliente_owner.post(
        "/cl/es/reciclaje/stock/productos/nuevo/",
        {
            "codigo": "cobre-01",
            "nombre": "Cobre limpio",
            "categoria": "Metales",
            "unidad_medida": ProductoChatarra.UNIDAD_KG,
            "precio_compra": "4500",
            "precio_venta": "5200",
            "cantidad_stock": "12.5",
            "stock_minimo": "3",
            "proveedor": "Mostrador",
        },
    )

    assert response.status_code == 302
    producto = ProductoChatarra.objects.get(empresa=empresa_a, codigo="COBRE-01")
    assert producto.nombre == "Cobre limpio"
    assert producto.categoria.nombre == "Metales"
    assert producto.precio_compra == Decimal("4500")
    assert producto.precio_venta == Decimal("5200")
    assert producto.cantidad_stock == Decimal("12.5")
    assert producto.stock_minimo == Decimal("3")
    assert CategoriaChatarra.objects.filter(empresa=empresa_a, nombre="Metales").count() == 1


@pytest.mark.django_db
def test_crear_categoria_chatarra_crea_categoria_para_empresa(cliente_owner, empresa_a):
    response = cliente_owner.post(
        "/cl/es/reciclaje/stock/categorias/nueva/",
        {
            "nombre": "Plásticos",
            "descripcion": "Material plástico comprado por kilo.",
        },
    )

    assert response.status_code == 302
    categoria = CategoriaChatarra.objects.get(empresa=empresa_a, nombre="Plásticos")
    assert categoria.descripcion == "Material plástico comprado por kilo."


@pytest.mark.django_db
def test_stock_segrega_materiales_por_categoria(cliente_owner, empresa_a):
    metales = CategoriaChatarra.objects.create(empresa=empresa_a, nombre="Metales")
    papel = CategoriaChatarra.objects.create(empresa=empresa_a, nombre="Papel y cartón")
    CataliticoFactory(empresa=empresa_a, codigo="CAT-OCULTO")
    ProductoChatarraFactory(empresa=empresa_a, categoria=metales, nombre="Cobre limpio")
    ProductoChatarraFactory(empresa=empresa_a, categoria=papel, nombre="Papel reciclado")

    response = cliente_owner.get("/cl/es/reciclaje/stock/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Cobre limpio" not in content
    assert "Papel reciclado" not in content
    assert "Selecciona una categoría" in content

    response = cliente_owner.get(f"/cl/es/reciclaje/stock/?categoria={metales.pk}")
    content = response.content.decode()

    assert "Cobre limpio" in content
    assert "Papel reciclado" not in content
    assert "Catalíticos disponibles" not in content
    assert "CAT-OCULTO" not in content


# ── Compra: catalítico ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_crear_compra_catalitico_nuevo_crea_sku(cliente_owner, empresa_a):
    response = cliente_owner.post(
        "/cl/es/reciclaje/compras/nueva/",
        {
            "catalitico_codigo[]": ["CAT-NEW-1"],
            "catalitico_nombre[]": ["Toyota Corolla"],
            "catalitico_marca[]": ["Toyota"],
            "catalitico_modelo[]": ["Corolla"],
            "catalitico_cantidad[]": ["3"],
            "catalitico_precio[]": ["15000"],
        },
    )
    assert response.status_code == 302
    catalitico = Catalitico.objects.get(empresa=empresa_a, codigo="CAT-NEW-1")
    assert catalitico.cantidad_stock == 3
    assert catalitico.estado == Catalitico.ESTADO_DISPONIBLE
    assert catalitico.precio_compra == Decimal("15000")

    compra = CompraReciclaje.objects.get(empresa=empresa_a)
    detalle = compra.detalles_catalitico.get()
    assert detalle.cantidad == 3
    assert detalle.precio_unitario == Decimal("15000")
    assert compra.total() == Decimal("45000")


@pytest.mark.django_db
def test_crear_compra_catalitico_existente_hace_restock(cliente_owner, empresa_a):
    catalitico = CataliticoFactory(
        empresa=empresa_a,
        codigo="CAT-RESTOCK",
        cantidad_stock=2,
        estado=Catalitico.ESTADO_VENDIDO,
    )

    cliente_owner.post(
        "/cl/es/reciclaje/compras/nueva/",
        {
            "catalitico_codigo[]": ["CAT-RESTOCK"],
            "catalitico_nombre[]": [""],
            "catalitico_marca[]": [""],
            "catalitico_modelo[]": [""],
            "catalitico_cantidad[]": ["5"],
            "catalitico_precio[]": ["9000"],
        },
    )

    catalitico.refresh_from_db()
    assert catalitico.cantidad_stock == 7  # 2 + 5
    assert catalitico.estado == Catalitico.ESTADO_DISPONIBLE  # reactivado
    assert Catalitico.objects.filter(empresa=empresa_a, codigo="CAT-RESTOCK").count() == 1


@pytest.mark.django_db
def test_api_catalitico_por_codigo_devuelve_datos_para_autocompletar(cliente_owner, empresa_a):
    CataliticoFactory(
        empresa=empresa_a,
        codigo="AUTO-1",
        nombre="Toyota Corolla",
        marca_vehiculo="Toyota",
        modelo_vehiculo="Corolla",
        precio_compra=Decimal("15000.00"),
        cantidad_stock=3,
    )

    response = cliente_owner.get(
        "/cl/es/reciclaje/api/catalitico-por-codigo/", {"codigo": "auto-1"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["nombre"] == "Toyota Corolla"
    assert data["marca_vehiculo"] == "Toyota"
    assert data["modelo_vehiculo"] == "Corolla"
    assert data["precio_compra"] == "15000.00"
    assert data["cantidad_stock"] == 3
    assert data["codigo"] == "AUTO-1"
    assert data["suggestions"][0]["codigo"] == "AUTO-1"


@pytest.mark.django_db
def test_api_catalitico_por_codigo_no_encontrado(cliente_owner, empresa_a):
    response = cliente_owner.get(
        "/cl/es/reciclaje/api/catalitico-por-codigo/", {"codigo": "NO-EXISTE"}
    )

    assert response.status_code == 200
    assert response.json() == {"found": False, "suggestions": []}


@pytest.mark.django_db
def test_api_catalitico_por_codigo_sugiere_por_busqueda_parcial(
    cliente_owner, empresa_a, empresa_b
):
    CataliticoFactory(
        empresa=empresa_a,
        codigo="HONDA-CRV-01",
        nombre="Catalítico Honda",
        marca_vehiculo="Honda",
        modelo_vehiculo="CR-V",
        precio_compra=Decimal("12345"),
    )
    CataliticoFactory(empresa=empresa_b, codigo="HONDA-AJENO")

    response = cliente_owner.get(
        "/cl/es/reciclaje/api/catalitico-por-codigo/", {"codigo": "hond"}
    )
    data = response.json()

    assert data["found"] is False
    assert data["suggestions"] == [
        {
            "codigo": "HONDA-CRV-01",
            "nombre": "Catalítico Honda",
            "marca_vehiculo": "Honda",
            "modelo_vehiculo": "CR-V",
            "precio_compra": "12345.00",
            "cantidad_stock": 1,
        }
    ]


@pytest.mark.django_db
def test_api_catalitico_por_codigo_aislado_por_empresa(cliente_owner, empresa_a, empresa_b):
    CataliticoFactory(empresa=empresa_b, codigo="OTRA-EMPRESA")

    response = cliente_owner.get(
        "/cl/es/reciclaje/api/catalitico-por-codigo/", {"codigo": "OTRA-EMPRESA"}
    )

    assert response.json() == {"found": False, "suggestions": []}


@pytest.mark.django_db
def test_crear_compra_codigos_duplicados_en_envio_se_rechaza(cliente_owner, empresa_a):
    response = cliente_owner.post(
        "/cl/es/reciclaje/compras/nueva/",
        {
            "catalitico_codigo[]": ["DUP-1", "DUP-1"],
            "catalitico_nombre[]": ["A", "B"],
            "catalitico_marca[]": ["", ""],
            "catalitico_modelo[]": ["", ""],
            "catalitico_cantidad[]": ["1", "1"],
            "catalitico_precio[]": ["1000", "1000"],
        },
        follow=True,
    )
    assert response.status_code == 200
    assert not Catalitico.objects.filter(empresa=empresa_a, codigo="DUP-1").exists()
    assert not CompraReciclaje.objects.filter(empresa=empresa_a).exists()


@pytest.mark.django_db
def test_crear_compra_vacia_no_crea_nada(cliente_owner, empresa_a):
    cliente_owner.post("/cl/es/reciclaje/compras/nueva/", {})
    assert not CompraReciclaje.objects.filter(empresa=empresa_a).exists()


# ── Compra: chatarra ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_crear_compra_chatarra_incrementa_stock(cliente_owner, empresa_a):
    producto = ProductoChatarraFactory(empresa=empresa_a, cantidad_stock=Decimal("10.000"))

    cliente_owner.post(
        "/cl/es/reciclaje/compras/nueva/",
        {
            "chatarra_producto_id[]": [str(producto.pk)],
            "chatarra_cantidad[]": ["5.5"],
            "chatarra_precio[]": ["2000"],
        },
    )

    producto.refresh_from_db()
    assert producto.cantidad_stock == Decimal("15.500")


@pytest.mark.django_db
def test_crear_compra_chatarra_expone_precio_compra_para_autocompletar(
    cliente_owner, empresa_a
):
    producto = ProductoChatarraFactory(
        empresa=empresa_a,
        nombre="Cobre primera",
        precio_compra=Decimal("7200.00"),
    )

    response = cliente_owner.get("/cl/es/reciclaje/compras/nueva/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'name="chatarra_producto_id[]"' in content
    assert "rec-producto-busqueda" in content
    assert "Buscar por código o nombre" in content
    assert "/api/producto-chatarra/" in content
    assert 'class="rec-input rec-linea-precio rec-money-input"' in content
    assert 'class="rec-linea-precio-raw"' in content
    assert "setPrecioFila" in content
    assert "Cantidad (unid.)" in content
    assert "Cantidad (kg)" in content
    assert "Cantidad (lb)" not in content


@pytest.mark.django_db
def test_api_producto_chatarra_busca_por_codigo_y_nombre(cliente_owner, empresa_a):
    producto = ProductoChatarraFactory(
        empresa=empresa_a,
        codigo="COBRE-API",
        nombre="Cobre limpio",
        precio_compra=Decimal("7200.00"),
    )

    response = cliente_owner.get(
        "/cl/es/reciclaje/api/producto-chatarra/", {"q": "cobre"}
    )

    assert response.status_code == 200
    suggestion = response.json()["suggestions"][0]
    assert suggestion["id"] == producto.pk
    assert suggestion["codigo"] == "COBRE-API"
    assert suggestion["nombre"] == "Cobre limpio"


@pytest.mark.django_db
def test_crear_compra_chatarra_de_otra_empresa_se_rechaza(cliente_owner, empresa_a, empresa_b):
    producto_ajeno = ProductoChatarraFactory(empresa=empresa_b, cantidad_stock=Decimal("10.000"))

    cliente_owner.post(
        "/cl/es/reciclaje/compras/nueva/",
        {
            "chatarra_producto_id[]": [str(producto_ajeno.pk)],
            "chatarra_cantidad[]": ["5"],
            "chatarra_precio[]": ["2000"],
        },
    )

    producto_ajeno.refresh_from_db()
    assert producto_ajeno.cantidad_stock == Decimal("10.000")  # sin cambios
    assert not CompraReciclaje.objects.filter(empresa=empresa_a).exists()


# ── Venta: catalítico ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_crear_venta_catalitico_decrementa_stock(cliente_owner, empresa_a):
    catalitico = CataliticoFactory(empresa=empresa_a, cantidad_stock=5)

    response = cliente_owner.post(
        "/cl/es/reciclaje/ventas/nueva/",
        {
            "catalitico_id[]": [str(catalitico.pk)],
            "catalitico_cantidad[]": ["2"],
            "catalitico_precio[]": ["20000"],
        },
    )

    assert response.status_code == 302
    catalitico.refresh_from_db()
    assert catalitico.cantidad_stock == 3
    assert catalitico.estado == Catalitico.ESTADO_DISPONIBLE
    venta = VentaReciclaje.objects.get(empresa=empresa_a)
    assert venta.total() == Decimal("40000")


@pytest.mark.django_db
def test_crear_venta_catalitico_agota_stock_marca_vendido(cliente_owner, empresa_a):
    catalitico = CataliticoFactory(empresa=empresa_a, cantidad_stock=2)

    cliente_owner.post(
        "/cl/es/reciclaje/ventas/nueva/",
        {
            "catalitico_id[]": [str(catalitico.pk)],
            "catalitico_cantidad[]": ["2"],
            "catalitico_precio[]": ["20000"],
        },
    )

    catalitico.refresh_from_db()
    assert catalitico.cantidad_stock == 0
    assert catalitico.estado == Catalitico.ESTADO_VENDIDO


@pytest.mark.django_db
def test_crear_venta_catalitico_stock_insuficiente_no_crea_nada(cliente_owner, empresa_a):
    catalitico = CataliticoFactory(empresa=empresa_a, cantidad_stock=1)

    response = cliente_owner.post(
        "/cl/es/reciclaje/ventas/nueva/",
        {
            "catalitico_id[]": [str(catalitico.pk)],
            "catalitico_cantidad[]": ["5"],
            "catalitico_precio[]": ["20000"],
        },
        follow=True,
    )

    assert response.status_code == 200
    catalitico.refresh_from_db()
    assert catalitico.cantidad_stock == 1  # sin cambios
    assert not VentaReciclaje.objects.filter(empresa=empresa_a).exists()


@pytest.mark.django_db
def test_crear_venta_stock_insuficiente_en_una_linea_no_deja_lineas_parciales(
    cliente_owner, empresa_a
):
    """Atomicidad: si UNA línea de la venta falla (stock insuficiente), NINGUNA
    línea debe aplicarse — ni siquiera las válidas que iban antes en el POST."""
    catalitico_ok = CataliticoFactory(empresa=empresa_a, cantidad_stock=10)
    producto_sin_stock = ProductoChatarraFactory(empresa=empresa_a, cantidad_stock=Decimal("1.000"))

    cliente_owner.post(
        "/cl/es/reciclaje/ventas/nueva/",
        {
            "catalitico_id[]": [str(catalitico_ok.pk)],
            "catalitico_cantidad[]": ["1"],
            "catalitico_precio[]": ["20000"],
            "chatarra_producto_id[]": [str(producto_sin_stock.pk)],
            "chatarra_cantidad[]": ["999"],
            "chatarra_precio[]": ["100"],
        },
    )

    catalitico_ok.refresh_from_db()
    producto_sin_stock.refresh_from_db()
    assert catalitico_ok.cantidad_stock == 10  # no se tocó
    assert producto_sin_stock.cantidad_stock == Decimal("1.000")
    assert not VentaReciclaje.objects.filter(empresa=empresa_a).exists()


# ── Venta: chatarra ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_crear_venta_chatarra_decrementa_stock(cliente_owner, empresa_a):
    producto = ProductoChatarraFactory(empresa=empresa_a, cantidad_stock=Decimal("10.000"))

    cliente_owner.post(
        "/cl/es/reciclaje/ventas/nueva/",
        {
            "chatarra_producto_id[]": [str(producto.pk)],
            "chatarra_cantidad[]": ["4"],
            "chatarra_precio[]": ["3000"],
        },
    )

    producto.refresh_from_db()
    assert producto.cantidad_stock == Decimal("6.000")


# ── Aislamiento multi-tenant en lectura/edición ───────────────────────────────


@pytest.mark.django_db
def test_detalle_compra_404_para_compra_de_otra_empresa(cliente_owner, empresa_b):
    from taller.tests.factories import EmpresaFactory as _EF  # noqa: F401

    compra_ajena = CompraReciclaje.objects.create(empresa=empresa_b)
    response = cliente_owner.get(f"/cl/es/reciclaje/compras/{compra_ajena.pk}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_detalle_compra_renderiza_invoice_moderno(cliente_owner, empresa_a):
    categoria = CategoriaChatarra.objects.create(empresa=empresa_a, nombre="Metales")
    producto = ProductoChatarraFactory(
        empresa=empresa_a,
        categoria=categoria,
        nombre="Cobre limpio",
    )
    compra = CompraReciclaje.objects.create(empresa=empresa_a, notas="Pago contra recepción.")
    DetalleCompraChatarra.objects.create(
        compra=compra,
        producto=producto,
        cantidad=Decimal("2"),
        precio_unitario=Decimal("4500"),
    )

    response = cliente_owner.get(f"/cl/es/reciclaje/compras/{compra.pk}/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Comprobante de compra" in content
    assert "invoice-hero" in content
    assert "Material comprado" in content
    assert 'href="../"' in content
    assert "Volver a compras" in content
    assert "Código/SKU" in content
    assert "Cobre limpio" in content
    assert "2 kilos" in content
    assert "$9.000" in content
    assert "$9.000 CLP" not in content
    assert 'href="editar/"' in content
    assert 'href="eliminar/"' in content
    assert "window.print()" in content


@pytest.mark.django_db
def test_detalle_compra_oculta_notas_tecnicas_migradas(cliente_owner, empresa_a):
    compra = CompraReciclaje.objects.create(
        empresa=empresa_a,
        notas="[pythonanywhere:compra:40] Migrado desde PythonAnywhere. Cliente original: marco Olivares.",
    )

    response = cliente_owner.get(f"/cl/es/reciclaje/compras/{compra.pk}/")
    content = response.content.decode()

    assert response.status_code == 200
    assert "Notas operativas" not in content
    assert "PythonAnywhere" not in content
    assert "marco Olivares" not in content


@pytest.mark.django_db
def test_eliminar_compra_revierte_stock_chatarra(cliente_owner, empresa_a):
    producto = ProductoChatarraFactory(
        empresa=empresa_a,
        cantidad_stock=Decimal("25.000"),
    )
    compra = CompraReciclaje.objects.create(empresa=empresa_a)
    DetalleCompraChatarra.objects.create(
        compra=compra,
        producto=producto,
        cantidad=Decimal("5.000"),
        precio_unitario=Decimal("1000"),
    )

    response = cliente_owner.post(f"/cl/es/reciclaje/compras/{compra.pk}/eliminar/")

    assert response.status_code == 302
    producto.refresh_from_db()
    assert producto.cantidad_stock == Decimal("20.000")
    assert not CompraReciclaje.objects.filter(pk=compra.pk).exists()


@pytest.mark.django_db
def test_detalle_compra_no_usa_categoria_otros_como_descripcion(cliente_owner, empresa_a):
    categoria = CategoriaChatarra.objects.create(empresa=empresa_a, nombre="otros")
    producto = ProductoChatarraFactory(
        empresa=empresa_a,
        categoria=categoria,
        codigo="9000",
        nombre="9000",
    )
    compra = CompraReciclaje.objects.create(empresa=empresa_a)
    DetalleCompraChatarra.objects.create(
        compra=compra,
        producto=producto,
        cantidad=Decimal("25"),
        precio_unitario=Decimal("100000"),
    )

    response = cliente_owner.get(f"/cl/es/reciclaje/compras/{compra.pk}/")
    content = response.content.decode()

    assert "Material comprado" in content
    assert "9000" in content
    assert "Código/SKU" in content
    assert "9000" in content
    assert "Sin categoría definida" not in content


@pytest.mark.django_db
def test_detalle_venta_404_para_venta_de_otra_empresa(cliente_owner, empresa_b):
    venta_ajena = VentaReciclaje.objects.create(empresa=empresa_b)
    response = cliente_owner.get(f"/cl/es/reciclaje/ventas/{venta_ajena.pk}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_resumen_stock_no_muestra_catalogo_de_otra_empresa(cliente_owner, empresa_a, empresa_b):
    CataliticoFactory(empresa=empresa_a, codigo="MIO")
    CataliticoFactory(empresa=empresa_b, codigo="AJENO")

    response = cliente_owner.get("/cl/es/reciclaje/stock/")
    codigos = [c.codigo for c in response.context["catalogo_disponible"]]
    assert codigos == ["MIO"]


@pytest.mark.django_db
def test_editar_catalitico_404_para_catalitico_de_otra_empresa(cliente_owner, empresa_b):
    catalitico_ajeno = CataliticoFactory(empresa=empresa_b)
    response = cliente_owner.get(f"/cl/es/reciclaje/catalitico/{catalitico_ajeno.pk}/editar/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_editar_catalitico_permite_editar_compra_y_venta(
    cliente_owner, empresa_a
):
    catalitico = CataliticoFactory(
        empresa=empresa_a,
        codigo="CAT-PRECIOS",
        precio_compra=Decimal("10000"),
        precio_venta=Decimal("30000"),
    )

    response = cliente_owner.post(
        f"/cl/es/reciclaje/catalitico/{catalitico.pk}/editar/",
        {
            "nombre": catalitico.nombre,
            "marca_vehiculo": catalitico.marca_vehiculo,
            "modelo_vehiculo": catalitico.modelo_vehiculo,
            "precio_compra": "12000",
            "precio_venta": "35000",
            "activo": "on",
        },
    )

    assert response.status_code == 302

    catalitico.refresh_from_db()

    assert catalitico.precio_compra == Decimal("12000")
    assert catalitico.precio_venta == Decimal("35000")


@pytest.mark.django_db
def test_eliminar_catalitico_bloqueado_si_tiene_compra(cliente_owner, empresa_a):
    catalitico = CataliticoFactory(empresa=empresa_a)
    compra = CompraReciclaje.objects.create(empresa=empresa_a)
    from taller.models.reciclaje import DetalleCompraCatalitico

    DetalleCompraCatalitico.objects.create(
        compra=compra, catalitico=catalitico, cantidad=1, precio_unitario=Decimal("1000")
    )

    cliente_owner.post(f"/cl/es/reciclaje/catalitico/{catalitico.pk}/eliminar/")

    assert Catalitico.objects.filter(pk=catalitico.pk).exists()


@pytest.mark.django_db
def test_eliminar_catalitico_sin_movimientos_se_elimina(cliente_owner, empresa_a):
    catalitico = CataliticoFactory(empresa=empresa_a)
    cliente_owner.post(f"/cl/es/reciclaje/catalitico/{catalitico.pk}/eliminar/")
    assert not Catalitico.objects.filter(pk=catalitico.pk).exists()


# ── Reportes ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_reporte_fechas_calcula_totales_y_margen(cliente_owner, empresa_a):
    catalitico = CataliticoFactory(empresa=empresa_a, cantidad_stock=5)
    compra = CompraReciclaje.objects.create(empresa=empresa_a)
    from taller.models.reciclaje import DetalleCompraCatalitico, DetalleVentaCatalitico

    DetalleCompraCatalitico.objects.create(
        compra=compra, catalitico=catalitico, cantidad=5, precio_unitario=Decimal("1000")
    )
    venta = VentaReciclaje.objects.create(empresa=empresa_a)
    DetalleVentaCatalitico.objects.create(
        venta=venta, catalitico=catalitico, cantidad=2, precio_unitario=Decimal("3000")
    )

    response = cliente_owner.get("/cl/es/reciclaje/reportes/")
    assert response.status_code == 200
    assert response.context["total_compras"] == Decimal("5000")
    assert response.context["total_ventas"] == Decimal("6000")
    assert response.context["margen"] == Decimal("1000")


@pytest.mark.django_db
def test_reporte_fechas_pdf_devuelve_content_type_pdf(cliente_owner, empresa_a):
    response = cliente_owner.get("/cl/es/reciclaje/reportes/?formato=pdf")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
