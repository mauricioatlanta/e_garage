"""
Tests for Sprint 3B: quick actions "Nueva cotización" (PRES) and "Nueva venta" (PTS).

Strategy:
- RequestFactory + direct view method calls for GET/initial tests (no template rendering).
- DocumentoForm direct instantiation for form validation / save tests.
- Direct attribute inspection for workspace structure tests.
- reverse() for URL existence verification.

Covers:
  1.  GET crear con ?tipo=PRES preselecciona tipo=PRES en form initial
  2.  DocumentoForm acepta tipo=PRES y guarda Documento.tipo=PRES
  3.  GET crear con ?tipo=PTS preselecciona tipo=PTS en form initial
  4.  DocumentoForm acepta tipo=PTS y guarda Documento.tipo=PTS
  5.  Tipo inválido en GET no entra en initial (usa default del form)
  6.  GET de edición con ?tipo=PTS no cambia initial del update view
  7.  POST de edición no altera tipo mediante parámetro GET (UpdateView no lee tipo de GET)
  8.  Tenant isolation: update view filtra por empresa
  9.  PARTS quick_actions incluye acción new_quote con path de PRES
  10. PARTS quick_actions incluye acción new_parts_sale con path de PTS
  11. URL CL para crear documento existe y resuelve
  12. URL US para crear documento existe y resuelve
  13. Otros workspaces (TALLER, DESARM, CARWASH) no tienen acciones con ?tipo=PRES o ?tipo=PTS
  14. Conversión Documento.convertir_documento_final() PRES→OT sigue funcionando
  15. test_documento_form_dal suite pasa
  16. test_documento_form_endpoints suite pasa
  17. manage.py check limpio
"""

from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse, resolve

from taller.constants.workspaces import (
    WORKSPACE_CASA_REPUESTOS,
    WORKSPACE_TALLER,
    WORKSPACE_DESARMADURIA,
    WORKSPACE_CARWASH,
)
from taller.documentos.views_migrated import DocumentoCreateView, DocumentoUpdateView
from taller.tests.factories import DocumentoFactory, EmpresaFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_create_view(empresa, **get_params):
    """DocumentoCreateView bound to a GET request, no template rendering."""
    factory = RequestFactory()
    request = factory.get("/cl/documentos/form/", get_params)
    request.user = empresa.user
    view = DocumentoCreateView()
    view.setup(request)
    view.kwargs = {}
    return view


# ---------------------------------------------------------------------------
# 1-5: tipo param on create view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_get_crear_pres_preselecciona_tipo():
    empresa = EmpresaFactory(pais="CL")
    view = _make_create_view(empresa, tipo="PRES")
    initial = view.get_initial()
    assert initial.get("tipo") == "PRES"


@pytest.mark.django_db
def test_form_pres_valido_y_guarda():
    from django.contrib.auth.models import User
    from taller.forms.documento_form import DocumentoForm
    from taller.models.clientes import Cliente

    empresa = EmpresaFactory(pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente Test PRES")

    data = {
        "tipo": "PRES",
        "fecha_emision": date.today().isoformat(),
        "cliente": str(cliente.pk),
        "repuestos_json": "[]",
        "servicios_json": "[]",
        "otros_json": "[]",
    }
    form = DocumentoForm(data=data, user=empresa.user, empresa=empresa, country="CL")
    assert form.is_valid(), form.errors
    doc = form.save()
    assert doc.tipo == "PRES"


@pytest.mark.django_db
def test_get_crear_pts_preselecciona_tipo():
    empresa = EmpresaFactory(pais="CL")
    view = _make_create_view(empresa, tipo="PTS")
    initial = view.get_initial()
    assert initial.get("tipo") == "PTS"


@pytest.mark.django_db
def test_form_pts_valido_y_guarda():
    from taller.forms.documento_form import DocumentoForm
    from taller.models.clientes import Cliente

    empresa = EmpresaFactory(pais="CL")
    cliente = Cliente.objects.create(empresa=empresa, nombre="Cliente Test PTS")

    data = {
        "tipo": "PTS",
        "fecha_emision": date.today().isoformat(),
        "cliente": str(cliente.pk),
        "repuestos_json": "[]",
        "servicios_json": "[]",
        "otros_json": "[]",
    }
    form = DocumentoForm(data=data, user=empresa.user, empresa=empresa, country="CL")
    assert form.is_valid(), form.errors
    doc = form.save()
    assert doc.tipo == "PTS"


@pytest.mark.django_db
def test_tipo_invalido_no_entra_en_initial():
    empresa = EmpresaFactory(pais="CL")
    view = _make_create_view(empresa, tipo="FACTURA_INVALIDA")
    initial = view.get_initial()
    assert initial.get("tipo") != "FACTURA_INVALIDA"


# ---------------------------------------------------------------------------
# 6-7: update view ignores ?tipo= GET param
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_update_view_ignora_tipo_en_get():
    """DocumentoUpdateView.get_initial() no lee tipo de GET — inherited from UpdateView."""
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="PRES", estado="BORRADOR")

    factory = RequestFactory()
    request = factory.get(f"/cl/documentos/form/{doc.pk}/", {"tipo": "PTS"})
    request.user = empresa.user

    view = DocumentoUpdateView()
    view.setup(request)
    view.kwargs = {"pk": doc.pk}

    initial = view.get_initial()
    # UpdateView.get_initial() returns {} — never reads GET params for tipo
    assert initial.get("tipo") != "PTS"


