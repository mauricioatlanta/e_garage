import json
from decimal import Decimal

import pytest

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_STOCK_BODEGA
from taller.models.repuesto import Repuesto
from taller.models.vehiculos import Vehiculo
from taller.services.inventory_service import InventoryService


# ---------- Fixtures simples ----------
@pytest.fixture
def user_cl(db):
    u = User.objects.create_user(username="mauri", password="pass")
    Empresa.objects.create(user=u, nombre_taller="EG Chile", pais="CL")  # moneda CLP por save()
    return u


@pytest.fixture
def user_us(db):
    u = User.objects.create_user(username="john", password="pass")
    Empresa.objects.create(user=u, nombre_taller="EG USA", pais="US")  # moneda USD por save()
    return u


@pytest.fixture
def cliente_y_vehiculos(user_cl):
    emp = user_cl.empresa
    c1 = Cliente.objects.create(empresa=emp, nombre="Acme Ltda.")
    c2 = Cliente.objects.create(empresa=emp, nombre="Otro Cliente")

    v1 = Vehiculo.objects.create(empresa=emp, cliente=c1, patente="AAA11", vin="VIN-111", anio=2020)
    v2 = Vehiculo.objects.create(empresa=emp, cliente=c1, patente="BBB22", vin="VIN-222", anio=2021)
    v3 = Vehiculo.objects.create(empresa=emp, cliente=c2, patente="CCC33", vin="VIN-333", anio=2022)
    return c1, c2, v1, v2, v3


# ---------- Tests del Form ----------
@pytest.mark.django_db
def test_form_filtra_vehiculos_por_cliente_en_post(client, user_cl, cliente_y_vehiculos):
    c1, c2, v1, v2, v3 = cliente_y_vehiculos
    client.login(username="mauri", password="pass")

    from taller.documentos.forms import DocumentoForm

    data = {
        "tipo": "OT",
        "numero": "",
        "fecha_emision": timezone.now().date(),
        "cliente": str(c1.id),  # ← cliente posteado
        "vehiculo": str(v1.id),  # ← pertenece a c1
        "observaciones": "",
        "pagado": "",
    }
    form = DocumentoForm(data=data, user=user_cl, empresa=user_cl.empresa, country="CL")
    assert form.is_valid(), form.errors  # debe ser válido

    # Ahora intenta usar vehículo de OTRO cliente
    data["vehiculo"] = str(v3.id)  # v3 pertenece a c2
    form2 = DocumentoForm(data=data, user=user_cl, empresa=user_cl.empresa, country="CL")
    assert not form2.is_valid()
    # Verificar que hay errores de validación
    assert form2.errors
    # El error puede estar en __all__ o en el campo específico
    if "__all__" in form2.errors:
        assert "El vehículo seleccionado no pertenece al cliente." in form2.errors["__all__"][0]
    else:
        # Si no está en __all__, debe estar en el campo vehiculo
        assert "vehiculo" in form2.errors


@pytest.mark.django_db
def test_form_restringe_cliente_y_vehiculo_a_empresa(client, user_cl, user_us):
    # Datos en CL
    emp_cl = user_cl.empresa
    c_cl = Cliente.objects.create(empresa=emp_cl, nombre="Cliente CL")
    v_cl = Vehiculo.objects.create(
        empresa=emp_cl, cliente=c_cl, patente="CLP11", vin="VIN-CLP", anio=2020
    )

    # Datos en US
    emp_us = user_us.empresa
    c_us = Cliente.objects.create(empresa=emp_us, nombre="Customer US")
    v_us = Vehiculo.objects.create(
        empresa=emp_us, cliente=c_us, patente="USA22", vin="VIN-USA", anio=2020
    )

    from taller.documentos.forms import DocumentoForm

    # Usuario CL no puede usar cliente/vehículo US
    data = {
        "tipo": "OT",
        "fecha_emision": timezone.now().date(),
        "cliente": str(c_us.id),
        "vehiculo": str(v_us.id),
        "observaciones": "",
    }
    form = DocumentoForm(data=data, user=user_cl, empresa=emp_cl, country="CL")
    assert not form.is_valid()
    # Verificar que hay errores de validación
    assert form.errors
    # El formulario debe rechazar los valores porque no están en el queryset filtrado por empresa
    assert "cliente" in form.errors
    assert "vehiculo" in form.errors

    # Usuario CL sí puede usar los suyos
    data["cliente"] = str(c_cl.id)
    data["vehiculo"] = str(v_cl.id)
    form2 = DocumentoForm(data=data, user=user_cl, empresa=emp_cl, country="CL")
    assert form2.is_valid(), form2.errors


