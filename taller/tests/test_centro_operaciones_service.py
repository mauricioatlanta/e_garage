"""
Tests for CentroOperacionesService.

Covers:
  - Contract: build_context() returns all keys expected by templates
  - Types: key values have the correct Python types
  - include_charts=False vs True: chart_data_json contents
  - Alertas structure: each entry has required keys
  - Projections: zero when no documents in current month
  - IVA logic: applied for CL, skipped for other countries
  - Checklist: reflects actual entity presence
  - No exception with an empty dataset (empresa with no activity)
"""

import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from taller.services.centro_operaciones_service import CentroOperacionesService
from taller.tests.factories import (
    ClienteFactory,
    DocumentoFactory,
    EmpresaFactory,
    UserFactory,
)

# ---------------------------------------------------------------------------
# Expected context keys — the contract between service and templates
# ---------------------------------------------------------------------------

_BASE_KEYS = {
    "empresa",
    "pais_emoji",
    "moneda",
    # document KPIs
    "documentos_hoy",
    "documentos_semana",
    "documentos_mes",
    "total_documentos",
    # billing KPIs
    "facturacion_servicios_hoy",
    "facturacion_servicios_semana",
    "facturacion_servicios_mes",
    "total_repuestos_mes",
    "iva_repuestos",
    "facturacion_mes_total",
    # client KPIs
    "clientes_activos",
    "clientes_nuevos_mes",
    "clientes_atendidos_semana",
    # staff
    "tecnicos_activos",
    # rankings
    "servicios_top",
    "tecnicos_productivos",
    # document state
    "presupuestos_pendientes",
    "ordenes_en_proceso",
    "presupuestos_mes",
    "facturas_mes",
    # vehicles
    "vehiculos_registrados",
    "marcas_atendidas",
    # alerts
    "alertas",
    "clientes_inactivos",
    # projections & efficiency
    "proyeccion_docs_mes",
    "proyeccion_facturacion",
    "ticket_promedio",
    "eficiencia_conversion",
    # onboarding
    "checklist_onboarding",
    "checklist_completo",
    # dates
    "fecha_hoy",
    "mes_actual",
    # charts & branding (always present, populated conditionally)
    "chart_data_json",
    "BRAND",
    "company_name",
    "company_logo_url",
    "company_color",
    "company_tagline",
}


@pytest.fixture
def empresa(db):
    return EmpresaFactory(pais="CL", with_config=True)


@pytest.fixture
def empresa_us(db):
    return EmpresaFactory(pais="US", with_config=True)


@pytest.fixture
def user(db):
    return UserFactory()


# ---------------------------------------------------------------------------
# Contract: all template keys must be present
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_build_context_returns_all_expected_keys(empresa):
    ctx = CentroOperacionesService.build_context(empresa)
    missing = _BASE_KEYS - ctx.keys()
    assert not missing, f"Missing context keys: {missing}"


@pytest.mark.django_db
def test_build_context_with_charts_returns_all_expected_keys(empresa, user):
    with patch("taller.services.branding_service.BrandingService") as mock_brand:
        mock_brand.get_brand.return_value.as_dict.return_value = {
            "name": "Test", "logo_url": "", "primary_color": "#fff", "tagline": ""
        }
        ctx = CentroOperacionesService.build_context(empresa, user=user, include_charts=True)

    missing = _BASE_KEYS - ctx.keys()
    assert not missing, f"Missing context keys: {missing}"


# ---------------------------------------------------------------------------
# Types: values must be the right Python types (no accidental strings for ints)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_build_context_value_types(empresa):
    ctx = CentroOperacionesService.build_context(empresa)

    assert isinstance(ctx["documentos_hoy"], int)
    assert isinstance(ctx["documentos_semana"], int)
    assert isinstance(ctx["documentos_mes"], int)
    assert isinstance(ctx["total_documentos"], int)
    assert isinstance(ctx["clientes_activos"], int)
    assert isinstance(ctx["tecnicos_activos"], int)
    assert isinstance(ctx["vehiculos_registrados"], int)
    assert isinstance(ctx["ticket_promedio"], Decimal)
    assert isinstance(ctx["iva_repuestos"], Decimal)
    assert isinstance(ctx["facturacion_mes_total"], Decimal)
    assert isinstance(ctx["eficiencia_conversion"], float)
    assert isinstance(ctx["proyeccion_docs_mes"], int)
    assert isinstance(ctx["alertas"], list)
    assert isinstance(ctx["servicios_top"], list)
    assert isinstance(ctx["tecnicos_productivos"], list)
    assert isinstance(ctx["checklist_onboarding"], dict)
    assert isinstance(ctx["checklist_completo"], bool)
    assert isinstance(ctx["fecha_hoy"], date)


