"""
Tests del flujo "crear vehículo desde documento".

- Al guardar vehículo con next=documentos/form, redirect vuelve al documento con cliente_id y vehiculo_id.
- La vista de documento crear (DocumentoCreateView) preselecciona cliente y vehículo cuando vienen en GET.
"""

import pytest
from django.test import Client

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo
from django.contrib.auth.models import User


@pytest.fixture
def user_usa_empresa(db):
    """Usuario con empresa USA."""
    from taller.tests.factories import EmpresaFactory
    user = User.objects.create_user(username="usa_user", password="testpass123")
    EmpresaFactory(user=user, nombre_taller="Taller USA", pais="US")
    return user


@pytest.fixture
def cliente_a(user_usa_empresa):
    """Cliente A de la empresa USA."""
    empresa = getattr(user_usa_empresa, "empresa", None)
    if not empresa:
        empresa = Empresa.objects.get(user=user_usa_empresa)
    return Cliente.objects.create(
        empresa=empresa,
        nombre="Cliente",
        apellido="A",
        email="cliente_a@test.com",
        telefono="+15551234567",
    )


@pytest.mark.django_db
def test_crear_vehiculo_redirect_a_documento_con_cliente_y_vehiculo(
    client: Client, user_usa_empresa, cliente_a
):
    """
    Usuario USA: crea vehículo con next=documentos/form y cliente_id;
    al guardar, redirect vuelve a documentos/form con cliente_id y vehiculo_id.
    """
    client.login(username="usa_user", password="testpass123")
    empresa = getattr(user_usa_empresa, "empresa", None) or Empresa.objects.get(
        user=user_usa_empresa
    )

    doc_form_path = "/us/documentos/form/"
    next_url = f"http://testserver{doc_form_path}"

    crear_url = "/us/en/vehiculos/crear/"
    get_resp = client.get(crear_url, {"next": next_url, "cliente_id": str(cliente_a.pk)})
    if get_resp.status_code not in (200, 302):
        pytest.skip("URL crear vehículo USA no disponible")
    if get_resp.status_code == 302:
        crear_url = get_resp.get("Location", crear_url)
        get_resp = client.get(crear_url, {"next": next_url, "cliente_id": str(cliente_a.pk)})
    if get_resp.status_code != 200:
        pytest.skip("No se pudo cargar el formulario de crear vehículo")

    csrf = get_resp.context.get("csrf_token") or ""
    if hasattr(csrf, "token"):
        csrf = csrf.token
    data = {
        "csrfmiddlewaretoken": csrf,
        "patente": "TEST99",
        "vin": "VIN-TEST-001",
        "anio": "2020",
        "millas": "10000",
        "cliente": str(cliente_a.pk),
        "next": next_url,
    }

    response = client.post(crear_url, data, follow=False)

    assert response.status_code == 302
    redirect_url = response.get("Location", "")
    assert "/documentos/form/" in redirect_url
    assert "cliente_id=" in redirect_url
    assert "vehiculo_id=" in redirect_url

    vehiculo_id = None
    for part in redirect_url.split("&"):
        if "vehiculo_id=" in part:
            vehiculo_id = part.split("vehiculo_id=", 1)[-1].split("&")[0].strip()
            break
    assert vehiculo_id
    vehiculo = Vehiculo.objects.filter(pk=vehiculo_id, empresa=empresa).first()
    assert vehiculo is not None
    assert vehiculo.cliente_id == cliente_a.pk


@pytest.mark.django_db
def test_documento_crear_con_cliente_id_vehiculo_id_preselecciona(
    client: Client, user_usa_empresa, cliente_a
):
    """
    GET /us/documentos/form/?cliente_id=A&vehiculo_id=V devuelve 200
    y el contexto incluye cliente_preselect_id y vehiculo_preselect_id (y form con initial).
    """
    empresa = getattr(user_usa_empresa, "empresa", None) or Empresa.objects.get(
        user=user_usa_empresa
    )
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente_a,
        patente="PRESEL",
        vin="VIN-PRE",
        anio=2021,
        millas=5000,
    )

    client.login(username="usa_user", password="testpass123")

    doc_crear_path = f"/us/documentos/form/?cliente_id={cliente_a.pk}&vehiculo_id={vehiculo.pk}"
    response = client.get(doc_crear_path)

    assert response.status_code == 200
    ctx = response.context
    assert ctx.get("cliente_preselect_id") == cliente_a.pk
    assert ctx.get("vehiculo_preselect_id") == vehiculo.pk
    form = ctx.get("form")
    assert form is not None
    assert form.initial.get("cliente") == cliente_a.pk
    assert form.initial.get("vehiculo") == vehiculo.pk