@pytest.mark.django_db
def test_form_labels_por_pais(client, user_cl, user_us):
    from taller.documentos.forms import DocumentoForm

    # Test Chile
    form_cl = DocumentoForm(user=user_cl, empresa=user_cl.empresa, country="CL")
    assert form_cl.fields["cliente"].label == "Cliente"
    assert form_cl.fields["vehiculo"].label == "Vehículo"

    # Test USA
    form_us = DocumentoForm(user=user_us, empresa=user_us.empresa, country="US", language="en")
    assert form_us.fields["cliente"].label == "Customer"
    assert form_us.fields["vehiculo"].label == "Vehicle"


@pytest.mark.django_db
def test_form_urls_dal_por_pais(client, user_cl, user_us):
    from taller.documentos.forms import DocumentoForm

    # Test Chile
    form_cl = DocumentoForm(user=user_cl, empresa=user_cl.empresa, country="CL")
    assert "/cl/autocomplete/cliente/" in form_cl.fields["cliente"].widget.url
    assert "/cl/autocomplete/vehiculo/" in form_cl.fields["vehiculo"].widget.url

    # Test USA
    form_us = DocumentoForm(user=user_us, empresa=user_us.empresa, country="US")
    assert "/us/autocomplete/cliente/" in form_us.fields["cliente"].widget.url
    assert "/us/autocomplete/vehiculo/" in form_us.fields["vehiculo"].widget.url


@pytest.mark.django_db
def test_form_forward_dal_vehiculo(client, user_cl):
    from taller.documentos.forms import DocumentoForm

    form = DocumentoForm(user=user_cl, empresa=user_cl.empresa, country="CL")
    assert "cliente" in form.fields["vehiculo"].widget.forward


# ---------- Tests de Autocomplete (si tienes las URLs activas) ----------
@pytest.mark.django_db
def test_cliente_autocomplete_filtra_por_empresa(client, user_cl):
    client.login(username="mauri", password="pass")
    emp = user_cl.empresa
    # Un cliente propio y otro de otra empresa
    c_ok = Cliente.objects.create(empresa=emp, nombre="Mi Cliente")
    other_user = User.objects.create_user(username="x", password="pass")
    Empresa.objects.create(user=other_user, nombre_taller="Otra", pais="CL")
    Cliente.objects.create(empresa=other_user.empresa, nombre="Ajeno")

    url = reverse("cl_autocomplete:cliente")
    r = client.get(url, {"q": "Cliente"})
    assert r.status_code == 200
    payload = r.json()
    # DAL devuelve {results: [{id,text},...]}
    texts = [o["text"] for o in payload.get("results", [])]
    assert any("Mi Cliente" in t for t in texts)
    assert not any("Ajeno" in t for t in texts)


