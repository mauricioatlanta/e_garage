"""
Tests for Workspace UI 2.0 layer.

Covers:
  - WorkspaceService.resolve() — zero ORM queries
  - Widget presence/absence per product
  - Terminology resolution (ES/EN)
  - WorkspaceDashboardService query count bounds
"""
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase, override_settings
from django.test.utils import override_settings
from django.utils import translation

from taller.constants.business_modules import (
    MOD_CLIENTES,
    MOD_CONFIGURACION,
    MOD_DESARME,
    MOD_DOCUMENTOS,
    MOD_INICIO,
    MOD_REPUESTOS,
    MOD_REPORTES,
    MOD_SERVICIOS,
    MOD_VEHICULOS,
)
from taller.constants.product_profiles import (
    PRODUCT_CARWASH,
    PRODUCT_CASA_REPUESTOS,
    PRODUCT_DESARMADURIA,
    PRODUCT_TALLER,
)
from taller.constants.workspaces import (
    WGT_KPI_CLIENTS_MONTH,
    WGT_KPI_DESARM_AVAIL,
    WGT_KPI_DESARM_DEPLETED,
    WGT_KPI_DOCS_TODAY,
    WGT_KPI_INVENTORY_VALUE,
    WGT_KPI_OT_OPEN,
    WGT_KPI_PARTS_COUNT,
    WGT_KPI_PARTS_SOLD_TODAY,
    WGT_KPI_QUOTES_PENDING,
    WGT_KPI_SALES_TODAY,
    WGT_KPI_SERVICES_TODAY,
    WGT_KPI_STOCK_CRITICAL,
    WORKSPACE_CARWASH,
    WORKSPACE_CASA_REPUESTOS,
    WORKSPACE_DESARMADURIA,
    WORKSPACE_TALLER,
    get_workspace_def,
)
from taller.services.workspace_service import WorkspaceService


def _make_config(rubro="WORKSHOP", usa_vehiculos=True, usa_servicios=True, rubros_extra=None):
    """Returns a mock ConfiguracionEmpresa with the given attributes."""
    cfg = MagicMock()
    cfg.rubro_principal = rubro
    cfg.usa_vehiculos = usa_vehiculos
    cfg.usa_servicios = usa_servicios
    cfg.rubros = rubros_extra or []
    return cfg


class WorkspaceDefResolutionTests(TestCase):
    """get_workspace_def() returns the correct WorkspaceDef per rubro."""

    def test_workshop_returns_taller(self):
        ws = get_workspace_def("WORKSHOP")
        self.assertEqual(ws.product_key, PRODUCT_TALLER)

    def test_mixed_returns_desarmaduria(self):
        ws = get_workspace_def("MIXED")
        self.assertEqual(ws.product_key, PRODUCT_DESARMADURIA)

    def test_parts_returns_casa_repuestos(self):
        ws = get_workspace_def("PARTS")
        self.assertEqual(ws.product_key, PRODUCT_CASA_REPUESTOS)

    def test_detailing_returns_carwash(self):
        ws = get_workspace_def("DETAILING")
        self.assertEqual(ws.product_key, PRODUCT_CARWASH)

    def test_none_returns_taller(self):
        ws = get_workspace_def(None)
        self.assertEqual(ws.product_key, PRODUCT_TALLER)

    def test_unknown_rubro_returns_taller(self):
        ws = get_workspace_def("DOES_NOT_EXIST")
        self.assertEqual(ws.product_key, PRODUCT_TALLER)

    def test_all_workshop_variants_resolve_to_taller(self):
        for rubro in ["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY", "EXHAUST", "BODYSHOP",
                      "ELECTRIC", "GLASS_AUDIO", "SUSPENSION_STEERING", "BRAKES",
                      "OBD_DIAGNOSTIC", "CLASSIC_CARS", "AUDIO_ENTERTAINMENT",
                      "GAS_CONVERSION", "BODY_GLASS", "TUNING", "FLEET", "FLEET_REPAIR"]:
            ws = get_workspace_def(rubro)
            self.assertEqual(ws.product_key, PRODUCT_TALLER, f"{rubro} should map to TALLER")


class WorkspaceServiceZeroQueryTests(TestCase):
    """WorkspaceService.resolve() must execute zero ORM queries."""

    def test_resolve_taller_zero_queries(self):
        config = _make_config("WORKSHOP")
        with self.assertNumQueries(0):
            result = WorkspaceService.resolve(config, "/cl/es", "/cl/es/dashboard/")
        self.assertIn("brand", result)
        self.assertIn("nav", result)
        self.assertIn("widget_keys", result)
        self.assertIn("quick_actions", result)
        self.assertIn("theme", result)

    def test_resolve_desarmaduria_zero_queries(self):
        config = _make_config("MIXED")
        with self.assertNumQueries(0):
            WorkspaceService.resolve(config, "/cl/es", "/cl/es/dashboard/")

    def test_resolve_carwash_zero_queries(self):
        config = _make_config("DETAILING")
        with self.assertNumQueries(0):
            WorkspaceService.resolve(config, "/cl/es", "/cl/es/dashboard/")

    def test_resolve_config_none_zero_queries(self):
        with self.assertNumQueries(0):
            WorkspaceService.resolve(None, "/cl/es", "/cl/es/dashboard/")


class WorkspaceBrandTests(TestCase):
    """Resolved brand dict contains expected keys."""

    def test_taller_brand_keys(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config)
        brand = ws["brand"]
        self.assertIn("product_name", brand)
        self.assertIn("tagline", brand)
        self.assertIn("icon", brand)
        self.assertIn("color_class", brand)
        self.assertIn("product_key", brand)

    def test_taller_icon_is_wrench(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config)
        self.assertEqual(ws["brand"]["icon"], "fas fa-wrench")

    def test_desarm_icon_is_car_crash(self):
        config = _make_config("MIXED")
        ws = WorkspaceService.resolve(config)
        self.assertEqual(ws["brand"]["icon"], "fas fa-car-crash")

    def test_carwash_icon_is_tint(self):
        config = _make_config("DETAILING")
        ws = WorkspaceService.resolve(config)
        self.assertEqual(ws["brand"]["icon"], "fas fa-tint")

    def test_parts_color_is_lime(self):
        config = _make_config("PARTS")
        ws = WorkspaceService.resolve(config)
        self.assertEqual(ws["brand"]["color_class"], "lime")


class WorkspaceNavTests(TestCase):
    """Resolved nav list respects active modules and product ordering."""

    def test_taller_nav_contains_inicio(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config, "/cl/es", "")
        keys = [item["key"] for item in ws["nav"]]
        self.assertIn(MOD_INICIO, keys)

    def test_taller_nav_contains_documentos(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config, "/cl/es", "")
        keys = [item["key"] for item in ws["nav"]]
        self.assertIn(MOD_DOCUMENTOS, keys)

    def test_carwash_nav_excludes_desarme(self):
        config = _make_config("DETAILING")
        ws = WorkspaceService.resolve(config, "/cl/es", "")
        keys = [item["key"] for item in ws["nav"]]
        self.assertNotIn(MOD_DESARME, keys)

    def test_parts_nav_excludes_vehiculos(self):
        config = _make_config("PARTS")
        ws = WorkspaceService.resolve(config, "/cl/es", "")
        keys = [item["key"] for item in ws["nav"]]
        self.assertNotIn(MOD_VEHICULOS, keys)

    def test_desarm_nav_includes_desarme(self):
        config = _make_config("MIXED")
        ws = WorkspaceService.resolve(config, "/cl/es", "")
        keys = [item["key"] for item in ws["nav"]]
        self.assertIn(MOD_DESARME, keys)

    def test_nav_items_have_required_keys(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config, "/cl/es", "")
        for item in ws["nav"]:
            self.assertIn("key", item)
            self.assertIn("label", item)
            self.assertIn("url", item)
            self.assertIn("icon", item)
            self.assertIn("is_active", item)

    def test_nav_urls_include_prefix(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config, "/us/en", "")
        for item in ws["nav"]:
            self.assertTrue(item["url"].startswith("/us/en/"), item["url"])

    def test_active_item_detected_by_path_hint(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config, "/cl/es", "/cl/es/documentos/")
        doc_item = next(i for i in ws["nav"] if i["key"] == MOD_DOCUMENTOS)
        self.assertTrue(doc_item["is_active"])

    def test_inactive_item_not_active(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config, "/cl/es", "/cl/es/documentos/")
        cliente_item = next((i for i in ws["nav"] if i["key"] == MOD_CLIENTES), None)
        if cliente_item:
            self.assertFalse(cliente_item["is_active"])

    def test_usa_vehiculos_false_removes_vehiculos(self):
        config = _make_config("WORKSHOP", usa_vehiculos=False)
        ws = WorkspaceService.resolve(config, "/cl/es", "")
        keys = [item["key"] for item in ws["nav"]]
        self.assertNotIn(MOD_VEHICULOS, keys)