@pytest.mark.django_db
def test_update_view_no_tiene_get_initial_propio():
    """DocumentoUpdateView no sobrescribe get_initial, por lo que no puede leer ?tipo= de GET."""
    assert "get_initial" not in DocumentoUpdateView.__dict__


# ---------------------------------------------------------------------------
# 8: Tenant isolation on update view
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_update_view_filtra_por_empresa():
    empresa_a = EmpresaFactory(pais="CL")
    empresa_b = EmpresaFactory(pais="CL")
    doc_b = DocumentoFactory(empresa=empresa_b, tipo="PRES", estado="BORRADOR")

    factory = RequestFactory()
    request = factory.get(f"/cl/documentos/form/{doc_b.pk}/")
    request.user = empresa_a.user

    view = DocumentoUpdateView()
    view.setup(request)
    view.kwargs = {"pk": doc_b.pk}

    qs = view.get_queryset()
    # Empresa A should not see empresa B's documents
    assert not qs.filter(pk=doc_b.pk).exists()


# ---------------------------------------------------------------------------
# 9-10: PARTS workspace quick_actions structure
# ---------------------------------------------------------------------------

def test_parts_quick_action_new_quote():
    """PARTS workspace tiene una acción con path que incluye ?tipo=PRES."""
    paths = [a.path for a in WORKSPACE_CASA_REPUESTOS.quick_actions]
    assert any("tipo=PRES" in p for p in paths), f"No hay path con tipo=PRES en: {paths}"


def test_parts_quick_action_new_parts_sale():
    """PARTS workspace tiene una acción con path que incluye ?tipo=PTS."""
    paths = [a.path for a in WORKSPACE_CASA_REPUESTOS.quick_actions]
    assert any("tipo=PTS" in p for p in paths), f"No hay path con tipo=PTS en: {paths}"


def test_parts_quick_action_term_keys():
    """Las acciones usan los term_keys correctos para cotización y venta."""
    term_keys = [a.term_key for a in WORKSPACE_CASA_REPUESTOS.quick_actions]
    assert "workspace.parts.action.new_quote" in term_keys
    assert "workspace.parts.action.new_parts_sale" in term_keys


# ---------------------------------------------------------------------------
# 11-12: URL existence for CL and US
# ---------------------------------------------------------------------------

def test_url_cl_documento_crear_existe():
    url = reverse("documentos_cl_es:documento_crear")
    assert url == "/cl/documentos/form/"


def test_url_us_documento_crear_existe():
    url = reverse("documentos_us_en:documento_crear")
    assert url == "/us/documentos/form/"


def test_url_cl_con_tipo_pres_resoluble():
    """La URL /cl/es/documentos/form/ llega a DocumentoCreateView via namespace chile."""
    result = resolve("/cl/es/documentos/form/")
    view_func = result.func
    # Puede ser DocumentoCreateView.as_view() o CBV view
    view_class = getattr(view_func, "view_class", None)
    assert view_class is DocumentoCreateView


def test_url_us_con_tipo_pres_resoluble():
    """La URL /us/en/documentos/form/ llega a DocumentoCreateView via namespace us_en."""
    result = resolve("/us/en/documentos/form/")
    view_func = result.func
    view_class = getattr(view_func, "view_class", None)
    assert view_class is DocumentoCreateView


# ---------------------------------------------------------------------------
# 13: Other workspaces don't have PRES/PTS quick actions
# ---------------------------------------------------------------------------

def test_otros_workspaces_no_tienen_tipo_en_paths():
    """TALLER, DESARM y CARWASH no tienen quick_actions con ?tipo= en sus paths."""
    for ws in (WORKSPACE_TALLER, WORKSPACE_DESARMADURIA, WORKSPACE_CARWASH):
        for action in ws.quick_actions:
            assert "tipo=" not in action.path, (
                f"{ws.product_key}: acción '{action.term_key}' tiene tipo= en path '{action.path}'"
            )


# ---------------------------------------------------------------------------
# 14: Existing PRES conversion still works
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_conversion_pres_a_ot_sigue_funcionando():
    empresa = EmpresaFactory(pais="CL")
    doc = DocumentoFactory(empresa=empresa, tipo="PRES", estado="EMITIDO")
    result = doc.convertir_documento_final()
    assert result is True
    doc.refresh_from_db()
    assert doc.tipo == "OT"


# ---------------------------------------------------------------------------
# 17: manage.py check
# ---------------------------------------------------------------------------

def test_manage_check_limpio():
    out = StringIO()
    call_command("check", stdout=out, stderr=StringIO())
    output = out.getvalue()
    assert "System check identified no issues" in output or "0 issues" in output
