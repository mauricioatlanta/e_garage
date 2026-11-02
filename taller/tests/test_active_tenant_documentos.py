import json

import pytest
from django.http import Http404
from django.test import RequestFactory

from taller.documentos import views as documentos_views
from taller.documentos.views_migrated import (
    DocumentoCreateView,
    DocumentoDetailView,
    DocumentoListView,
)
from taller.documentos.views_pdf import _get_documento_for_request
from taller.tests.factories import (
    ClienteFactory,
    DocumentoFactory,
    EmpresaFactory,
    RepuestoFactory,
    VehiculoFactory,
)


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
    empresa_a = EmpresaFactory(pais="CL")
    empresa_b = EmpresaFactory(pais="US")
    return empresa_a, empresa_b


@pytest.mark.django_db
def test_documentos_listado_usa_tenant_activo_y_aisla_propietaria(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    doc_a = DocumentoFactory(empresa=empresa_a, tipo="PRES", estado="EMITIDO")
    doc_b = DocumentoFactory(empresa=empresa_b, tipo="PRES", estado="EMITIDO")
    request = _active_request("/us/documentos/", empresa_a, empresa_b)

    view = DocumentoListView()
    view.setup(request)
    view.kwargs = {}

    ids = {documento.pk for documento in view.get_queryset()}

    assert doc_b.pk in ids
    assert doc_a.pk not in ids
    assert request.user.empresa == empresa_a
    assert request.empresa == empresa_b


@pytest.mark.django_db
def test_documento_creacion_inyecta_tenant_activo_en_form(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    request = _active_request("/us/documentos/form/", empresa_a, empresa_b)

    view = DocumentoCreateView()
    view.setup(request)
    view.kwargs = {}

    kwargs = view.get_form_kwargs()

    assert kwargs["empresa"] == empresa_b
    assert kwargs["user"] == empresa_a.user
    assert request.user.empresa == empresa_a


@pytest.mark.django_db
def test_documento_detalle_permite_b_y_bloquea_a(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    doc_a = DocumentoFactory(empresa=empresa_a)
    doc_b = DocumentoFactory(empresa=empresa_b)
    request = _active_request(f"/us/documentos/ver/{doc_b.pk}/", empresa_a, empresa_b)

    view = DocumentoDetailView()
    view.setup(request, pk=doc_b.pk)
    view.kwargs = {"pk": doc_b.pk}
    assert view.get_object() == doc_b

    view.kwargs = {"pk": doc_a.pk}
    with pytest.raises(Http404):
        view.get_object()


@pytest.mark.django_db
def test_pdf_documento_respeta_tenant_activo_incluso_con_superuser(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    user = empresa_a.user
    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    doc_a = DocumentoFactory(empresa=empresa_a)
    doc_b = DocumentoFactory(empresa=empresa_b)
    request = _active_request(f"/us/documentos/{doc_b.pk}/pdf/", empresa_a, empresa_b)

    assert _get_documento_for_request(request, doc_b.pk) == doc_b
    with pytest.raises(Http404):
        _get_documento_for_request(request, doc_a.pk)


@pytest.mark.django_db
def test_autocompletes_documentos_filtran_por_tenant_activo(empresas_ab):
    empresa_a, empresa_b = empresas_ab
    cliente_a = ClienteFactory(empresa=empresa_a, nombre="Mismo")
    cliente_b = ClienteFactory(empresa=empresa_b, nombre="Mismo")
    vehiculo_a = VehiculoFactory(empresa=empresa_a, cliente=cliente_a, patente="AAA111")
    vehiculo_b = VehiculoFactory(empresa=empresa_b, cliente=cliente_b, patente="BBB222")
    repuesto_a = RepuestoFactory(empresa=empresa_a, nombre="Filtro Aceite")
    repuesto_b = RepuestoFactory(empresa=empresa_b, nombre="Filtro Aceite")

    request = _active_request("/us/documentos/autocomplete/cliente/", empresa_a, empresa_b)
    response = documentos_views.autocomplete_cliente(request)
    cliente_ids = {item["id"] for item in json.loads(response.content)["results"]}
    assert cliente_b.pk in cliente_ids
    assert cliente_a.pk not in cliente_ids

    request = _active_request(
        "/us/documentos/api/vehiculos-por-cliente/",
        empresa_a,
        empresa_b,
        data={"cliente_id": cliente_b.pk},
    )
    response = documentos_views.obtener_vehiculos_por_cliente(request)
    vehiculo_ids = {item["id"] for item in json.loads(response.content)}
    assert vehiculo_b.pk in vehiculo_ids
    assert vehiculo_a.pk not in vehiculo_ids

    request = _active_request(
        "/us/documentos/api/autocomplete-repuesto/",
        empresa_a,
        empresa_b,
        data={"q": "Filtro"},
    )
    response = documentos_views.autocomplete_repuesto(request)
    repuesto_ids = {item["id"] for item in json.loads(response.content)["results"]}
    assert repuesto_b.pk in repuesto_ids
    assert repuesto_a.pk not in repuesto_ids