@pytest.mark.django_db
def test_vehiculo_autocomplete_filtra_por_cliente_forward(client, user_cl, cliente_y_vehiculos):
    client.login(username="mauri", password="pass")
    c1, c2, v1, v2, v3 = cliente_y_vehiculos

    url = reverse("cl_autocomplete:vehiculo")
    forwarded = json.dumps({"cliente": c1.id})
    r = client.get(url, {"q": "", "forward": forwarded})
    assert r.status_code == 200
    texts = [o["text"] for o in r.json().get("results", [])]
    # Debe listar v1 y v2 (cliente c1), NO v3 (cliente c2)
    assert any(v1.patente in t or v1.vin in t for t in texts)
    assert any(v2.patente in t or v2.vin in t for t in texts)
    assert not any(v3.patente in t or v3.vin in t for t in texts)


@pytest.mark.django_db
def test_autocomplete_usa_namespace(client, user_us):
    client.login(username="john", password="pass")
    emp = user_us.empresa
    Cliente.objects.create(empresa=emp, nombre="US Customer")

    url = reverse("usa_autocomplete:cliente")
    r = client.get(url, {"q": "Customer"})
    assert r.status_code == 200
    payload = r.json()
    texts = [o["text"] for o in payload.get("results", [])]
    assert any("US Customer" in t for t in texts)


@pytest.mark.django_db
def test_form_widget_ids_set_correctly(client, user_cl):
    from taller.documentos.forms import DocumentoForm

    form = DocumentoForm(user=user_cl, empresa=user_cl.empresa, country="CL")

    # Verificar que todos los campos tienen IDs únicos
    assert form.fields["tipo"].widget.attrs.get("id") == "id_tipo"
    assert form.fields["numero"].widget.attrs.get("id") == "id_numero"
    assert form.fields["fecha_emision"].widget.attrs.get("id") == "id_fecha_emision"
    assert form.fields["cliente"].widget.attrs.get("id") == "id_cliente"
    assert form.fields["vehiculo"].widget.attrs.get("id") == "id_vehiculo"
    assert form.fields["tecnico_responsable"].widget.attrs.get("id") == "id_tecnico_responsable"
    assert form.fields["kilometraje"].widget.attrs.get("id") == "id_kilometraje"
    assert form.fields["observaciones"].widget.attrs.get("id") == "id_observaciones"
    assert form.fields["pagado"].widget.attrs.get("id") == "id_pagado"


@pytest.mark.django_db
def test_form_rechaza_json_invalido(user_cl, cliente_y_vehiculos):
    c1, _, v1, _, _ = cliente_y_vehiculos

    from taller.documentos.forms import DocumentoForm

    data = {
        "tipo": "OT",
        "fecha_emision": timezone.now().date(),
        "cliente": str(c1.id),
        "vehiculo": str(v1.id),
        "repuestos_json": "{not-json",
        "servicios_json": "[]",
        "otros_json": "[]",
    }

    form = DocumentoForm(data=data, user=user_cl, empresa=user_cl.empresa, country="CL")

    assert not form.is_valid()
    assert "repuestos_json" in form.errors


@pytest.mark.django_db
def test_form_update_reemplaza_lineas_y_recalcula_totales(user_cl, cliente_y_vehiculos):
    c1, _, v1, _, _ = cliente_y_vehiculos
    empresa = user_cl.empresa

    documento = Documento.objects.create(
        empresa=empresa,
        cliente=c1,
        vehiculo=v1,
        tipo="OT",
        fecha_emision=timezone.now().date(),
    )
    LineaRepuesto.objects.create(
        documento=documento,
        nombre="Linea vieja",
        codigo="OLD-1",
        cantidad=1,
        precio_unitario=Decimal("100.00"),
        descuento=Decimal("0.00"),
        origen_repuesto="EXTERNO",
    )

    from taller.documentos.forms import DocumentoForm

    data = {
        "tipo": "OT",
        "fecha_emision": timezone.now().date(),
        "cliente": str(c1.id),
        "vehiculo": str(v1.id),
        "apply_vat": "on",
        "repuestos_json": json.dumps(
            [
                {
                    "codigo": "NEW-1",
                    "nombre": "Linea nueva",
                    "cantidad": 2,
                    "precio": "150",
                    "descuento": "10",
                }
            ]
        ),
        "servicios_json": "[]",
        "otros_json": "[]",
    }

    form = DocumentoForm(
        data=data,
        instance=documento,
        user=user_cl,
        empresa=empresa,
        country="CL",
    )

    assert form.is_valid(), form.errors
    saved = form.save()
    saved.refresh_from_db()

    assert saved.lineas_repuesto.count() == 1
    linea = saved.lineas_repuesto.get()
    assert linea.nombre == "Linea nueva"
    assert linea.codigo == "NEW-1"
    assert saved.lineas_repuesto.filter(codigo="OLD-1").count() == 0
    assert saved.neto_repuestos == Decimal("270.00")
    assert saved.tax_amount == Decimal("51.00")
    assert saved.total == Decimal("321.00")