# ---------------------------------------------------------------------------
# include_charts=False: chart_data_json is the empty-sentinel, no branding
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_include_charts_false_returns_empty_sentinel(empresa):
    ctx = CentroOperacionesService.build_context(empresa, include_charts=False)

    assert ctx["chart_data_json"] == "{}"
    assert ctx["BRAND"] == {}
    assert ctx["company_name"] == ""


@pytest.mark.django_db
def test_include_charts_true_returns_valid_json(empresa, user):
    with patch("taller.services.branding_service.BrandingService") as mock_brand:
        mock_brand.get_brand.return_value.as_dict.return_value = {
            "name": "Mi Taller", "logo_url": "/logo.png",
            "primary_color": "#0ff", "tagline": "Siempre listos",
        }
        ctx = CentroOperacionesService.build_context(empresa, user=user, include_charts=True)

    data = json.loads(ctx["chart_data_json"])
    assert "ingresos_mensuales" in data
    assert "servicios" in data
    assert "tecnicos" in data
    assert isinstance(data["ingresos_mensuales"]["labels"], list)
    assert isinstance(data["ingresos_mensuales"]["data"], list)
    assert len(data["ingresos_mensuales"]["labels"]) == 7


@pytest.mark.django_db
def test_include_charts_true_populates_brand(empresa, user):
    with patch("taller.services.branding_service.BrandingService") as mock_brand:
        mock_brand.get_brand.return_value.as_dict.return_value = {
            "name": "Mi Taller", "logo_url": "/logo.png",
            "primary_color": "#0ff", "tagline": "Siempre listos",
        }
        ctx = CentroOperacionesService.build_context(empresa, user=user, include_charts=True)

    assert ctx["company_name"] == "Mi Taller"
    assert ctx["company_logo_url"] == "/logo.png"
    assert ctx["BRAND"]["primary_color"] == "#0ff"


# ---------------------------------------------------------------------------
# IVA: applied only for CL, zero for other countries
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_iva_is_zero_for_non_cl(empresa_us):
    ctx = CentroOperacionesService.build_context(empresa_us)
    assert ctx["iva_repuestos"] == Decimal("0.00")


@pytest.mark.django_db
def test_iva_cl_rate_is_19pct(db):
    """Unit: _kpis_facturacion applies 19% IVA on repuestos for CL, zero for others.

    Patches _sum_subtotal so no LineaRepuesto fixtures are needed; the queryset
    is built (needs a real empresa.id) but aggregation is intercepted.
    """
    from datetime import timedelta

    empresa_cl = EmpresaFactory(pais="CL", with_config=True)
    empresa_us = EmpresaFactory(pais="US", with_config=True)
    hoy = date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)
    hace_7 = hoy - timedelta(days=7)

    repuestos_total = Decimal("10000.00")

    # Actual call order inside _kpis_facturacion:
    #   1. _sum_subtotal(base_mes_srv)  → facturacion_servicios_mes (computed early)
    #   2. _sum_subtotal(base_mes_rep)  → total_repuestos_mes       (computed early)
    #   3. _sum_subtotal(base_hoy)      → facturacion_servicios_hoy (in return dict)
    #   4. _sum_subtotal(base_sem)      → facturacion_servicios_semana (in return dict)
    with patch(
        "taller.services.centro_operaciones_service._sum_subtotal",
        side_effect=[
            Decimal("0"), repuestos_total, Decimal("0"), Decimal("0"),   # CL call
            Decimal("0"), repuestos_total, Decimal("0"), Decimal("0"),   # US call
        ],
    ):
        result_cl = CentroOperacionesService._kpis_facturacion(empresa_cl, hoy, hace_7, inicio_mes)
        result_us = CentroOperacionesService._kpis_facturacion(empresa_us, hoy, hace_7, inicio_mes)

    assert result_cl["iva_repuestos"] == Decimal("1900.00")
    assert result_us["iva_repuestos"] == Decimal("0.00")


