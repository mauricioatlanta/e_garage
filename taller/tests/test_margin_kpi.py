"""
Tests for Sprint 2C: WGT_KPI_MARGIN_MONTH — gross margin KPI for PARTS workspace.

Business rule: margin = (ingreso_conocido − costo_conocido) / ingreso_conocido × 100
where ingreso_conocido and costo_conocido are computed ONLY over STOCK_BODEGA lines
where costo_linea IS NOT NULL (same set for both numerator and denominator).

has_value=False (shows "—") when:
  - no STOCK_BODEGA lines exist
  - coverage (lineas_con_costo / lineas_total) < MIN_MARGIN_COST_COVERAGE (30%)
  - ingreso_conocido <= 0

Covers:
  1.  Margen correcto con una línea y costo conocido
  2.  Descuento porcentual reduce el ingreso
  3.  Cantidad multiplica ingreso y costo
  4.  IVA/sales tax no afecta el margen
  5.  Excluye líneas sin costo del ingreso y del costo conocido
  6.  Cobertura incluye líneas STOCK_BODEGA sin costo
  7.  Cobertura bajo 30% devuelve has_value=False
  8.  Cobertura exactamente 30% permite calcular
  9.  Margen real 0% se muestra como 0,0%, no como "—"
  10. Margen negativo se muestra correctamente
  11. Excluye PRES
  12. Excluye BORRADOR
  13. Excluye ANULADO
  14. Incluye OT, FAC y PTS EMITIDOS
  15. Excluye DESARME y EXTERNO
  16. Excluye documentos de otra empresa
  17. Excluye documentos de meses anteriores
  18. Empresa sin líneas devuelve has_value=False
  19. PARTS incluye el widget
  20. Los demás perfiles no cambian
  21. PARTS mantiene el límite de queries
  22. manage.py check limpio
"""

from datetime import date
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext

from taller.constants.workspaces import (
    WGT_KPI_MARGIN_MONTH,
    WGT_KPI_CLIENTS_MONTH,
    get_workspace_def,
    WORKSPACE_CASA_REPUESTOS,
    WORKSPACE_CARWASH,
    WORKSPACE_DESARMADURIA,
    WORKSPACE_TALLER,
)
from taller.models.lineas_documento import (
    LineaRepuesto,
    ORIGEN_DESARME,
    ORIGEN_EXTERNO,
    ORIGEN_STOCK_BODEGA,
)
from taller.services.workspace_dashboard_service import (
    MIN_MARGIN_COST_COVERAGE,
    WorkspaceDashboardService,
)
from taller.tests.factories import DocumentoFactory, EmpresaFactory, RepuestoFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(empresa, tipo="OT", estado="EMITIDO", fecha_emision=None):
    kwargs = {}
    if fecha_emision is not None:
        kwargs["fecha_emision"] = fecha_emision
    return DocumentoFactory(empresa=empresa, tipo=tipo, estado=estado, **kwargs)


def _make_linea(doc, *, precio_unitario, costo=None, descuento=Decimal("0"), cantidad=1, origen=ORIGEN_STOCK_BODEGA):
    """
    Creates a LineaRepuesto.
    costo=None  → costo_linea stays NULL (not yet frozen).
    costo=X     → costo_linea is set to X via bypass update (simulates frozen cost).
    """
    empresa = doc.empresa
    repuesto = RepuestoFactory(empresa=empresa, precio_venta=precio_unitario, cantidad_stock=10)
    linea = LineaRepuesto.objects.create(
        documento=doc,
        nombre=repuesto.nombre,
        codigo=repuesto.part_number or "T",
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        descuento=descuento,
        origen_repuesto=origen,
        repuesto=repuesto,
    )
    if costo is not None:
        LineaRepuesto.objects.filter(pk=linea.pk).update(costo_linea=costo)
        linea.refresh_from_db()
    return linea


def _resolve_margin(empresa, today=None):
    ws_def = get_workspace_def("PARTS")
    result = WorkspaceDashboardService.resolve(ws_def, empresa, today=today)
    return next(w for w in result["widgets"] if w["key"] == WGT_KPI_MARGIN_MONTH)


# ---------------------------------------------------------------------------
# Core formula tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_margen_correcto_una_linea():
    """Margen = (100 - 70) / 100 × 100 = 30%."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True
    assert round(w["value"], 2) == Decimal("30.00")


@pytest.mark.django_db
def test_descuento_reduce_ingreso():
    """Descuento=20% → ingreso=80, costo=70 → margen=12.5%."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"), descuento=Decimal("20"))

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True
    assert round(w["value"], 2) == Decimal("12.50")