class WorkspaceWidgetKeyTests(TestCase):
    """Each workspace declares the correct widget_keys for its product."""

    def test_taller_widget_keys(self):
        ws = get_workspace_def("WORKSHOP")
        self.assertIn(WGT_KPI_OT_OPEN, ws.widget_keys)
        self.assertIn(WGT_KPI_DOCS_TODAY, ws.widget_keys)
        self.assertIn(WGT_KPI_SALES_TODAY, ws.widget_keys)
        self.assertIn(WGT_KPI_CLIENTS_MONTH, ws.widget_keys)

    def test_taller_has_no_desarm_widget(self):
        ws = get_workspace_def("WORKSHOP")
        self.assertNotIn(WGT_KPI_DESARM_AVAIL, ws.widget_keys)

    def test_taller_has_no_stock_critical_widget(self):
        ws = get_workspace_def("WORKSHOP")
        self.assertNotIn(WGT_KPI_STOCK_CRITICAL, ws.widget_keys)

    def test_desarm_widget_keys(self):
        ws = get_workspace_def("MIXED")
        self.assertIn(WGT_KPI_DESARM_AVAIL, ws.widget_keys)
        self.assertIn(WGT_KPI_DESARM_DEPLETED, ws.widget_keys)
        self.assertIn(WGT_KPI_PARTS_COUNT, ws.widget_keys)
        self.assertIn(WGT_KPI_PARTS_SOLD_TODAY, ws.widget_keys)

    def test_desarm_has_no_ot_open_widget(self):
        ws = get_workspace_def("MIXED")
        self.assertNotIn(WGT_KPI_OT_OPEN, ws.widget_keys)

    def test_desarm_excludes_generic_inventory_value(self):
        ws = get_workspace_def("MIXED")
        self.assertNotIn(WGT_KPI_INVENTORY_VALUE, ws.widget_keys)

    def test_parts_widget_keys(self):
        ws = get_workspace_def("PARTS")
        self.assertIn(WGT_KPI_STOCK_CRITICAL, ws.widget_keys)
        self.assertIn(WGT_KPI_SALES_TODAY, ws.widget_keys)

    def test_parts_includes_quotes_pending_widget(self):
        ws = get_workspace_def("PARTS")
        self.assertIn(WGT_KPI_QUOTES_PENDING, ws.widget_keys)

    def test_parts_excludes_docs_today_widget(self):
        ws = get_workspace_def("PARTS")
        self.assertNotIn(WGT_KPI_DOCS_TODAY, ws.widget_keys)

    def test_workshop_still_includes_docs_today(self):
        ws = get_workspace_def("WORKSHOP")
        self.assertIn(WGT_KPI_DOCS_TODAY, ws.widget_keys)

    def test_desarm_uses_parts_sold_today_not_docs_today(self):
        ws = get_workspace_def("MIXED")
        self.assertIn(WGT_KPI_PARTS_SOLD_TODAY, ws.widget_keys)
        self.assertNotIn(WGT_KPI_DOCS_TODAY, ws.widget_keys)

    def test_carwash_still_includes_docs_today(self):
        ws = get_workspace_def("DETAILING")
        self.assertIn(WGT_KPI_DOCS_TODAY, ws.widget_keys)

    def test_parts_has_no_desarm_widget(self):
        ws = get_workspace_def("PARTS")
        self.assertNotIn(WGT_KPI_DESARM_AVAIL, ws.widget_keys)

    def test_carwash_widget_keys(self):
        ws = get_workspace_def("DETAILING")
        self.assertIn(WGT_KPI_SERVICES_TODAY, ws.widget_keys)
        self.assertIn(WGT_KPI_SALES_TODAY, ws.widget_keys)

    def test_carwash_has_no_ot_open_widget(self):
        ws = get_workspace_def("DETAILING")
        self.assertNotIn(WGT_KPI_OT_OPEN, ws.widget_keys)

    def test_carwash_has_no_desarm_widget(self):
        ws = get_workspace_def("DETAILING")
        self.assertNotIn(WGT_KPI_DESARM_AVAIL, ws.widget_keys)


class WorkspaceThemeTests(TestCase):
    """Each workspace declares CSS custom properties in its theme dict."""

    def test_taller_theme_has_primary(self):
        self.assertIn("--eg-primary", WORKSPACE_TALLER.theme)

    def test_desarm_theme_has_primary(self):
        self.assertIn("--eg-primary", WORKSPACE_DESARMADURIA.theme)

    def test_parts_theme_has_primary(self):
        self.assertIn("--eg-primary", WORKSPACE_CASA_REPUESTOS.theme)

    def test_carwash_theme_has_primary(self):
        self.assertIn("--eg-primary", WORKSPACE_CARWASH.theme)

    def test_each_workspace_has_distinct_primary_color(self):
        primaries = {
            ws.theme["--eg-primary"]
            for ws in [WORKSPACE_TALLER, WORKSPACE_DESARMADURIA,
                        WORKSPACE_CASA_REPUESTOS, WORKSPACE_CARWASH]
        }
        self.assertEqual(len(primaries), 4)


class WorkspaceTerminologyTests(TestCase):
    """Terminology resolution returns strings, never raw keys."""

    def test_taller_brand_name_is_string(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config)
        self.assertIsInstance(ws["brand"]["product_name"], str)
        self.assertGreater(len(ws["brand"]["product_name"]), 0)

    def test_taller_tagline_is_string(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config)
        self.assertIsInstance(ws["brand"]["tagline"], str)

    def test_nav_labels_are_strings(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config)
        for item in ws["nav"]:
            self.assertIsInstance(item["label"], str, f"label for {item['key']} is not str")
            self.assertGreater(len(item["label"]), 0)

    def test_quick_action_labels_are_strings(self):
        config = _make_config("WORKSHOP")
        ws = WorkspaceService.resolve(config)
        for action in ws["quick_actions"]:
            self.assertIsInstance(action["label"], str)
            self.assertGreater(len(action["label"]), 0)


class WorkspaceDashboardServiceTests(TestCase):
    """WorkspaceDashboardService.resolve() executes ≤ 4 queries."""

    def _make_empresa(self, rubro="WORKSHOP"):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory(nombre_taller=f"Test {rubro}", pais="CL")

    def test_taller_dashboard_query_count(self):
        # TALLER: GROUP_DOCS + GROUP_CLIENTS + ACTIVITY_FEED = 3 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("WORKSHOP")
        ws_def = get_workspace_def("WORKSHOP")
        with self.assertNumQueries(3):
            result = WorkspaceDashboardService.resolve(ws_def, empresa)
        self.assertIn("widgets", result)
        self.assertIn("date", result)
        self.assertIn("activity_feed", result)

    def test_desarm_dashboard_query_count(self):
        # DESARM: GROUP_INVENTORY + GROUP_DESARM + GROUP_PARTS_TODAY + ACTIVITY_FEED = 4 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("MIXED")
        ws_def = get_workspace_def("MIXED")
        with self.assertNumQueries(4):
            WorkspaceDashboardService.resolve(ws_def, empresa)

    def test_parts_dashboard_query_count(self):
        # PARTS: GROUP_DOCS + GROUP_INVENTORY + GROUP_LINEAS + ACTIVITY_FEED = 4 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("PARTS")
        ws_def = get_workspace_def("PARTS")
        with self.assertNumQueries(4):
            WorkspaceDashboardService.resolve(ws_def, empresa)

    def test_carwash_dashboard_query_count(self):
        # CARWASH: GROUP_DOCS + GROUP_CLIENTS + ACTIVITY_FEED = 3 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("DETAILING")
        ws_def = get_workspace_def("DETAILING")
        with self.assertNumQueries(3):
            WorkspaceDashboardService.resolve(ws_def, empresa)

    def test_widgets_have_required_keys(self):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("WORKSHOP")
        ws_def = get_workspace_def("WORKSHOP")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        for w in result["widgets"]:
            self.assertIn("key", w)
            self.assertIn("title", w)
            self.assertIn("icon", w)
            self.assertIn("value", w)
            self.assertIn("format", w)

    def test_taller_widget_count_matches_def(self):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("WORKSHOP")
        ws_def = get_workspace_def("WORKSHOP")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        self.assertEqual(len(result["widgets"]), len(ws_def.widget_keys))

    def test_widget_keys_in_workspace_order(self):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("WORKSHOP")
        ws_def = get_workspace_def("WORKSHOP")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        returned_keys = [w["key"] for w in result["widgets"]]
        self.assertEqual(returned_keys, list(ws_def.widget_keys))

    def test_sales_widget_format_is_currency(self):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("WORKSHOP")
        ws_def = get_workspace_def("WORKSHOP")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        sales = next(w for w in result["widgets"] if w["key"] == WGT_KPI_SALES_TODAY)
        self.assertEqual(sales["format"], "currency")

    def test_ot_open_widget_format_is_number(self):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("WORKSHOP")
        ws_def = get_workspace_def("WORKSHOP")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        ot = next(w for w in result["widgets"] if w["key"] == WGT_KPI_OT_OPEN)
        self.assertEqual(ot["format"], "number")


