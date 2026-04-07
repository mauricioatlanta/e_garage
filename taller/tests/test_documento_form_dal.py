import json

import pytest

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo


# ---------- Fixtures simples ----------
@pytest.fixture
@pytest.mark.django_db
def user_cl(db):
    u = User.objects.create_user(username="mauri", password="pass")
    Empresa.objects.create(user=u, nombre_taller="EG Chile", pais="CL")  # moneda CLP por save()
    return u


@pytest.fixture
@pytest.mark.django_db
def user_us(db):
    u = User.objects.create_user(username="john", password="pass")
    Empresa.objects.create(user=u, nombre_taller="EG USA", pais="US")  # moneda USD por save()
    return u


@pytest.fixture
@pytest.mark.django_db
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
        "estado_pago": "PENDIENTE",
        "observaciones": "",
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
        "estado_pago": "PENDIENTE",
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
    form_us = DocumentoForm(user=user_us, empresa=user_us.empresa, country="US")
    assert form_us.fields["cliente"].label == "Cliente"
    assert form_us.fields["vehiculo"].label == "Veh\u00edculo"


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

    url = "/cl/es/autocomplete/cliente/"
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

    url = "/cl/es/autocomplete/vehiculo/"
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
    emp = user_us.empresa
    Cliente.objects.create(empresa=emp, nombre="US Customer")

    from django.test import RequestFactory
    from taller.views_autocomplete import ClienteAutocomplete

    request = RequestFactory().get("/us/autocomplete/cliente/", {"q": "Customer"})
    request.user = user_us
    request.session = {}
    r = ClienteAutocomplete.as_view()(request)
    assert r.status_code == 200
    payload = json.loads(r.content.decode("utf-8"))
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
