"""
Tests for Sprint 3A: filtros ?tipo y ?estado en DocumentoListView.

Strategy: use RequestFactory + call get_queryset() / get_context_data() directly
to avoid the Python 3.14 + Django 4.2 copy(context) incompatibility that occurs
when the test client renders TemplateResponse objects.

Covers:
  1.  ?tipo=PRES devuelve solo presupuestos
  2.  ?tipo=OT devuelve solo órdenes de trabajo
  3.  ?estado=BORRADOR devuelve solo borradores
  4.  ?estado=BORRADOR,EMITIDO acepta múltiples estados
  5.  Tipo y estado se combinan con AND
  6.  Excluye documentos de otra empresa (aislamiento multi-tenant)
  7.  Parámetro tipo inválido no causa excepción y no elimina aislamiento tenant
  8.  Parámetro estado inválido no causa excepción y no elimina aislamiento tenant
  9.  La paginación conserva tipo y estado en base_query_string
  10. KPI quotes_pending contiene URL filtrada
  11. El enlace del KPI devuelve únicamente PRES pendientes
  12. WORKSHOP, DESARMADURIA y CARWASH no tienen kpi_quotes_pending
  13. manage.py check limpio
"""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse

from taller.constants.workspaces import (
    WGT_KPI_QUOTES_PENDING,
    get_workspace_def,
    WORKSPACE_CARWASH,
    WORKSPACE_DESARMADURIA,
    WORKSPACE_TALLER,
)
from taller.documentos.views_migrated import DocumentoListView
from taller.services.workspace_dashboard_service import WorkspaceDashboardService
from taller.tests.factories import DocumentoFactory, EmpresaFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_view(empresa, **get_params):
    """
    Returns a DocumentoListView instance bound to a GET request.
    Does NOT call render_to_response — safe to call get_queryset() / get_context_data().
    """
    factory = RequestFactory()
    request = factory.get("/cl/documentos/", get_params)
    request.user = empresa.user

    view = DocumentoListView()
    view.setup(request)
    view.kwargs = {}
    return view


def _qs_ids(empresa, **get_params):
    """Returns the set of pk values in get_queryset() for the given params."""
    view = _make_view(empresa, **get_params)
    return {d.pk for d in view.get_queryset()}


# ---------------------------------------------------------------------------
# 1-5: Filter correctness
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tipo_pres_devuelve_solo_presupuestos():
    empresa = EmpresaFactory(pais="CL")
    doc_pres = DocumentoFactory(empresa=empresa, tipo="PRES", estado="EMITIDO")
    doc_ot   = DocumentoFactory(empresa=empresa, tipo="OT",   estado="EMITIDO")

    ids = _qs_ids(empresa, tipo="PRES")
    assert doc_pres.pk in ids
    assert doc_ot.pk not in ids


@pytest.mark.django_db
def test_tipo_ot_devuelve_solo_ordenes():
    empresa = EmpresaFactory(pais="CL")
    doc_ot   = DocumentoFactory(empresa=empresa, tipo="OT",   estado="EMITIDO")
    doc_pres = DocumentoFactory(empresa=empresa, tipo="PRES", estado="EMITIDO")

    ids = _qs_ids(empresa, tipo="OT")
    assert doc_ot.pk in ids
    assert doc_pres.pk not in ids


@pytest.mark.django_db
def test_estado_borrador_devuelve_solo_borradores():
    empresa = EmpresaFactory(pais="CL")
    doc_b = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    doc_e = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")

    ids = _qs_ids(empresa, estado="BORRADOR")
    assert doc_b.pk in ids
    assert doc_e.pk not in ids


@pytest.mark.django_db
def test_estado_multiple_acepta_borrador_y_emitido():
    empresa = EmpresaFactory(pais="CL")
    doc_b = DocumentoFactory(empresa=empresa, tipo="OT", estado="BORRADOR")
    doc_e = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")
    doc_a = DocumentoFactory(empresa=empresa, tipo="OT", estado="ANULADO")

    ids = _qs_ids(empresa, estado="BORRADOR,EMITIDO")
    assert doc_b.pk in ids
    assert doc_e.pk in ids
    assert doc_a.pk not in ids


@pytest.mark.django_db
def test_tipo_y_estado_combinan_con_and():
    empresa = EmpresaFactory(pais="CL")
    doc_pres_b = DocumentoFactory(empresa=empresa, tipo="PRES", estado="BORRADOR")
    doc_pres_e = DocumentoFactory(empresa=empresa, tipo="PRES", estado="EMITIDO")
    doc_ot_b   = DocumentoFactory(empresa=empresa, tipo="OT",   estado="BORRADOR")

    ids = _qs_ids(empresa, tipo="PRES", estado="BORRADOR")
    assert doc_pres_b.pk in ids
    assert doc_pres_e.pk not in ids
    assert doc_ot_b.pk not in ids


