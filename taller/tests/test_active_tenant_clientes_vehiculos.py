import json
from types import SimpleNamespace

import pytest
from django.http import Http404
from django.test import RequestFactory

from taller.clientes.dal_views import ClientesAutocomplete
from taller.clientes.views_cbv import ClienteCreateView, ClienteDetailView, ClienteListView
from taller.tests.factories import ClienteFactory, EmpresaFactory, VehiculoFactory
from taller.vehiculos import views_fbv as vehiculos_views


def _active_request(path, empresa_a, empresa_b, method="get", data=None):
    factory = RequestFactory()
    request_method = getattr(factory, method)
    request = request_method(path, data=data or {})
    request.user = empresa_a.user
    request.empresa = empresa_b
    request.company = empresa_b
    request.country = empresa_b.pais
    request.company_country = empresa_b.pais
    return request


@pytest.fixture
def empresas_ab(db):
    return EmpresaFactory(pais="CL"), EmpresaFactory(pais="US")


@pytest.mark.django_db
def test_clientes_listado_usa_tenant_activo_y_aisla_propietaria(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a, nombre="Cliente A")
    cliente_b = ClienteFactory(empresa=empresa_b, nombre="Cliente B")
    request = _active_request("/us/clientes/", empresa_a, empresa_b)

    view = ClienteListView()
    view.setup(request)
    view.kwargs = {}
    ids = {cliente.pk for cliente in view.get_queryset()}

    assert cliente_b.pk in ids
    assert cliente_a.pk not in ids
    assert request.user.empresa == empresa_a


@pytest.mark.django_db
def test_cliente_creacion_y_detalle_usan_tenant_activo(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a)
    cliente_b = ClienteFactory(empresa=empresa_b)
    request = _active_request("/us/clientes/crear/", empresa_a, empresa_b)

    create_view = ClienteCreateView()
    create_view.setup(request)
    create_view.kwargs = {}
    kwargs = create_view.get_form_kwargs()
    assert kwargs["empresa"] == empresa_b

    detail_view = ClienteDetailView()
    detail_view.setup(request, pk=cliente_b.pk)
    detail_view.kwargs = {"pk": cliente_b.pk}
    assert detail_view.get_object() == cliente_b

    detail_view.kwargs = {"pk": cliente_a.pk}
    with pytest.raises(Http404):
        detail_view.get_object()


@pytest.mark.django_db
def test_cliente_autocomplete_dal_filtra_por_tenant_activo(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a, nombre="Mismo")
    cliente_b = ClienteFactory(empresa=empresa_b, nombre="Mismo")
    request = _active_request("/us/clientes/autocomplete/", empresa_a, empresa_b)

    view = ClientesAutocomplete()
    view.request = request
    view.q = "Mismo"
    ids = {cliente.pk for cliente in view.get_queryset()}

    assert cliente_b.pk in ids
    assert cliente_a.pk not in ids


@pytest.mark.django_db
def test_vehiculos_listado_y_busqueda_clientes_usan_tenant_activo(empresas_ab, monkeypatch):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a, nombre="Cliente")
    cliente_b = ClienteFactory(empresa=empresa_b, nombre="Cliente")
    vehiculo_a = VehiculoFactory(empresa=empresa_a, cliente=cliente_a, patente="AAA111")
    vehiculo_b = VehiculoFactory(empresa=empresa_b, cliente=cliente_b, patente="BBB222")
    captured = {}

    def fake_render(request, template_name, context):
        captured["context"] = context
        return SimpleNamespace(status_code=200, context_data=context)

    monkeypatch.setattr(vehiculos_views, "render", fake_render)
    request = _active_request("/us/vehiculos/", empresa_a, empresa_b)
    response = vehiculos_views.lista_vehiculos(request)

    assert response.status_code == 200
    ids = {vehiculo.pk for vehiculo in captured["context"]["vehiculos"]}
    assert vehiculo_b.pk in ids
    assert vehiculo_a.pk not in ids

    request = _active_request(
        "/us/vehiculos/api/clientes/",
        empresa_a,
        empresa_b,
        data={"q": "Cliente"},
    )
    response = vehiculos_views.api_busqueda_clientes(request)
    cliente_ids = {item["id"] for item in json.loads(response.content)}
    assert cliente_b.pk in cliente_ids
    assert cliente_a.pk not in cliente_ids


@pytest.mark.django_db
def test_vehiculo_detalle_bloquea_objetos_de_empresa_propietaria(empresas_ab, monkeypatch):
    empresa_a, empresa_b = empresas_ab
    vehiculo_a = VehiculoFactory(empresa=empresa_a)
    vehiculo_b = VehiculoFactory(empresa=empresa_b)

    def fake_template_response(request, template_name, context):
        return SimpleNamespace(status_code=200, context_data=context)

    monkeypatch.setattr(vehiculos_views, "TemplateResponse", fake_template_response)
    request = _active_request(f"/us/vehiculos/{vehiculo_b.pk}/", empresa_a, empresa_b)
    response = vehiculos_views.ver_vehiculo(request, vehiculo_b.pk)
    assert response.context_data["vehiculo"] == vehiculo_b

    with pytest.raises(Http404):
        vehiculos_views.ver_vehiculo(request, vehiculo_a.pk)