# ---------------------------------------------------------------------------
# Projections: zero when no documents in current month
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_projections_zero_when_no_documents(empresa):
    ctx = CentroOperacionesService.build_context(empresa)

    assert ctx["proyeccion_docs_mes"] == 0
    assert ctx["proyeccion_facturacion"] == 0


# ---------------------------------------------------------------------------
# Alertas: structure and content
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_alertas_empty_with_no_activity(empresa):
    ctx = CentroOperacionesService.build_context(empresa)
    assert ctx["alertas"] == []
    assert ctx["clientes_inactivos"] == 0


@pytest.mark.django_db
def test_alertas_have_required_keys(db):
    """Old presupuesto (>15 days) triggers an alerta with required structure."""
    from datetime import timedelta

    empresa = EmpresaFactory(pais="CL", with_config=True)
    hoy = date.today()
    fecha_vieja = hoy - timedelta(days=20)
    cliente = ClienteFactory(empresa=empresa)
    DocumentoFactory(empresa=empresa, cliente=cliente, tipo="PRES", fecha_emision=fecha_vieja)

    ctx = CentroOperacionesService.build_context(empresa)

    assert len(ctx["alertas"]) >= 1
    for alerta in ctx["alertas"]:
        assert "tipo" in alerta
        assert "titulo" in alerta
        assert "descripcion" in alerta
        assert "accion" in alerta


# ---------------------------------------------------------------------------
# Checklist: reflects actual entity presence
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_checklist_all_false_on_empty_empresa(empresa):
    ctx = CentroOperacionesService.build_context(empresa)
    checklist = ctx["checklist_onboarding"]

    assert checklist["tecnico_creado"] is False
    assert checklist["cliente_creado"] is False
    assert checklist["vehiculo_creado"] is False
    assert checklist["documento_creado"] is False
    assert ctx["checklist_completo"] is False


@pytest.mark.django_db
def test_checklist_cliente_true_after_creating_one(db):
    empresa = EmpresaFactory(pais="CL", with_config=True)
    ClienteFactory(empresa=empresa)

    ctx = CentroOperacionesService.build_context(empresa)

    assert ctx["checklist_onboarding"]["cliente_creado"] is True


# ---------------------------------------------------------------------------
# Smoke test: no exception on completely empty dataset
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_build_context_no_exception_empty_db(empresa):
    ctx = CentroOperacionesService.build_context(empresa)
    assert ctx is not None


@pytest.mark.django_db
def test_build_context_with_charts_no_exception_empty_db(empresa, user):
    with patch("taller.services.branding_service.BrandingService") as mock_brand:
        mock_brand.get_brand.return_value.as_dict.return_value = {
            "name": "", "logo_url": "", "primary_color": "", "tagline": ""
        }
        ctx = CentroOperacionesService.build_context(empresa, user=user, include_charts=True)
    assert ctx is not None


# ---------------------------------------------------------------------------
# Eficiencia conversion: stays within [0, 100]
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_eficiencia_conversion_range(empresa):
    ctx = CentroOperacionesService.build_context(empresa)
    assert 0 <= ctx["eficiencia_conversion"] <= 100


# ---------------------------------------------------------------------------
# Both views use the same service (structural guard)
# ---------------------------------------------------------------------------

def test_views_import_centro_operaciones_service():
    """Guard: both views must import from CentroOperacionesService, not inline ORM."""
    import inspect
    from taller.views_extra import dashboard_empresa

    source = inspect.getsource(dashboard_empresa)
    assert "CentroOperacionesService" in source
    assert "Documento.objects" not in source
    assert "Cliente.objects" not in source
    assert "LineaServicio.objects" not in source