class WorkspaceQuotesPendingServiceTests(TestCase):
    """
    Sprint 2A — WGT_KPI_QUOTES_PENDING data correctness.

    Verifies the aggregate counts presupuestos pendientes accurately:
      - Includes BORRADOR and EMITIDO (tipo=PRES)
      - Excludes ANULADO
      - Excludes converted docs (tipo changed to OT/FAC on conversion)
      - Enforces multi-tenant isolation
    """

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory(nombre_taller="Parts Co", pais="CL")

    def _resolve_parts(self, empresa, today=None):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        ws_def = get_workspace_def("PARTS")
        result = WorkspaceDashboardService.resolve(ws_def, empresa, today=today)
        widget = next(w for w in result["widgets"] if w["key"] == WGT_KPI_QUOTES_PENDING)
        return widget["value"]

    def _make_doc(self, empresa, tipo, estado):
        from taller.tests.factories import DocumentoFactory
        return DocumentoFactory(empresa=empresa, tipo=tipo, estado=estado)

    def test_zero_when_no_documents(self):
        empresa = self._make_empresa()
        self.assertEqual(self._resolve_parts(empresa), 0)

    def test_counts_emitido_pres(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, "PRES", "EMITIDO")
        self._make_doc(empresa, "PRES", "EMITIDO")
        self.assertEqual(self._resolve_parts(empresa), 2)

    def test_counts_borrador_pres(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, "PRES", "BORRADOR")
        self.assertEqual(self._resolve_parts(empresa), 1)

    def test_counts_borrador_and_emitido_together(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, "PRES", "BORRADOR")
        self._make_doc(empresa, "PRES", "EMITIDO")
        self.assertEqual(self._resolve_parts(empresa), 2)

    def test_excludes_anulado_pres(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, "PRES", "EMITIDO")
        self._make_doc(empresa, "PRES", "ANULADO")
        self.assertEqual(self._resolve_parts(empresa), 1)

    def test_excludes_converted_docs(self):
        """Converted PRES change tipo to OT/FAC — they must not appear in count."""
        empresa = self._make_empresa()
        self._make_doc(empresa, "OT", "EMITIDO")   # converted CL
        self._make_doc(empresa, "FAC", "EMITIDO")  # converted US
        self.assertEqual(self._resolve_parts(empresa), 0)

    def test_excludes_other_tipo_docs(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, "PTS", "EMITIDO")  # Venta Repuestos, not a quote
        self.assertEqual(self._resolve_parts(empresa), 0)

    def test_no_cross_tenant(self):
        empresa_a = self._make_empresa()
        empresa_b = self._make_empresa()
        self._make_doc(empresa_b, "PRES", "EMITIDO")
        self._make_doc(empresa_b, "PRES", "EMITIDO")
        self._make_doc(empresa_a, "PRES", "EMITIDO")
        self.assertEqual(self._resolve_parts(empresa_a), 1)

    def test_quotes_pending_widget_format_is_number(self):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa()
        ws_def = get_workspace_def("PARTS")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        widget = next(w for w in result["widgets"] if w["key"] == WGT_KPI_QUOTES_PENDING)
        self.assertEqual(widget["format"], "number")


class WorkspaceDesarmDepletedTests(TestCase):
    """WGT_KPI_DESARM_DEPLETED — vehículos agotados, aislamiento por tenant."""

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def _make_vehiculo(self, empresa, estado):
        from taller.tests.factories import VehiculoDesarmeFactory
        return VehiculoDesarmeFactory(empresa=empresa, estado_desarme=estado)

    def _resolve_desarm(self, empresa):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        ws_def = get_workspace_def("MIXED")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        return {w["key"]: w["value"] for w in result["widgets"]}

    def test_zero_when_no_vehicles(self):
        empresa = self._make_empresa()
        widgets = self._resolve_desarm(empresa)
        self.assertEqual(widgets[WGT_KPI_DESARM_DEPLETED], 0)

    def test_counts_agotado_state(self):
        empresa = self._make_empresa()
        self._make_vehiculo(empresa, "AGOTADO")
        self._make_vehiculo(empresa, "AGOTADO")
        widgets = self._resolve_desarm(empresa)
        self.assertEqual(widgets[WGT_KPI_DESARM_DEPLETED], 2)

    def test_excludes_non_agotado_states(self):
        empresa = self._make_empresa()
        for estado in ["INGRESADO", "DESARMANDO", "DESARMADO", "RECUPERADO", "CERRADO", "BAJA"]:
            self._make_vehiculo(empresa, estado)
        widgets = self._resolve_desarm(empresa)
        self.assertEqual(widgets[WGT_KPI_DESARM_DEPLETED], 0)

    def test_excludes_placeholders(self):
        empresa = self._make_empresa()
        from taller.tests.factories import VehiculoDesarmeFactory
        VehiculoDesarmeFactory(empresa=empresa, estado_desarme="AGOTADO", es_placeholder=True)
        VehiculoDesarmeFactory(empresa=empresa, estado_desarme="AGOTADO", es_placeholder=False)
        widgets = self._resolve_desarm(empresa)
        self.assertEqual(widgets[WGT_KPI_DESARM_DEPLETED], 1)

    def test_tenant_isolation(self):
        empresa_a = self._make_empresa()
        empresa_b = self._make_empresa()
        self._make_vehiculo(empresa_b, "AGOTADO")
        self._make_vehiculo(empresa_b, "AGOTADO")
        self._make_vehiculo(empresa_a, "AGOTADO")
        widgets = self._resolve_desarm(empresa_a)
        self.assertEqual(widgets[WGT_KPI_DESARM_DEPLETED], 1)

    def test_avail_and_depleted_independent(self):
        empresa = self._make_empresa()
        self._make_vehiculo(empresa, "INGRESADO")
        self._make_vehiculo(empresa, "DESARMANDO")
        self._make_vehiculo(empresa, "AGOTADO")
        widgets = self._resolve_desarm(empresa)
        self.assertEqual(widgets[WGT_KPI_DESARM_AVAIL], 2)
        self.assertEqual(widgets[WGT_KPI_DESARM_DEPLETED], 1)


class WorkspacePartsSoldTodayTests(TestCase):
    """WGT_KPI_PARTS_SOLD_TODAY — Sum(LineaRepuesto.cantidad) para ventas del día."""

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def _resolve_parts_sold(self, empresa, today=None):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        ws_def = get_workspace_def("MIXED")
        result = WorkspaceDashboardService.resolve(ws_def, empresa, today=today)
        return next(w["value"] for w in result["widgets"] if w["key"] == WGT_KPI_PARTS_SOLD_TODAY)

    def _make_linea(self, empresa, tipo="PTS", estado="EMITIDO", fecha=None, cantidad=1):
        from datetime import date
        from taller.tests.factories import DocumentoFactory, LineaRepuestoFactory
        today = fecha or date.today()
        doc = DocumentoFactory(empresa=empresa, tipo=tipo, estado=estado, fecha_emision=today)
        return LineaRepuestoFactory(documento=doc, cantidad=cantidad)

    def test_zero_when_no_sales(self):
        empresa = self._make_empresa()
        self.assertEqual(self._resolve_parts_sold(empresa), 0)

    def test_sums_cantidad_from_pts(self):
        empresa = self._make_empresa()
        self._make_linea(empresa, tipo="PTS", cantidad=3)
        self._make_linea(empresa, tipo="PTS", cantidad=5)
        self.assertEqual(self._resolve_parts_sold(empresa), 8)

    def test_includes_ot_and_fac(self):
        empresa = self._make_empresa()
        self._make_linea(empresa, tipo="OT",  cantidad=2)
        self._make_linea(empresa, tipo="FAC", cantidad=4)
        self.assertEqual(self._resolve_parts_sold(empresa), 6)

    def test_excludes_pres(self):
        empresa = self._make_empresa()
        self._make_linea(empresa, tipo="PRES", cantidad=10)
        self.assertEqual(self._resolve_parts_sold(empresa), 0)

    def test_excludes_anulado(self):
        empresa = self._make_empresa()
        self._make_linea(empresa, tipo="PTS", estado="ANULADO", cantidad=10)
        self.assertEqual(self._resolve_parts_sold(empresa), 0)

    def test_excludes_borrador(self):
        empresa = self._make_empresa()
        self._make_linea(empresa, tipo="PTS", estado="BORRADOR", cantidad=10)
        self.assertEqual(self._resolve_parts_sold(empresa), 0)

    def test_excludes_other_dates(self):
        from datetime import date, timedelta
        empresa = self._make_empresa()
        yesterday = date.today() - timedelta(days=1)
        self._make_linea(empresa, tipo="PTS", cantidad=10, fecha=yesterday)
        self.assertEqual(self._resolve_parts_sold(empresa), 0)

    def test_tenant_isolation(self):
        empresa_a = self._make_empresa()
        empresa_b = self._make_empresa()
        self._make_linea(empresa_b, tipo="PTS", cantidad=10)
        self._make_linea(empresa_a, tipo="PTS", cantidad=3)
        self.assertEqual(self._resolve_parts_sold(empresa_a), 3)