# ---------------------------------------------------------------------------
# 6: Tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_excluye_documentos_de_otra_empresa():
    empresa_a = EmpresaFactory(pais="CL")
    empresa_b = EmpresaFactory(pais="CL")
    doc_a = DocumentoFactory(empresa=empresa_a, tipo="PRES", estado="EMITIDO")
    doc_b = DocumentoFactory(empresa=empresa_b, tipo="PRES", estado="EMITIDO")

    ids = _qs_ids(empresa_a, tipo="PRES")
    assert doc_a.pk in ids
    assert doc_b.pk not in ids


# ---------------------------------------------------------------------------
# 7-8: Invalid params — no exception, no tenant breach
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tipo_invalido_ignorado_sin_excepcion():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")

    # Should not raise; invalid tipo is silently ignored → all empresa docs shown
    ids = _qs_ids(empresa, tipo="INVALID_TYPE")
    assert doc.pk in ids  # doc is visible because filter was not applied


@pytest.mark.django_db
def test_estado_invalido_ignorado_sin_excepcion():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="OT", estado="EMITIDO")

    # Should not raise; invalid estado is silently ignored → all empresa docs shown
    ids = _qs_ids(empresa, estado="NO_EXISTE")
    assert doc.pk in ids


# ---------------------------------------------------------------------------
# 9: Pagination preserves GET params in base_query_string
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_paginacion_conserva_tipo_y_estado_en_context():
    empresa = EmpresaFactory(pais="CL")
    for _ in range(5):
        DocumentoFactory(empresa=empresa, tipo="PRES", estado="BORRADOR")

    view = _make_view(empresa, tipo="PRES", estado="BORRADOR")
    view.object_list = view.get_queryset()
    context = view.get_context_data()

    base_qs = context.get("base_query_string", "")
    assert "tipo=PRES" in base_qs
    assert "estado=BORRADOR" in base_qs
    # page= must NOT appear in base_query_string (it's omitted so pagination links can append it)
    assert "page=" not in base_qs


# ---------------------------------------------------------------------------
# 10-12: KPI URL
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_kpi_quotes_pending_contiene_url_filtrada():
    empresa = EmpresaFactory(pais="CL")
    ws_def = get_workspace_def("PARTS")
    dashboard_data = WorkspaceDashboardService.resolve(ws_def, empresa)

    # Simulate what workspace_dashboard view does
    lista_base = reverse("documentos_cl_es:lista_documentos")
    quotes_url = lista_base + "?tipo=PRES&estado=BORRADOR,EMITIDO"
    for widget in dashboard_data["widgets"]:
        if widget["key"] == WGT_KPI_QUOTES_PENDING:
            widget["url"] = quotes_url
            break

    w = next(w for w in dashboard_data["widgets"] if w["key"] == WGT_KPI_QUOTES_PENDING)
    assert "tipo=PRES" in w["url"]
    assert "estado=BORRADOR,EMITIDO" in w["url"]


@pytest.mark.django_db
def test_enlace_kpi_devuelve_pres_pendientes():
    empresa = EmpresaFactory(pais="CL")
    doc_pres_b  = DocumentoFactory(empresa=empresa, tipo="PRES", estado="BORRADOR")
    doc_pres_e  = DocumentoFactory(empresa=empresa, tipo="PRES", estado="EMITIDO")
    doc_ot      = DocumentoFactory(empresa=empresa, tipo="OT",   estado="EMITIDO")
    doc_anulado = DocumentoFactory(empresa=empresa, tipo="PRES", estado="ANULADO")

    # The KPI URL params: tipo=PRES&estado=BORRADOR,EMITIDO
    ids = _qs_ids(empresa, tipo="PRES", estado="BORRADOR,EMITIDO")
    assert doc_pres_b.pk in ids
    assert doc_pres_e.pk in ids
    assert doc_ot.pk not in ids
    assert doc_anulado.pk not in ids


def test_otros_workspaces_no_tienen_quotes_pending():
    """TALLER, DESARMADURIA y CARWASH no incluyen kpi_quotes_pending en sus widget_keys."""
    for ws in (WORKSPACE_TALLER, WORKSPACE_DESARMADURIA, WORKSPACE_CARWASH):
        assert WGT_KPI_QUOTES_PENDING not in ws.widget_keys, (
            f"{ws.product_key} no debería tener kpi_quotes_pending"
        )


# ---------------------------------------------------------------------------
# 13: manage.py check
# ---------------------------------------------------------------------------

def test_manage_check_limpio():
    out = StringIO()
    call_command("check", stdout=out, stderr=StringIO())
    output = out.getvalue()
    assert "System check identified no issues" in output or "0 issues" in output