@pytest.mark.django_db
def test_documento_form_descuenta_stock_en_creacion_emitida(user_cl):
    empresa = user_cl.empresa
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente Stock")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="STK55",
        vin="VIN-STOCK-55",
        anio=2022,
    )
    repuesto = Repuesto.objects.create(
        empresa=empresa,
        part_number="1040",
        nombre="Aceite de motor 10/40w",
        cantidad_stock=50,
        precio_venta=Decimal("12500.00"),
    )

    from taller.documentos.forms import DocumentoForm

    data = {
        "tipo": "OT",
        "fecha_emision": timezone.now().date(),
        "cliente": str(cliente.id),
        "vehiculo": str(vehiculo.id),
        "repuestos_json": json.dumps(
            [
                {
                    "repuesto_id": repuesto.id,
                    "codigo": "1040",
                    "nombre": "Aceite de motor 10/40w",
                    "cantidad": 5,
                    "precio": "12500",
                    "origen_repuesto": ORIGEN_STOCK_BODEGA,
                }
            ]
        ),
        "servicios_json": "[]",
        "otros_json": "[]",
    }

    form = DocumentoForm(data=data, user=user_cl, empresa=empresa, country="CL")

    assert form.is_valid(), form.errors
    form.save()
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 45


@pytest.mark.django_db
def test_documento_form_reajusta_stock_en_edicion_emitida(user_cl):
    empresa = user_cl.empresa
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente Edicion")
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        patente="EDT77",
        vin="VIN-EDIT-77",
        anio=2021,
    )
    repuesto = Repuesto.objects.create(
        empresa=empresa,
        part_number="1040",
        nombre="Aceite de motor 10/40w",
        cantidad_stock=50,
        precio_venta=Decimal("12500.00"),
    )
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tipo="OT",
        estado="EMITIDO",
        fecha_emision=timezone.now().date(),
    )
    LineaRepuesto.objects.create(
        documento=documento,
        repuesto=repuesto,
        codigo="1040",
        nombre="Aceite de motor 10/40w",
        cantidad=5,
        precio_unitario=Decimal("12500.00"),
        origen_repuesto=ORIGEN_STOCK_BODEGA,
    )
    InventoryService.procesar_movimiento_stock(documento, "descontar")
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 45

    from taller.documentos.forms import DocumentoForm

    data = {
        "tipo": "OT",
        "fecha_emision": timezone.now().date(),
        "cliente": str(cliente.id),
        "vehiculo": str(vehiculo.id),
        "repuestos_json": json.dumps(
            [
                {
                    "repuesto_id": repuesto.id,
                    "codigo": "1040",
                    "nombre": "Aceite de motor 10/40w",
                    "cantidad": 7,
                    "precio": "12500",
                    "origen_repuesto": ORIGEN_STOCK_BODEGA,
                }
            ]
        ),
        "servicios_json": "[]",
        "otros_json": "[]",
    }

    form = DocumentoForm(
        data=data,
        instance=documento,
        user=user_cl,
        empresa=empresa,
        country="CL",
    )

    assert form.is_valid(), form.errors
    form.save()
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == 43