class WorkspacePartsCountTests(TestCase):
    """WGT_KPI_PARTS_COUNT — total de Repuesto en inventario."""

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def _resolve_parts_count(self, empresa):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        ws_def = get_workspace_def("MIXED")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        return next(w["value"] for w in result["widgets"] if w["key"] == WGT_KPI_PARTS_COUNT)

    def test_zero_when_no_parts(self):
        empresa = self._make_empresa()
        self.assertEqual(self._resolve_parts_count(empresa), 0)

    def test_counts_all_repuestos(self):
        from taller.tests.factories import RepuestoFactory
        empresa = self._make_empresa()
        RepuestoFactory(empresa=empresa)
        RepuestoFactory(empresa=empresa)
        RepuestoFactory(empresa=empresa)
        self.assertEqual(self._resolve_parts_count(empresa), 3)

    def test_tenant_isolation(self):
        from taller.tests.factories import RepuestoFactory
        empresa_a = self._make_empresa()
        empresa_b = self._make_empresa()
        RepuestoFactory(empresa=empresa_b)
        RepuestoFactory(empresa=empresa_b)
        RepuestoFactory(empresa=empresa_a)
        self.assertEqual(self._resolve_parts_count(empresa_a), 1)


class WorkspaceActivityFeedTests(TestCase):
    """activity_feed — últimos 5 documentos EMITIDO, sin N+1, con aislamiento."""

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def _resolve_feed(self, empresa, rubro="WORKSHOP"):
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        ws_def = get_workspace_def(rubro)
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        return result["activity_feed"]

    def _make_doc(self, empresa, tipo="OT", estado="EMITIDO"):
        from taller.tests.factories import DocumentoFactory
        return DocumentoFactory(empresa=empresa, tipo=tipo, estado=estado)

    def test_feed_present_in_result(self):
        empresa = self._make_empresa()
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        ws_def = get_workspace_def("WORKSHOP")
        result = WorkspaceDashboardService.resolve(ws_def, empresa)
        self.assertIn("activity_feed", result)
        self.assertIsInstance(result["activity_feed"], list)

    def test_empty_when_no_documents(self):
        empresa = self._make_empresa()
        feed = self._resolve_feed(empresa)
        self.assertEqual(feed, [])

    def test_excludes_borrador(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, estado="BORRADOR")
        feed = self._resolve_feed(empresa)
        self.assertEqual(feed, [])

    def test_excludes_anulado(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, estado="ANULADO")
        feed = self._resolve_feed(empresa)
        self.assertEqual(feed, [])

    def test_includes_emitido(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, estado="EMITIDO")
        feed = self._resolve_feed(empresa)
        self.assertEqual(len(feed), 1)

    def test_feed_items_have_required_keys(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, estado="EMITIDO")
        feed = self._resolve_feed(empresa)
        item = feed[0]
        for key in ("numero", "tipo", "tipo_label", "total", "cliente_nombre", "fecha"):
            self.assertIn(key, item, f"Missing key: {key}")

    def test_capped_at_five(self):
        empresa = self._make_empresa()
        for _ in range(8):
            self._make_doc(empresa, estado="EMITIDO")
        feed = self._resolve_feed(empresa)
        self.assertLessEqual(len(feed), 5)

    def test_tenant_isolation(self):
        empresa_a = self._make_empresa()
        empresa_b = self._make_empresa()
        for _ in range(3):
            self._make_doc(empresa_b, estado="EMITIDO")
        self._make_doc(empresa_a, estado="EMITIDO")
        feed = self._resolve_feed(empresa_a)
        self.assertEqual(len(feed), 1)

    def test_feed_present_for_desarm(self):
        empresa = self._make_empresa()
        self._make_doc(empresa, tipo="PTS", estado="EMITIDO")
        feed = self._resolve_feed(empresa, rubro="MIXED")
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0]["tipo"], "PTS")
        self.assertEqual(feed[0]["tipo_label"], "Venta Repuestos")


# ---------------------------------------------------------------------------
# Fase 5: KPI card URLs for DESARMADURIA
# ---------------------------------------------------------------------------

class WorkspaceDesarmWidgetUrlTests(TestCase):
    """
    _inject_desarm_widget_urls wires the correct filtered URL into each
    DESARMADURIA KPI widget so cards are clickable and land on the right list.
    """

    def setUp(self):
        from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory
        self.empresa = EmpresaFactory()
        ConfiguracionEmpresaFactory(empresa=self.empresa, rubro_principal="DESARMADURIA")
        self.config = self.empresa.config

    def _get_urls(self, prefix="/cl/es", ns="documentos_cl_es"):
        import datetime
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        from taller.services.workspace_service import WorkspaceService
        from taller.views.workspace_dashboard import _inject_desarm_widget_urls

        ws_def = WorkspaceService.get_workspace_def(self.config)
        today = datetime.date.today()
        widgets = [{"key": k, "url": None} for k in ws_def.widget_keys]
        _inject_desarm_widget_urls(widgets, prefix, ns, today)
        return {w["key"]: w["url"] for w in widgets}

    def test_all_four_desarm_widgets_get_url(self):
        urls = self._get_urls()
        for key in (
            WGT_KPI_DESARM_AVAIL,
            WGT_KPI_DESARM_DEPLETED,
            WGT_KPI_PARTS_SOLD_TODAY,
            WGT_KPI_PARTS_COUNT,
        ):
            self.assertIsNotNone(urls.get(key), f"{key} should have a URL")

    def test_avail_url_contains_ingresado_and_desarmando(self):
        url = self._get_urls()[WGT_KPI_DESARM_AVAIL]
        self.assertIn("INGRESADO", url)
        self.assertIn("DESARMANDO", url)

    def test_depleted_url_filters_agotado_only(self):
        url = self._get_urls()[WGT_KPI_DESARM_DEPLETED]
        self.assertIn("AGOTADO", url)
        self.assertNotIn("INGRESADO", url)

    def test_parts_sold_today_url_has_emitido_and_todays_date(self):
        import datetime
        today = datetime.date.today()
        url = self._get_urls()[WGT_KPI_PARTS_SOLD_TODAY]
        self.assertIn("EMITIDO", url)
        self.assertIn(today.isoformat(), url)

    def test_parts_count_url_points_to_repuestos(self):
        url = self._get_urls()[WGT_KPI_PARTS_COUNT]
        self.assertIn("repuesto", url.lower())

    def test_cl_prefix_produces_cl_paths(self):
        urls = self._get_urls(prefix="/cl/es", ns="documentos_cl_es")
        self.assertTrue(urls[WGT_KPI_DESARM_AVAIL].startswith("/cl/"))
        self.assertTrue(urls[WGT_KPI_PARTS_SOLD_TODAY].startswith("/cl/"))

    def test_us_prefix_produces_us_paths(self):
        urls = self._get_urls(prefix="/us/en", ns="documentos_us_en")
        self.assertTrue(urls[WGT_KPI_DESARM_AVAIL].startswith("/us/"))
        self.assertTrue(urls[WGT_KPI_PARTS_SOLD_TODAY].startswith("/us/"))


# ---------------------------------------------------------------------------
# Fase 4: WorkspaceAlertsService — DESARMADURIA only
# ---------------------------------------------------------------------------