@pytest.mark.django_db
def test_cantidad_multiplica_ingreso_y_costo():
    """Cantidad=5, precio=100, costo=70 → ingreso=500, costo=350 → margen=30%."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"), cantidad=5)

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True
    assert round(w["value"], 2) == Decimal("30.00")


@pytest.mark.django_db
def test_iva_no_afecta_margen():
    """El KPI usa precio_unitario y costo_linea — no el campo IVA del documento."""
    empresa_cl = EmpresaFactory(pais="CL")  # IVA 19%
    doc = _make_doc(empresa_cl)
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))

    empresa_us = EmpresaFactory(pais="US")  # sales tax, not IVA
    doc_us = _make_doc(empresa_us)
    _make_linea(doc_us, precio_unitario=Decimal("100"), costo=Decimal("70"))

    w_cl = _resolve_margin(empresa_cl, today=date.today())
    w_us = _resolve_margin(empresa_us, today=date.today())

    assert round(w_cl["value"], 2) == round(w_us["value"], 2)


@pytest.mark.django_db
def test_excluye_lineas_sin_costo_del_ingreso_y_costo():
    """
    Línea 1 (costo=70) y línea 2 (sin costo).
    ingreso_conocido = 100, costo_conocido = 70 → margen = 30%.
    El precio_unitario=200 de la línea sin costo NO entra en el ingreso.
    """
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))
    _make_linea(doc, precio_unitario=Decimal("200"), costo=None)  # excluida

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True
    # If line 2 were included in ingreso: margin = (300-70)/300 = 76.67% — wrong
    assert round(w["value"], 2) == Decimal("30.00")


# ---------------------------------------------------------------------------
# Coverage tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cobertura_incluye_lineas_sin_costo_en_denominador():
    """
    5 líneas STOCK_BODEGA; 2 tienen costo → cobertura=40% ≥ 30% → has_value=True.
    Verifica que el denominador cuenta todas las líneas STOCK_BODEGA, no solo las conocidas.
    """
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    for _ in range(2):
        _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("60"))
    for _ in range(3):
        _make_linea(doc, precio_unitario=Decimal("100"), costo=None)

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True  # 40% ≥ 30%


@pytest.mark.django_db
def test_cobertura_bajo_30_pct_devuelve_sin_valor():
    """10 líneas, 2 con costo → cobertura=20% < 30% → has_value=False."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    for _ in range(2):
        _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("60"))
    for _ in range(8):
        _make_linea(doc, precio_unitario=Decimal("100"), costo=None)

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is False


@pytest.mark.django_db
def test_cobertura_exactamente_30_pct_permite_calcular():
    """10 líneas, 3 con costo → cobertura=30% exacto → el umbral es >= → has_value=True."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    for _ in range(3):
        _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("60"))
    for _ in range(7):
        _make_linea(doc, precio_unitario=Decimal("100"), costo=None)

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True


@pytest.mark.django_db
def test_margen_cero_muestra_valor_no_guion():
    """precio=100, costo=100 → margen=0%. has_value=True; value=0, no None."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("100"))

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True
    assert w["value"] is not None
    assert round(w["value"], 2) == Decimal("0.00")


@pytest.mark.django_db
def test_margen_negativo_se_muestra_correctamente():
    """precio=100, costo=150 → margen=-50%. Negativo es válido (pérdida real)."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("150"))

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True
    assert round(w["value"], 2) == Decimal("-50.00")


# ---------------------------------------------------------------------------
# Document type / state filters
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_excluye_pres():
    """PRES emitido no cuenta para el margen (nunca fue venta real)."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa, tipo="PRES", estado="EMITIDO")
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is False


@pytest.mark.django_db
def test_excluye_borrador():
    """OT en BORRADOR no cuenta para el margen."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa, tipo="OT", estado="BORRADOR")
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is False


@pytest.mark.django_db
def test_excluye_anulado():
    """OT ANULADO no cuenta para el margen."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa, tipo="OT", estado="ANULADO")
    _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is False


@pytest.mark.django_db
def test_incluye_ot_fac_pts_emitidos():
    """OT, FAC y PTS emitidos se suman correctamente."""
    empresa = EmpresaFactory(pais="CL")
    today = date.today()
    for tipo in ("OT", "FAC", "PTS"):
        doc = _make_doc(empresa, tipo=tipo, estado="EMITIDO")
        _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))

    w = _resolve_margin(empresa, today=today)
    assert w["has_value"] is True
    # 3 lines, each contributes 30% → combined margin still 30%
    assert round(w["value"], 2) == Decimal("30.00")


