import json
from decimal import Decimal

import pytest

from django.contrib.auth.models import User
from django.urls import reverse

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.repuesto import Repuesto
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import CategoriaServicio, Servicio, SubcategoriaServicio


@pytest.fixture
def user_cl(db):
    user = User.objects.create_user(username="doc-endpoints", password="pass")
    Empresa.objects.create(user=user, nombre_taller="EG Chile", pais="CL")
    return user


@pytest.fixture
def auth_client(client, user_cl):
    client.force_login(user_cl)
    return client


@pytest.mark.django_db
def test_api_vehiculos_por_cliente_devuelve_etiqueta_formateada(auth_client, user_cl):
    empresa = user_cl.empresa
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente Documento")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="ABCD12",
        vin="VIN-ABCD12",
        anio=2024,
        marca_texto="Toyota",
        modelo_texto="Yaris",
    )

    response = auth_client.get(
        "/cl/documentos/api/vehiculos-por-cliente/",
        {"cliente_id": cliente.id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == vehiculo.id
    assert payload[0]["text"] == "2024 - Toyota - Yaris - ABCD12"
    assert payload[0]["label"] == "2024 - Toyota - Yaris - ABCD12"
    assert payload[0]["marca"] == "Toyota"
    assert payload[0]["modelo"] == "Yaris"


@pytest.mark.django_db
def test_vehiculo_autocomplete_usa_formato_ano_marca_modelo_patente(auth_client, user_cl):
    empresa = user_cl.empresa
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente DAL")
    Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="ZXCV98",
        vin="VIN-ZXCV98",
        anio=2021,
        marca_texto="Mazda",
        modelo_texto="CX-5",
    )

    response = auth_client.get(
        "/cl/autocomplete/vehiculo/",
        {
            "q": "Mazda",
            "forward": json.dumps({"cliente": cliente.id}),
        },
    )

    assert response.status_code == 200
    texts = [item["text"] for item in response.json().get("results", [])]
    assert "2021 - Mazda - CX-5 - ZXCV98" in texts


@pytest.mark.django_db
def test_servicios_menu_shell_no_prerenderiza_catalogo(auth_client, user_cl):
    empresa = user_cl.empresa
    categoria = CategoriaServicio.objects.create(country="CL", code="MANT", activo=True)
    subcategoria = SubcategoriaServicio.objects.create(
        categoria=categoria,
        country="CL",
        code="ACEITE",
        activo=True,
    )
    servicio = Servicio.objects.create(
        empresa=empresa,
        nombre="Cambio de aceite premium",
        categoria=categoria,
        subcategoria=subcategoria,
        precio_base=Decimal("24990.00"),
        activo=True,
    )

    response = auth_client.get(reverse("chile:taller:servicios:servicios_menu"))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="servicios-menu-config"' in content
    assert 'id="servicesGrid"' in content
    assert servicio.nombre not in content


@pytest.mark.django_db
def test_servicios_menu_data_api_devuelve_scope_de_empresa_y_urls(auth_client, user_cl):
    empresa = user_cl.empresa
    categoria = CategoriaServicio.objects.create(country="CL", code="MANT", activo=True)
    subcategoria = SubcategoriaServicio.objects.create(
        categoria=categoria,
        country="CL",
        code="ACEITE",
        activo=True,
    )
    servicio_empresa = Servicio.objects.create(
        empresa=empresa,
        nombre="Cambio de aceite premium",
        categoria=categoria,
        subcategoria=subcategoria,
        precio_base=Decimal("24990.00"),
        activo=True,
    )

    other_user = User.objects.create_user(username="doc-endpoints-other", password="pass")
    other_empresa = Empresa.objects.create(
        user=other_user,
        nombre_taller="EG Otra Empresa",
        pais="CL",
    )
    Servicio.objects.create(
        empresa=other_empresa,
        nombre="Cambio de aceite externo",
        categoria=categoria,
        subcategoria=subcategoria,
        precio_base=Decimal("19990.00"),
        activo=True,
    )

    response = auth_client.get(
        reverse("chile:taller:servicios:servicios_menu_data_api"),
        {"q": "aceite"},
    )

    assert response.status_code == 200
    payload = response.json()
    service_ids = [item["id"] for item in payload["servicios"]]
    assert service_ids == [servicio_empresa.id]

    found = payload["servicios"][0]
    assert found["nombre"] == "Cambio de aceite premium"
    assert found["view_url"].endswith(f"/cl/servicios/{servicio_empresa.id}/")
    assert found["edit_url"].endswith(f"/cl/servicios/{servicio_empresa.id}/editar/")
    assert found["delete_url"].endswith(f"/cl/servicios/{servicio_empresa.id}/eliminar/")


@pytest.mark.django_db
def test_buscar_servicios_api_busca_por_nombre_y_devuelve_precio(auth_client, user_cl):
    empresa = user_cl.empresa
    categoria = CategoriaServicio.objects.create(country="CL", code="MANT", activo=True)
    subcategoria = SubcategoriaServicio.objects.create(
        categoria=categoria,
        country="CL",
        code="ACEITE",
        activo=True,
    )
    servicio = Servicio.objects.create(
        empresa=empresa,
        nombre="Cambio de aceite premium",
        categoria=categoria,
        subcategoria=subcategoria,
        precio_base=Decimal("24990.00"),
        activo=True,
    )

    response = auth_client.get(
        reverse("chile:taller:servicios:buscar_servicios_api"),
        {"q": "aceite"},
    )

    assert response.status_code == 200
    payload = response.json()
    service_ids = [item["id"] for item in payload["servicios"]]
    assert servicio.id in service_ids

    found = next(item for item in payload["servicios"] if item["id"] == servicio.id)
    assert found["nombre"] == "Cambio de aceite premium"
    assert found["precio"] == "24990.00"
    assert found["precio_base"] == "24990.00"


@pytest.mark.django_db
def test_buscar_repuestos_api_busca_por_proveedor(auth_client, user_cl):
    empresa = user_cl.empresa
    repuesto = Repuesto.objects.create(
        empresa=empresa,
        part_number="FLT-9",
        nombre="Filtro premium",
        proveedor="Proveedor Norte",
        precio_venta=Decimal("15990.00"),
        cantidad_stock=3,
    )

    response = auth_client.get("/cl/documentos/api/repuestos/buscar/", {"q": "norte"})

    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == repuesto.id for item in payload)

    found = next(item for item in payload if item["id"] == repuesto.id)
    assert found["nombre"] == "Filtro premium"
    assert found["codigo"] == "FLT-9"
    assert found["proveedor"] == "Proveedor Norte"


@pytest.mark.django_db
def test_api_repuestos_general_incluye_stock_y_minimo(auth_client, user_cl):
    empresa = user_cl.empresa
    repuesto = Repuesto.objects.create(
        empresa=empresa,
        part_number="AMR-77",
        nombre="Amortiguador delantero",
        proveedor="Proveedor Sur",
        precio_venta=Decimal("42990.00"),
        cantidad_stock=8,
        stock_minimo=3,
    )

    response = auth_client.get("/cl/api/repuestos/", {"q": "sur"})

    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == repuesto.id for item in payload["results"])

    found = next(item for item in payload["results"] if item["id"] == repuesto.id)
    assert found["proveedor"] == "Proveedor Sur"
    assert found["stock"] == 8
    assert found["stock_minimo"] == 3