class WorkspaceAlertsQueryCountTests(TestCase):
    """Service contract: 0 queries for non-DESARM, 2 for DESARM."""

    def _make_empresa(self, rubro="WORKSHOP"):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def test_zero_queries_for_taller(self):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        ws_def = get_workspace_def("WORKSHOP")
        with self.assertNumQueries(0):
            result = WorkspaceAlertsService.resolve(ws_def, empresa)
        self.assertEqual(result, [])

    def test_zero_queries_for_casa_repuestos(self):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        ws_def = get_workspace_def("PARTS")
        with self.assertNumQueries(0):
            result = WorkspaceAlertsService.resolve(ws_def, empresa)
        self.assertEqual(result, [])

    def test_zero_queries_for_carwash(self):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        ws_def = get_workspace_def("DETAILING")
        with self.assertNumQueries(0):
            result = WorkspaceAlertsService.resolve(ws_def, empresa)
        self.assertEqual(result, [])

    def test_exactly_two_queries_for_desarmaduria(self):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")
        with self.assertNumQueries(2):
            WorkspaceAlertsService.resolve(ws_def, empresa)

    def test_empty_result_when_no_issues(self):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")
        result = WorkspaceAlertsService.resolve(ws_def, empresa)
        self.assertEqual(result, [])


class WorkspaceAlertsDelayedTests(TestCase):
    """alrt_desarm_delayed: vehicles stuck > DELAYED_DAYS with no progress."""

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def _make_vehiculo(self, empresa, **kwargs):
        from taller.tests.factories import VehiculoDesarmeFactory
        return VehiculoDesarmeFactory(empresa=empresa, **kwargs)

    def _resolve(self, empresa, today=None):
        from datetime import date
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        ws_def = get_workspace_def("MIXED")
        today = today or date.today()
        return WorkspaceAlertsService.resolve(ws_def, empresa, today=today)

    def _get_alert(self, alerts, key):
        return next((a for a in alerts if a["key"] == key), None)

    def test_no_alert_when_no_delayed_vehicles(self):
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED
        empresa = self._make_empresa()
        alerts = self._resolve(empresa)
        self.assertIsNone(self._get_alert(alerts, ALRT_DESARM_DELAYED))

    def test_alert_when_vehicle_over_threshold(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        cutoff = today - timedelta(days=DELAYED_DAYS)
        old_date = cutoff - timedelta(days=1)
        self._make_vehiculo(
            empresa,
            estado_desarme="INGRESADO",
            fecha_ingreso_desarme=old_date,
            es_placeholder=False,
        )
        alerts = self._resolve(empresa, today=today)
        alert = self._get_alert(alerts, ALRT_DESARM_DELAYED)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["count"], 1)
        self.assertEqual(alert["severity"], "warning")

    def test_no_alert_when_vehicle_exactly_at_threshold(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        cutoff = today - timedelta(days=DELAYED_DAYS)
        self._make_vehiculo(
            empresa,
            estado_desarme="INGRESADO",
            fecha_ingreso_desarme=cutoff,
            es_placeholder=False,
        )
        alerts = self._resolve(empresa, today=today)
        self.assertIsNone(self._get_alert(alerts, ALRT_DESARM_DELAYED))

    def test_excludes_placeholder_vehicles(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        old_date = today - timedelta(days=DELAYED_DAYS + 5)
        self._make_vehiculo(
            empresa,
            estado_desarme="INGRESADO",
            fecha_ingreso_desarme=old_date,
            es_placeholder=True,
        )
        alerts = self._resolve(empresa, today=today)
        self.assertIsNone(self._get_alert(alerts, ALRT_DESARM_DELAYED))

    def test_excludes_vehicles_without_ingreso_date(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        self._make_vehiculo(
            empresa,
            estado_desarme="INGRESADO",
            fecha_ingreso_desarme=None,
            es_placeholder=False,
        )
        alerts = self._resolve(empresa, today=today)
        self.assertIsNone(self._get_alert(alerts, ALRT_DESARM_DELAYED))

    def test_excludes_non_active_estados(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        old_date = today - timedelta(days=DELAYED_DAYS + 5)
        for estado in ["AGOTADO", "DESARMADO", "CERRADO", "BAJA"]:
            self._make_vehiculo(
                empresa,
                estado_desarme=estado,
                fecha_ingreso_desarme=old_date,
                es_placeholder=False,
            )
        alerts = self._resolve(empresa, today=today)
        self.assertIsNone(self._get_alert(alerts, ALRT_DESARM_DELAYED))

    def test_tenant_isolation(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa_a = self._make_empresa()
        empresa_b = self._make_empresa()
        today = date(2026, 6, 1)
        old_date = today - timedelta(days=DELAYED_DAYS + 5)
        self._make_vehiculo(empresa_b, estado_desarme="INGRESADO", fecha_ingreso_desarme=old_date, es_placeholder=False)
        self._make_vehiculo(empresa_b, estado_desarme="INGRESADO", fecha_ingreso_desarme=old_date, es_placeholder=False)
        alerts = self._resolve(empresa_a, today=today)
        self.assertIsNone(self._get_alert(alerts, ALRT_DESARM_DELAYED))

    def test_plural_message_for_multiple_vehicles(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        old_date = today - timedelta(days=DELAYED_DAYS + 1)
        self._make_vehiculo(empresa, estado_desarme="INGRESADO", fecha_ingreso_desarme=old_date, es_placeholder=False)
        self._make_vehiculo(empresa, estado_desarme="DESARMANDO", fecha_ingreso_desarme=old_date, es_placeholder=False)
        alerts = self._resolve(empresa, today=today)
        alert = self._get_alert(alerts, ALRT_DESARM_DELAYED)
        self.assertEqual(alert["count"], 2)
        self.assertIn("vehículos", alert["message"])

    def test_singular_message_for_one_vehicle(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        old_date = today - timedelta(days=DELAYED_DAYS + 1)
        self._make_vehiculo(empresa, estado_desarme="INGRESADO", fecha_ingreso_desarme=old_date, es_placeholder=False)
        alerts = self._resolve(empresa, today=today)
        alert = self._get_alert(alerts, ALRT_DESARM_DELAYED)
        self.assertIn("vehículo", alert["message"])
        self.assertNotIn("vehículos", alert["message"])

    def test_alert_url_contains_ingresado_antes(self):
        from datetime import date, timedelta
        from taller.services.workspace_alerts_service import ALRT_DESARM_DELAYED, DELAYED_DAYS
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        old_date = today - timedelta(days=DELAYED_DAYS + 1)
        self._make_vehiculo(empresa, estado_desarme="INGRESADO", fecha_ingreso_desarme=old_date, es_placeholder=False)
        ws_def = get_workspace_def("MIXED")
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa, prefix="/cl/es", today=today)
        alert = self._get_alert(alerts, ALRT_DESARM_DELAYED)
        self.assertIn("ingresado_antes=", alert["url"])
        self.assertIn("INGRESADO", alert["url"])
        self.assertIn("DESARMANDO", alert["url"])


class WorkspaceAlertsPiezaTests(TestCase):
    """alrt_pieza_no_foto / sin_precio / sin_ubicacion — aggregate counts."""

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def _make_pieza(self, empresa, vehiculo=None, **kwargs):
        from taller.tests.factories import PiezaDesarmeFactory
        return PiezaDesarmeFactory(empresa=empresa, vehiculo_desarme=vehiculo, **kwargs)

    def _resolve(self, empresa):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        ws_def = get_workspace_def("MIXED")
        return WorkspaceAlertsService.resolve(ws_def, empresa)

    def _get_alert(self, alerts, key):
        return next((a for a in alerts if a["key"] == key), None)

    def test_sin_foto_null_imagen(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_FOTO
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=True, imagen=None)
        alerts = self._resolve(empresa)
        alert = self._get_alert(alerts, ALRT_PIEZA_NO_FOTO)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["count"], 1)

    def test_sin_foto_empty_string_imagen(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_FOTO
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=True, imagen="")
        alerts = self._resolve(empresa)
        alert = self._get_alert(alerts, ALRT_PIEZA_NO_FOTO)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["count"], 1)

    def test_sin_precio_both_null(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_PRECIO
        empresa = self._make_empresa()
        self._make_pieza(
            empresa,
            estado_pieza="DISPONIBLE",
            activo=True,
            precio_venta_sugerido=None,
            precio_sugerido=None,
        )
        alerts = self._resolve(empresa)
        alert = self._get_alert(alerts, ALRT_PIEZA_NO_PRECIO)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["count"], 1)

    def test_no_sin_precio_alert_when_precio_venta_set(self):
        from decimal import Decimal
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_PRECIO
        empresa = self._make_empresa()
        self._make_pieza(
            empresa,
            estado_pieza="DISPONIBLE",
            activo=True,
            precio_venta_sugerido=Decimal("15000"),
            precio_sugerido=None,
        )
        alerts = self._resolve(empresa)
        self.assertIsNone(self._get_alert(alerts, ALRT_PIEZA_NO_PRECIO))

    def test_no_sin_precio_alert_when_precio_sugerido_set(self):
        from decimal import Decimal
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_PRECIO
        empresa = self._make_empresa()
        self._make_pieza(
            empresa,
            estado_pieza="DISPONIBLE",
            activo=True,
            precio_venta_sugerido=None,
            precio_sugerido=Decimal("12000"),
        )
        alerts = self._resolve(empresa)
        self.assertIsNone(self._get_alert(alerts, ALRT_PIEZA_NO_PRECIO))

    def test_sin_ubicacion(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_UBICACION
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=True, ubicacion_fisica=None)
        alerts = self._resolve(empresa)
        alert = self._get_alert(alerts, ALRT_PIEZA_NO_UBICACION)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["count"], 1)

    def test_no_sin_ubicacion_when_set(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_UBICACION
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=True, ubicacion_fisica="A1")
        alerts = self._resolve(empresa)
        self.assertIsNone(self._get_alert(alerts, ALRT_PIEZA_NO_UBICACION))

    def test_excludes_vendida_piezas(self):
        from taller.services.workspace_alerts_service import (
            ALRT_PIEZA_NO_FOTO, ALRT_PIEZA_NO_PRECIO, ALRT_PIEZA_NO_UBICACION,
        )
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="VENDIDA", activo=True, imagen=None,
                         precio_venta_sugerido=None, precio_sugerido=None, ubicacion_fisica=None)
        alerts = self._resolve(empresa)
        for key in (ALRT_PIEZA_NO_FOTO, ALRT_PIEZA_NO_PRECIO, ALRT_PIEZA_NO_UBICACION):
            self.assertIsNone(self._get_alert(alerts, key), f"{key} should not fire for VENDIDA")

    def test_excludes_inactive_piezas(self):
        from taller.services.workspace_alerts_service import (
            ALRT_PIEZA_NO_FOTO, ALRT_PIEZA_NO_PRECIO, ALRT_PIEZA_NO_UBICACION,
        )
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=False, imagen=None,
                         precio_venta_sugerido=None, precio_sugerido=None, ubicacion_fisica=None)
        alerts = self._resolve(empresa)
        for key in (ALRT_PIEZA_NO_FOTO, ALRT_PIEZA_NO_PRECIO, ALRT_PIEZA_NO_UBICACION):
            self.assertIsNone(self._get_alert(alerts, key), f"{key} should not fire for inactive")

    def test_tenant_isolation(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_FOTO
        empresa_a = self._make_empresa()
        empresa_b = self._make_empresa()
        self._make_pieza(empresa_b, estado_pieza="DISPONIBLE", activo=True, imagen=None)
        self._make_pieza(empresa_b, estado_pieza="DISPONIBLE", activo=True, imagen=None)
        alerts = self._resolve(empresa_a)
        self.assertIsNone(self._get_alert(alerts, ALRT_PIEZA_NO_FOTO))

    def test_pieza_url_contains_sin_foto_flag(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_FOTO, WorkspaceAlertsService
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=True, imagen=None)
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa, prefix="/cl/es")
        alert = self._get_alert(alerts, ALRT_PIEZA_NO_FOTO)
        self.assertIn("sin_foto=1", alert["url"])
        self.assertIn("/cl/", alert["url"])

    def test_pieza_url_contains_sin_precio_flag(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_PRECIO, WorkspaceAlertsService
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=True,
                         precio_venta_sugerido=None, precio_sugerido=None)
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa, prefix="/cl/es")
        alert = self._get_alert(alerts, ALRT_PIEZA_NO_PRECIO)
        self.assertIn("sin_precio=1", alert["url"])

    def test_pieza_url_contains_sin_ubicacion_flag(self):
        from taller.services.workspace_alerts_service import ALRT_PIEZA_NO_UBICACION, WorkspaceAlertsService
        empresa = self._make_empresa()
        self._make_pieza(empresa, estado_pieza="DISPONIBLE", activo=True, ubicacion_fisica=None)
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa, prefix="/cl/es")
        alert = self._get_alert(alerts, ALRT_PIEZA_NO_UBICACION)
        self.assertIn("sin_ubicacion=1", alert["url"])


