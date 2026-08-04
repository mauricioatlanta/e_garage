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
    WGT_KPI_DOCS_TODAY,
    WGT_KPI_INVENTORY_VALUE,
    WGT_KPI_OT_OPEN,
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
        self.assertIn(WGT_KPI_INVENTORY_VALUE, ws.widget_keys)

    def test_desarm_has_no_ot_open_widget(self):
        ws = get_workspace_def("MIXED")
        self.assertNotIn(WGT_KPI_OT_OPEN, ws.widget_keys)

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

    def test_desarm_still_includes_docs_today(self):
        ws = get_workspace_def("MIXED")
        self.assertIn(WGT_KPI_DOCS_TODAY, ws.widget_keys)

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
        # TALLER: GROUP_DOCS + GROUP_CLIENTS = 2 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("WORKSHOP")
        ws_def = get_workspace_def("WORKSHOP")
        with self.assertNumQueries(2):
            result = WorkspaceDashboardService.resolve(ws_def, empresa)
        self.assertIn("widgets", result)
        self.assertIn("date", result)

    def test_desarm_dashboard_query_count(self):
        # DESARM: GROUP_DOCS + GROUP_CLIENTS + GROUP_INVENTORY + GROUP_DESARM = 4 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("MIXED")
        ws_def = get_workspace_def("MIXED")
        with self.assertNumQueries(4):
            WorkspaceDashboardService.resolve(ws_def, empresa)

    def test_parts_dashboard_query_count(self):
        # PARTS: GROUP_DOCS + GROUP_CLIENTS + GROUP_INVENTORY = 3 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("PARTS")
        ws_def = get_workspace_def("PARTS")
        with self.assertNumQueries(3):
            WorkspaceDashboardService.resolve(ws_def, empresa)

    def test_carwash_dashboard_query_count(self):
        # CARWASH: GROUP_DOCS + GROUP_CLIENTS = 2 queries
        from taller.services.workspace_dashboard_service import WorkspaceDashboardService
        empresa = self._make_empresa("DETAILING")
        ws_def = get_workspace_def("DETAILING")
        with self.assertNumQueries(2):
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


class WorkspaceThemeRenderTests(TestCase):
    """Render tests: workspace.theme CSS vars appear in HTML output of layouts/app.html.

    Uses /us/en/dashboard/ because that URL maps directly to workspace_dashboard
    (which renders dashboard/index.html → extends layouts/app.html).
    The /cl/es/dashboard/ path is a redirect dispatcher to centro-operaciones.
    """

    _DASH = "/us/en/dashboard/"

    def _make_empresa(self, rubro):
        from taller.tests.factories import EmpresaFactory, ConfiguracionEmpresaFactory
        empresa = EmpresaFactory(pais="US")
        ConfiguracionEmpresaFactory(empresa=empresa, rubro_principal=rubro)
        return empresa

    def test_parts_theme_vars_in_dashboard_html(self):
        from django.test import Client
        empresa = self._make_empresa("PARTS")
        c = Client()
        c.force_login(empresa.user)
        response = c.get(self._DASH)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("--eg-primary", content)
        self.assertIn("#84cc16", content)  # PARTS lime primary

    def test_desarmaduria_theme_vars_in_dashboard_html(self):
        from django.test import Client
        empresa = self._make_empresa("DESARMADURIA")
        c = Client()
        c.force_login(empresa.user)
        response = c.get(self._DASH)
        self.assertEqual(response.status_code, 200)
        self.assertIn("#fb923c", response.content.decode())  # DESARMADURIA orange primary

    def test_workshop_theme_vars_in_dashboard_html(self):
        from django.test import Client
        empresa = self._make_empresa("WORKSHOP")
        c = Client()
        c.force_login(empresa.user)
        response = c.get(self._DASH)
        self.assertEqual(response.status_code, 200)
        self.assertIn("#00f5ff", response.content.decode())  # TALLER cyan primary

    def test_user_without_config_no_crash(self):
        from django.test import Client
        from taller.tests.factories import EmpresaFactory
        empresa = EmpresaFactory(pais="US")  # no config
        c = Client()
        c.force_login(empresa.user)
        response = c.get(self._DASH)
        self.assertIn(response.status_code, [200, 302])

    def test_anonymous_request_redirects_no_crash(self):
        from django.test import Client
        c = Client()
        response = c.get(self._DASH)
        self.assertEqual(response.status_code, 302)