# ---------------------------------------------------------------------------
# Origin filters
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_excluye_desarme_y_externo():
    """Solo STOCK_BODEGA entra en el cálculo; DESARME y EXTERNO se ignoran."""
    empresa = EmpresaFactory(pais="CL")
    doc = _make_doc(empresa)
    linea_bodega = _make_linea(doc, precio_unitario=Decimal("100"), costo=Decimal("70"))

    # Force two extra lines to other origins with sentinel costs
    linea_extra_a = _make_linea(doc, precio_unitario=Decimal("999"), costo=Decimal("999"))
    linea_extra_b = _make_linea(doc, precio_unitario=Decimal("999"), costo=Decimal("999"))
    LineaRepuesto.objects.filter(pk=linea_extra_a.pk).update(
        origen_repuesto=ORIGEN_DESARME, repuesto=None, pieza_desarme=None
    )
    LineaRepuesto.objects.filter(pk=linea_extra_b.pk).update(
        origen_repuesto=ORIGEN_EXTERNO, repuesto=None
    )

    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is True
    # Only linea_bodega counted: margin = 30%
    assert round(w["value"], 2) == Decimal("30.00")


# ---------------------------------------------------------------------------
# Tenant isolation / date scope
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_excluye_documentos_de_otra_empresa():
    """Datos de otra empresa no contaminan el KPI."""
    empresa_a = EmpresaFactory(pais="CL")
    empresa_b = EmpresaFactory(pais="CL")
    today = date.today()

    doc_a = _make_doc(empresa_a)
    _make_linea(doc_a, precio_unitario=Decimal("100"), costo=Decimal("70"))

    doc_b = _make_doc(empresa_b)
    _make_linea(doc_b, precio_unitario=Decimal("999"), costo=Decimal("1"))

    w = _resolve_margin(empresa_a, today=today)
    assert round(w["value"], 2) == Decimal("30.00")


@pytest.mark.django_db
def test_excluye_documentos_de_meses_anteriores():
    """Solo fecha_emision en el mes corriente de 'today' se incluye."""
    empresa = EmpresaFactory(pais="CL")
    today = date(2026, 7, 31)

    doc_este_mes = _make_doc(empresa, fecha_emision=date(2026, 7, 1))
    _make_linea(doc_este_mes, precio_unitario=Decimal("100"), costo=Decimal("70"))

    doc_mes_anterior = _make_doc(empresa, fecha_emision=date(2026, 6, 30))
    _make_linea(doc_mes_anterior, precio_unitario=Decimal("999"), costo=Decimal("1"))

    w = _resolve_margin(empresa, today=today)
    assert w["has_value"] is True
    assert round(w["value"], 2) == Decimal("30.00")


@pytest.mark.django_db
def test_empresa_sin_lineas_devuelve_sin_valor():
    """Sin documentos ni líneas → has_value=False."""
    empresa = EmpresaFactory(pais="CL")
    w = _resolve_margin(empresa, today=date.today())
    assert w["has_value"] is False


# ---------------------------------------------------------------------------
# Workspace configuration
# ---------------------------------------------------------------------------

def test_parts_incluye_widget_margin_month():
    """WORKSPACE_CASA_REPUESTOS tiene WGT_KPI_MARGIN_MONTH."""
    assert WGT_KPI_MARGIN_MONTH in WORKSPACE_CASA_REPUESTOS.widget_keys


def test_parts_no_incluye_clients_month():
    """WORKSPACE_CASA_REPUESTOS reemplazó kpi_clients_month con kpi_margin_month."""
    assert WGT_KPI_CLIENTS_MONTH not in WORKSPACE_CASA_REPUESTOS.widget_keys


def test_otros_perfiles_no_tienen_margin_month():
    """Taller, Desarmaduria y Carwash no incluyen el widget de margen."""
    for ws in (WORKSPACE_TALLER, WORKSPACE_DESARMADURIA, WORKSPACE_CARWASH):
        assert WGT_KPI_MARGIN_MONTH not in ws.widget_keys, f"{ws.product_key} no debería tener margin_month"


# ---------------------------------------------------------------------------
# Query count
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_parts_limite_de_queries():
    """PARTS ejecuta ≤ 4 queries (DOCS + INVENTORY + LINEAS, sin CLIENTS)."""
    empresa = EmpresaFactory(pais="CL")
    ws_def = get_workspace_def("PARTS")

    with CaptureQueriesContext(connection) as ctx:
        WorkspaceDashboardService.resolve(ws_def, empresa, today=date.today())

    assert len(ctx) <= 4, f"Demasiadas queries: {len(ctx)}"


# ---------------------------------------------------------------------------
# System check
# ---------------------------------------------------------------------------

def test_manage_check_limpio():
    """manage.py check no reporta errores de sistema."""
    out = StringIO()
    call_command("check", stdout=out, stderr=StringIO())
    output = out.getvalue()
    assert "System check identified no issues" in output or "0 issues" in output