class WorkspaceAlertsStructureTests(TestCase):
    """Alert dict keys and values match the contract."""

    def _make_empresa(self):
        from taller.tests.factories import EmpresaFactory
        return EmpresaFactory()

    def _make_pieza_sin_foto(self, empresa):
        from taller.tests.factories import PiezaDesarmeFactory
        return PiezaDesarmeFactory(empresa=empresa, estado_pieza="DISPONIBLE", activo=True, imagen=None)

    def test_alert_has_required_keys(self):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        self._make_pieza_sin_foto(empresa)
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa)
        self.assertTrue(len(alerts) > 0)
        for alert in alerts:
            for key in ("key", "severity", "message", "count", "url", "icon"):
                self.assertIn(key, alert, f"Alert missing required key: {key}")

    def test_only_nonzero_alerts_returned(self):
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa)
        for alert in alerts:
            self.assertGreater(alert["count"], 0)

    def test_severity_values_are_valid(self):
        from taller.tests.factories import PiezaDesarmeFactory
        from taller.services.workspace_alerts_service import WorkspaceAlertsService
        empresa = self._make_empresa()
        PiezaDesarmeFactory(empresa=empresa, estado_pieza="DISPONIBLE", activo=True, imagen=None)
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa)
        for alert in alerts:
            self.assertIn(alert["severity"], ("warning", "info"))

    def test_delayed_alert_severity_is_warning(self):
        from datetime import date, timedelta
        from taller.tests.factories import VehiculoDesarmeFactory
        from taller.services.workspace_alerts_service import (
            ALRT_DESARM_DELAYED, DELAYED_DAYS, WorkspaceAlertsService,
        )
        empresa = self._make_empresa()
        today = date(2026, 6, 1)
        old_date = today - timedelta(days=DELAYED_DAYS + 1)
        VehiculoDesarmeFactory(empresa=empresa, estado_desarme="INGRESADO",
                               fecha_ingreso_desarme=old_date, es_placeholder=False)
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa, today=today)
        alert = next(a for a in alerts if a["key"] == ALRT_DESARM_DELAYED)
        self.assertEqual(alert["severity"], "warning")

    def test_pieza_alerts_severity_is_info(self):
        from taller.tests.factories import PiezaDesarmeFactory
        from taller.services.workspace_alerts_service import (
            ALRT_PIEZA_NO_FOTO, ALRT_PIEZA_NO_PRECIO, ALRT_PIEZA_NO_UBICACION,
            WorkspaceAlertsService,
        )
        empresa = self._make_empresa()
        PiezaDesarmeFactory(empresa=empresa, estado_pieza="DISPONIBLE", activo=True,
                            imagen=None, precio_venta_sugerido=None,
                            precio_sugerido=None, ubicacion_fisica=None)
        ws_def = get_workspace_def("MIXED")
        alerts = WorkspaceAlertsService.resolve(ws_def, empresa)
        pieza_keys = {ALRT_PIEZA_NO_FOTO, ALRT_PIEZA_NO_PRECIO, ALRT_PIEZA_NO_UBICACION}
        for alert in alerts:
            if alert["key"] in pieza_keys:
                self.assertEqual(alert["severity"], "info")


# ===========================================================================
# Workspace AI Briefing tests (Fase IA)
# ===========================================================================

def _make_desarm_context(
    empresa_id=1,
    empresa_nombre="Test Desarme",
    kpi_snapshot=(),
    alert_snapshot=(),
    lang="es",
    today=None,
):
    """Helper: builds a BriefingContext without touching the DB."""
    from datetime import date as _date
    from taller.services.workspace_briefing_service import BriefingContext
    from taller.constants.product_profiles import PRODUCT_DESARMADURIA

    return BriefingContext(
        empresa_id=empresa_id,
        empresa_nombre=empresa_nombre,
        rubro_label="Desarmaduría / Salvage",
        product_key=PRODUCT_DESARMADURIA,
        kpi_snapshot=kpi_snapshot,
        alert_snapshot=alert_snapshot,
        date=today or _date(2026, 8, 4),
        lang=lang,
    )


# ---------------------------------------------------------------------------
# 1. BriefingFallback — deterministic, no DB, no HTTP
# ---------------------------------------------------------------------------

class BriefingFallbackTests(TestCase):

    def test_returns_briefing_result(self):
        from taller.services.workspace_briefing_service import BriefingFallback, BriefingResult
        ctx = _make_desarm_context()
        result = BriefingFallback.generate(ctx)
        self.assertIsInstance(result, BriefingResult)

    def test_source_is_fallback(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        result = BriefingFallback.generate(_make_desarm_context())
        self.assertEqual(result.source, "fallback")

    def test_cached_is_false(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        result = BriefingFallback.generate(_make_desarm_context())
        self.assertFalse(result.cached)

    def test_greeting_is_non_empty(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        result = BriefingFallback.generate(_make_desarm_context())
        self.assertTrue(result.greeting.strip())

    def test_summary_non_empty_tuple(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        result = BriefingFallback.generate(_make_desarm_context())
        self.assertIsInstance(result.summary, tuple)
        self.assertGreater(len(result.summary), 0)

    def test_recommendation_non_empty(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        result = BriefingFallback.generate(_make_desarm_context())
        self.assertTrue(result.recommendation.strip())

    def test_warning_alert_drives_recommendation(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        ctx = _make_desarm_context(alert_snapshot=(
            {"message": "2 vehículos atascados", "count": 2, "severity": "warning"},
        ))
        result = BriefingFallback.generate(ctx)
        self.assertIn("2", result.recommendation)

    def test_info_alert_drives_recommendation_when_no_warning(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        ctx = _make_desarm_context(alert_snapshot=(
            {"message": "3 piezas sin fotografía", "count": 3, "severity": "info"},
        ))
        result = BriefingFallback.generate(ctx)
        self.assertTrue(result.recommendation.strip())

    def test_no_alerts_produces_positive_message(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        ctx = _make_desarm_context(alert_snapshot=())
        result = BriefingFallback.generate(ctx)
        self.assertEqual(len(result.summary), 1)

    def test_en_language(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        ctx = _make_desarm_context(lang="en", alert_snapshot=(
            {"message": "2 stuck vehicles", "count": 2, "severity": "warning"},
        ))
        result = BriefingFallback.generate(ctx)
        self.assertIn("2", result.recommendation)

    def test_summary_capped_at_max(self):
        from taller.services.workspace_briefing_service import BriefingFallback, _MAX_SUMMARY_ITEMS
        ctx = _make_desarm_context(alert_snapshot=tuple(
            {"message": f"alerta {i}", "count": i, "severity": "info"}
            for i in range(1, 10)
        ))
        result = BriefingFallback.generate(ctx)
        self.assertLessEqual(len(result.summary), _MAX_SUMMARY_ITEMS)

    def test_generated_at_is_iso_string(self):
        from taller.services.workspace_briefing_service import BriefingFallback
        result = BriefingFallback.generate(_make_desarm_context())
        from datetime import datetime
        parsed = datetime.fromisoformat(result.generated_at)
        self.assertIsNotNone(parsed)


# ---------------------------------------------------------------------------
# 2. BriefingAIProvider — all HTTP mocked
# ---------------------------------------------------------------------------

class BriefingAIProviderTests(TestCase):

    def _good_response(self, text=None):
        """Returns a mock requests.Response with a valid Anthropic payload."""
        import json as _json
        from unittest.mock import MagicMock
        body = text or _json.dumps({
            "greeting": "Buenos días equipo.",
            "summary": ["2 vehículos atascados.", "3 piezas sin foto."],
            "recommendation": "Atiende los vehículos atascados cuanto antes.",
        })
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "content": [{"type": "text", "text": body}]
        }
        return mock_resp

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_happy_path_returns_briefing_result(self):
        from unittest.mock import patch
        from taller.services.workspace_briefing_service import BriefingAIProvider, BriefingResult
        ctx = _make_desarm_context()
        with patch("taller.services.workspace_briefing_service._requests.post",
                   return_value=self._good_response()):
            result = BriefingAIProvider.call(ctx)
        self.assertIsInstance(result, BriefingResult)
        self.assertEqual(result.source, "ai")
        self.assertFalse(result.cached)

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_greeting_and_summary_populated(self):
        from unittest.mock import patch
        from taller.services.workspace_briefing_service import BriefingAIProvider
        ctx = _make_desarm_context()
        with patch("taller.services.workspace_briefing_service._requests.post",
                   return_value=self._good_response()):
            result = BriefingAIProvider.call(ctx)
        self.assertEqual(result.greeting, "Buenos días equipo.")
        self.assertIn("2 vehículos atascados.", result.summary)

    def test_missing_api_key_raises(self):
        from taller.services.workspace_briefing_service import BriefingAIProvider, BriefingAIError
        with override_settings(ANTHROPIC_API_KEY=""):
            with self.assertRaises(BriefingAIError):
                BriefingAIProvider.call(_make_desarm_context())

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_timeout_raises_briefing_ai_error(self):
        import requests as req
        from unittest.mock import patch
        from taller.services.workspace_briefing_service import BriefingAIProvider, BriefingAIError
        with patch("taller.services.workspace_briefing_service._requests.post",
                   side_effect=req.exceptions.Timeout):
            with self.assertRaises(BriefingAIError):
                BriefingAIProvider.call(_make_desarm_context())

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_http_500_raises_briefing_ai_error(self):
        from unittest.mock import MagicMock, patch
        from taller.services.workspace_briefing_service import BriefingAIProvider, BriefingAIError
        bad = MagicMock()
        bad.ok = False
        bad.status_code = 500
        with patch("taller.services.workspace_briefing_service._requests.post", return_value=bad):
            with self.assertRaises(BriefingAIError):
                BriefingAIProvider.call(_make_desarm_context())

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_invalid_json_raises(self):
        from unittest.mock import MagicMock, patch
        from taller.services.workspace_briefing_service import BriefingAIProvider, BriefingAIError
        bad_json = MagicMock()
        bad_json.ok = True
        bad_json.json.return_value = {"content": [{"type": "text", "text": "not json {{{"}]}
        with patch("taller.services.workspace_briefing_service._requests.post", return_value=bad_json):
            with self.assertRaises(BriefingAIError):
                BriefingAIProvider.call(_make_desarm_context())

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_missing_greeting_raises(self):
        import json as _json
        from unittest.mock import MagicMock, patch
        from taller.services.workspace_briefing_service import BriefingAIProvider, BriefingAIError
        bad_body = _json.dumps({"summary": ["line"], "recommendation": "rec"})
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"content": [{"type": "text", "text": bad_body}]}
        with patch("taller.services.workspace_briefing_service._requests.post", return_value=resp):
            with self.assertRaises(BriefingAIError):
                BriefingAIProvider.call(_make_desarm_context())

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_empty_summary_list_raises(self):
        import json as _json
        from unittest.mock import MagicMock, patch
        from taller.services.workspace_briefing_service import BriefingAIProvider, BriefingAIError
        bad_body = _json.dumps({"greeting": "Hi", "summary": [], "recommendation": "rec"})
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"content": [{"type": "text", "text": bad_body}]}
        with patch("taller.services.workspace_briefing_service._requests.post", return_value=resp):
            with self.assertRaises(BriefingAIError):
                BriefingAIProvider.call(_make_desarm_context())

    @override_settings(ANTHROPIC_API_KEY="test-key-123")
    def test_summary_capped_at_six(self):
        import json as _json
        from unittest.mock import MagicMock, patch
        from taller.services.workspace_briefing_service import BriefingAIProvider
        body = _json.dumps({
            "greeting": "Hi",
            "summary": [f"line {i}" for i in range(10)],
            "recommendation": "Do something.",
        })
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"content": [{"type": "text", "text": body}]}
        with patch("taller.services.workspace_briefing_service._requests.post", return_value=resp):
            result = BriefingAIProvider.call(_make_desarm_context())
        self.assertLessEqual(len(result.summary), 6)


# ---------------------------------------------------------------------------
# 3. WorkspaceBriefingService — cache and budget
# ---------------------------------------------------------------------------

class WorkspaceBriefingServiceCacheTests(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def tearDown(self):
        from django.core.cache import cache
        cache.clear()

    @override_settings(ANTHROPIC_API_KEY="", BRIEFING_CACHE_TTL=300)
    def test_first_call_is_not_cached(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        ctx = _make_desarm_context()
        result = WorkspaceBriefingService.resolve(ctx)
        self.assertFalse(result.cached)

    @override_settings(ANTHROPIC_API_KEY="", BRIEFING_CACHE_TTL=300)
    def test_second_call_is_cached(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        ctx = _make_desarm_context()
        WorkspaceBriefingService.resolve(ctx)
        result2 = WorkspaceBriefingService.resolve(ctx)
        self.assertTrue(result2.cached)

    @override_settings(ANTHROPIC_API_KEY="", BRIEFING_CACHE_TTL=300)
    def test_different_lang_different_cache_entry(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        ctx_es = _make_desarm_context(lang="es")
        ctx_en = _make_desarm_context(lang="en")
        WorkspaceBriefingService.resolve(ctx_es)
        result_en = WorkspaceBriefingService.resolve(ctx_en)
        self.assertFalse(result_en.cached)

    @override_settings(ANTHROPIC_API_KEY="", BRIEFING_CACHE_TTL=300)
    def test_different_empresa_different_cache_entry(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        ctx1 = _make_desarm_context(empresa_id=1)
        ctx2 = _make_desarm_context(empresa_id=2)
        WorkspaceBriefingService.resolve(ctx1)
        result2 = WorkspaceBriefingService.resolve(ctx2)
        self.assertFalse(result2.cached)

    @override_settings(ANTHROPIC_API_KEY="", BRIEFING_CACHE_TTL=300)
    def test_fallback_result_is_also_cached(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        ctx = _make_desarm_context()
        r1 = WorkspaceBriefingService.resolve(ctx)
        self.assertEqual(r1.source, "fallback")
        r2 = WorkspaceBriefingService.resolve(ctx)
        self.assertTrue(r2.cached)
        self.assertEqual(r2.source, "fallback")


class WorkspaceBriefingServiceBudgetTests(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def tearDown(self):
        from django.core.cache import cache
        cache.clear()

    @override_settings(ANTHROPIC_API_KEY="test-key", BRIEFING_DAILY_LIMIT=2)
    def test_budget_exhausted_uses_fallback(self):
        import json as _json
        from unittest.mock import MagicMock, patch
        from taller.services.workspace_briefing_service import (
            WorkspaceBriefingService, _budget_key,
        )
        from django.core.cache import cache
        from datetime import date

        ctx = _make_desarm_context(empresa_id=77)
        # Manually set budget to the limit
        cache.set(_budget_key(77, date(2026, 8, 4)), 2, 86400)

        good_body = _json.dumps({
            "greeting": "Hola",
            "summary": ["línea 1"],
            "recommendation": "Recomendación.",
        })
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"content": [{"type": "text", "text": good_body}]}

        with patch("taller.services.workspace_briefing_service._requests.post", return_value=resp) as mock_post:
            result = WorkspaceBriefingService.resolve(ctx)
            mock_post.assert_not_called()

        self.assertEqual(result.source, "fallback")

    @override_settings(ANTHROPIC_API_KEY="test-key", BRIEFING_DAILY_LIMIT=5, BRIEFING_CACHE_TTL=1)
    def test_budget_incremented_on_successful_ai_call(self):
        import json as _json
        from unittest.mock import MagicMock, patch
        from taller.services.workspace_briefing_service import (
            WorkspaceBriefingService, _budget_key,
        )
        from django.core.cache import cache
        from datetime import date

        ctx = _make_desarm_context(empresa_id=88)
        good_body = _json.dumps({
            "greeting": "Buenos días",
            "summary": ["Línea 1"],
            "recommendation": "Recomendación.",
        })
        resp = MagicMock()
        resp.ok = True
        resp.json.return_value = {"content": [{"type": "text", "text": good_body}]}

        with patch("taller.services.workspace_briefing_service._requests.post", return_value=resp):
            result = WorkspaceBriefingService.resolve(ctx)

        self.assertEqual(result.source, "ai")
        used = cache.get(_budget_key(88, date(2026, 8, 4)), 0)
        self.assertEqual(used, 1)


# ---------------------------------------------------------------------------
# 4. DESARMADURIA exclusivity
# ---------------------------------------------------------------------------

class WorkspaceBriefingDesarmaduriOnlyTests(TestCase):

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def tearDown(self):
        from django.core.cache import cache
        cache.clear()

    def _non_desarm_context(self, product_key):
        from datetime import date
        from taller.services.workspace_briefing_service import BriefingContext
        return BriefingContext(
            empresa_id=1,
            empresa_nombre="Test",
            rubro_label="Taller",
            product_key=product_key,
            kpi_snapshot=(),
            alert_snapshot=(),
            date=date(2026, 8, 4),
            lang="es",
        )

    def test_taller_returns_fallback_immediately(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        from taller.constants.product_profiles import PRODUCT_TALLER
        result = WorkspaceBriefingService.resolve(self._non_desarm_context(PRODUCT_TALLER))
        self.assertEqual(result.source, "fallback")
        self.assertFalse(result.cached)

    def test_carwash_returns_fallback_immediately(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        from taller.constants.product_profiles import PRODUCT_CARWASH
        result = WorkspaceBriefingService.resolve(self._non_desarm_context(PRODUCT_CARWASH))
        self.assertEqual(result.source, "fallback")

    def test_casa_repuestos_returns_fallback_immediately(self):
        from taller.services.workspace_briefing_service import WorkspaceBriefingService
        from taller.constants.product_profiles import PRODUCT_CASA_REPUESTOS
        result = WorkspaceBriefingService.resolve(self._non_desarm_context(PRODUCT_CASA_REPUESTOS))
        self.assertEqual(result.source, "fallback")


# ---------------------------------------------------------------------------
# 5. BriefingContextBuilder — query-level, uses DB
# ---------------------------------------------------------------------------

class BriefingContextBuilderTests(TestCase):

    def _make_empresa(self):
        from taller.tests.factories import ConfiguracionEmpresaFactory, EmpresaFactory
        empresa = EmpresaFactory()
        ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal="DESARMADURIA")
        return empresa

    def test_build_returns_briefing_context(self):
        from taller.services.workspace_briefing_service import BriefingContext, BriefingContextBuilder
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")  # DESARMADURIA
        ctx = BriefingContextBuilder.build(empresa, ws_def, "/cl/es", "es")
        self.assertIsInstance(ctx, BriefingContext)

    def test_product_key_matches_workspace(self):
        from taller.services.workspace_briefing_service import BriefingContextBuilder
        from taller.constants.product_profiles import PRODUCT_DESARMADURIA
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")
        ctx = BriefingContextBuilder.build(empresa, ws_def, "/cl/es", "es")
        self.assertEqual(ctx.product_key, PRODUCT_DESARMADURIA)

    def test_kpi_snapshot_has_no_url_field(self):
        from taller.services.workspace_briefing_service import BriefingContextBuilder
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")
        ctx = BriefingContextBuilder.build(empresa, ws_def, "/cl/es", "es")
        for kpi in ctx.kpi_snapshot:
            self.assertNotIn("url", kpi, "kpi_snapshot must not contain URLs")
            self.assertNotIn("key", kpi, "kpi_snapshot must not contain internal keys")

    def test_alert_snapshot_has_no_url_or_icon(self):
        from taller.services.workspace_briefing_service import BriefingContextBuilder
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")
        ctx = BriefingContextBuilder.build(empresa, ws_def, "/cl/es", "es")
        for a in ctx.alert_snapshot:
            self.assertNotIn("url", a, "alert_snapshot must not contain URLs")
            self.assertNotIn("icon", a, "alert_snapshot must not contain icons")

    def test_empresa_id_is_pk(self):
        from taller.services.workspace_briefing_service import BriefingContextBuilder
        empresa = self._make_empresa()
        ws_def = get_workspace_def("MIXED")
        ctx = BriefingContextBuilder.build(empresa, ws_def, "/cl/es", "es")
        self.assertEqual(ctx.empresa_id, empresa.pk)


# ---------------------------------------------------------------------------
# 6. Privacy tests — prompt never contains PII
# ---------------------------------------------------------------------------

class BriefingPrivacyTests(TestCase):

    def _ctx(self):
        return _make_desarm_context(
            empresa_id=9999,
            empresa_nombre="Desarme Test",
            kpi_snapshot=({"title": "Vehículos disponibles", "value": 5, "format": "number"},),
            alert_snapshot=({"message": "2 vehículos atascados", "count": 2, "severity": "warning"},),
        )

    def test_empresa_id_not_in_prompt(self):
        from taller.services.workspace_briefing_service import BriefingAIProvider
        _, user_prompt = BriefingAIProvider._build_prompt(self._ctx())
        self.assertNotIn("9999", user_prompt)

    def test_no_url_in_user_prompt(self):
        from taller.services.workspace_briefing_service import BriefingAIProvider
        _, user_prompt = BriefingAIProvider._build_prompt(self._ctx())
        self.assertNotIn("http", user_prompt)
        self.assertNotIn("/cl/", user_prompt)
        self.assertNotIn("/es/", user_prompt)

    def test_kpi_snapshot_no_url_key(self):
        ctx = self._ctx()
        for kpi in ctx.kpi_snapshot:
            self.assertNotIn("url", kpi)

    def test_alert_snapshot_no_url_key(self):
        ctx = self._ctx()
        for a in ctx.alert_snapshot:
            self.assertNotIn("url", a)

    def test_alert_snapshot_no_icon_key(self):
        ctx = self._ctx()
        for a in ctx.alert_snapshot:
            self.assertNotIn("icon", a)

    def test_system_prompt_has_no_raw_empresa_id(self):
        from taller.services.workspace_briefing_service import BriefingAIProvider
        system, _ = BriefingAIProvider._build_prompt(self._ctx())
        self.assertNotIn("9999", system)
