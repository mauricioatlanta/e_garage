"""
taller/constants/workspaces.py — Workspace UI 2.0

Declarative workspace definitions for eGarage.

Rules enforced here:
  - No ORM imports.
  - No model references.
  - No conditional logic.
  - No request-time evaluation.
  - Pure data declarations only.

A Workspace declares:
  brand         → visual identity (name key, tagline key, icon, color)
  nav           → ordered navigation slots (module key, terminology key, icon)
  widget_keys   → ordered dashboard widget identifiers
  quick_actions → primary shortcuts (terminology key, icon, URL path suffix)
  theme         → CSS custom-property overrides

Terminology keys follow the schema:
  workspace.<product>.<section>.<item>

These are semantic msgids resolved via Django i18n at request time by
WorkspaceService. They are never shown raw to the user.
"""
from __future__ import annotations

from dataclasses import dataclass
from django.utils.translation import gettext_lazy as _

from taller.constants.business_modules import (
    MOD_CLIENTES,
    MOD_CONFIGURACION,
    MOD_DESARME,
    MOD_DOCUMENTOS,
    MOD_FLOTA,
    MOD_INICIO,
    MOD_REPORTES,
    MOD_REPUESTOS,
    MOD_SERVICIOS,
    MOD_VEHICULOS,
)
from taller.constants.product_profiles import (
    DEFAULT_PRODUCT,
    PRODUCT_CARWASH,
    PRODUCT_CASA_REPUESTOS,
    PRODUCT_DESARMADURIA,
    PRODUCT_TALLER,
    RUBRO_TO_PRODUCT,
)


# ---------------------------------------------------------------------------
# Dataclasses — frozen, immutable, serializable to plain dicts by the service.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkspaceBrand:
    name_key: str     # terminology key → "eGarage Taller"
    tagline_key: str  # terminology key → "Gestión integral de tu taller"
    icon: str         # FontAwesome class, e.g. "fas fa-wrench"
    color_class: str  # CSS token, e.g. "cyan" (matches Tailwind palette)


@dataclass(frozen=True)
class WorkspaceNavDef:
    module_key: str  # MOD_* constant from business_modules
    term_key: str    # terminology key → label shown in sidebar
    icon: str        # FontAwesome class


@dataclass(frozen=True)
class WorkspaceActionDef:
    term_key: str  # terminology key → button label
    icon: str      # FontAwesome class
    path: str      # URL path suffix, e.g. "documentos/form/"


@dataclass(frozen=True)
class WorkspaceDef:
    """Complete declarative workspace for one product experience."""
    product_key: str
    brand: WorkspaceBrand
    nav: tuple[WorkspaceNavDef, ...]
    widget_keys: tuple[str, ...]
    quick_actions: tuple[WorkspaceActionDef, ...]
    theme: dict  # CSS custom property overrides: {"--eg-primary": "#00f5ff"}


# ---------------------------------------------------------------------------
# Widget key constants — stable identifiers for ORM data slots.
# WorkspaceDashboardService maps these to queries; templates only iterate.
# ---------------------------------------------------------------------------

WGT_KPI_DOCS_TODAY      = "kpi_docs_today"       # All docs created today
WGT_KPI_SALES_TODAY     = "kpi_sales_today"       # Total sales value today
WGT_KPI_CLIENTS_MONTH   = "kpi_clients_month"     # New clients this month
WGT_KPI_OT_OPEN         = "kpi_ot_open"           # Open work orders
WGT_KPI_OT_DONE_TODAY   = "kpi_ot_done_today"     # Completed OTs today
WGT_KPI_STOCK_CRITICAL  = "kpi_stock_critical"    # Parts below stock minimum
WGT_KPI_DESARM_AVAIL    = "kpi_desarm_available"  # Dismantlable vehicles
WGT_KPI_INVENTORY_VALUE = "kpi_inventory_value"   # Total inventory value
WGT_KPI_SERVICES_TODAY  = "kpi_services_today"    # Services registered today
WGT_KPI_QUOTES_PENDING  = "kpi_quotes_pending"    # PRES not yet converted or cancelled (PARTS)
WGT_KPI_MARGIN_MONTH    = "kpi_margin_month"      # Gross margin % this month (PARTS, STOCK_BODEGA lines with known cost)


# ---------------------------------------------------------------------------
# Terminology — maps semantic keys to lazy-translated strings.
# The semantic key IS the gettext msgid; translations live in locale/*.po.
# WorkspaceService resolves these to concrete strings at request time.
# ---------------------------------------------------------------------------

TERMINOLOGY: dict[str, object] = {
    # -- Taller: brand --
    "workspace.taller.brand.name":    _("workspace.taller.brand.name"),
    "workspace.taller.brand.tagline": _("workspace.taller.brand.tagline"),
    # -- Taller: nav --
    "workspace.taller.nav.home":      _("workspace.taller.nav.home"),
    "workspace.taller.nav.documents": _("workspace.taller.nav.documents"),
    "workspace.taller.nav.vehicles":  _("workspace.taller.nav.vehicles"),
    "workspace.taller.nav.clients":   _("workspace.taller.nav.clients"),
    "workspace.taller.nav.services":  _("workspace.taller.nav.services"),
    "workspace.taller.nav.parts":     _("workspace.taller.nav.parts"),
    "workspace.taller.nav.fleet":     _("workspace.taller.nav.fleet"),
    "workspace.taller.nav.reports":   _("workspace.taller.nav.reports"),
    "workspace.taller.nav.settings":  _("workspace.taller.nav.settings"),
    # -- Taller: actions --
    "workspace.taller.action.new_document": _("workspace.taller.action.new_document"),
    "workspace.taller.action.new_vehicle":  _("workspace.taller.action.new_vehicle"),
    "workspace.taller.action.new_client":   _("workspace.taller.action.new_client"),

    # -- Desarmaduría: brand --
    "workspace.desarm.brand.name":    _("workspace.desarm.brand.name"),
    "workspace.desarm.brand.tagline": _("workspace.desarm.brand.tagline"),
    # -- Desarmaduría: nav --
    "workspace.desarm.nav.home":      _("workspace.desarm.nav.home"),
    "workspace.desarm.nav.vehicles":  _("workspace.desarm.nav.vehicles"),
    "workspace.desarm.nav.parts":     _("workspace.desarm.nav.parts"),
    "workspace.desarm.nav.documents": _("workspace.desarm.nav.documents"),
    "workspace.desarm.nav.clients":   _("workspace.desarm.nav.clients"),
    "workspace.desarm.nav.reports":   _("workspace.desarm.nav.reports"),
    "workspace.desarm.nav.settings":  _("workspace.desarm.nav.settings"),
    # -- Desarmaduría: actions --
    "workspace.desarm.action.new_vehicle":  _("workspace.desarm.action.new_vehicle"),
    "workspace.desarm.action.new_sale":     _("workspace.desarm.action.new_sale"),
    "workspace.desarm.action.view_inventory": _("workspace.desarm.action.view_inventory"),

    # -- Casa de Repuestos: brand --
    "workspace.parts.brand.name":    _("workspace.parts.brand.name"),
    "workspace.parts.brand.tagline": _("workspace.parts.brand.tagline"),
    # -- Casa de Repuestos: nav --
    "workspace.parts.nav.home":      _("workspace.parts.nav.home"),
    "workspace.parts.nav.parts":     _("workspace.parts.nav.parts"),
    "workspace.parts.nav.documents": _("workspace.parts.nav.documents"),
    "workspace.parts.nav.clients":   _("workspace.parts.nav.clients"),
    "workspace.parts.nav.reports":   _("workspace.parts.nav.reports"),
    "workspace.parts.nav.settings":  _("workspace.parts.nav.settings"),
    # -- Casa de Repuestos: actions --
    "workspace.parts.action.new_sale":        _("workspace.parts.action.new_sale"),
    "workspace.parts.action.new_quote":       _("workspace.parts.action.new_quote"),
    "workspace.parts.action.new_parts_sale":  _("workspace.parts.action.new_parts_sale"),
    "workspace.parts.action.add_part":        _("workspace.parts.action.add_part"),
    "workspace.parts.action.view_inventory":  _("workspace.parts.action.view_inventory"),

    # -- Carwash: brand --
    "workspace.carwash.brand.name":    _("workspace.carwash.brand.name"),
    "workspace.carwash.brand.tagline": _("workspace.carwash.brand.tagline"),
    # -- Carwash: nav --
    "workspace.carwash.nav.home":      _("workspace.carwash.nav.home"),
    "workspace.carwash.nav.documents": _("workspace.carwash.nav.documents"),
    "workspace.carwash.nav.clients":   _("workspace.carwash.nav.clients"),
    "workspace.carwash.nav.services":  _("workspace.carwash.nav.services"),
    "workspace.carwash.nav.reports":   _("workspace.carwash.nav.reports"),
    "workspace.carwash.nav.settings":  _("workspace.carwash.nav.settings"),
    # -- Carwash: actions --
    "workspace.carwash.action.new_service": _("workspace.carwash.action.new_service"),
    "workspace.carwash.action.new_client":  _("workspace.carwash.action.new_client"),
}


# ---------------------------------------------------------------------------
# Workspace definitions — one per product family.
# ---------------------------------------------------------------------------

WORKSPACE_TALLER = WorkspaceDef(
    product_key=PRODUCT_TALLER,
    brand=WorkspaceBrand(
        name_key="workspace.taller.brand.name",
        tagline_key="workspace.taller.brand.tagline",
        icon="fas fa-wrench",
        color_class="cyan",
    ),
    nav=(
        WorkspaceNavDef(MOD_INICIO,        "workspace.taller.nav.home",      "fas fa-home"),
        WorkspaceNavDef(MOD_DOCUMENTOS,    "workspace.taller.nav.documents", "fas fa-file-invoice"),
        WorkspaceNavDef(MOD_VEHICULOS,     "workspace.taller.nav.vehicles",  "fas fa-car"),
        WorkspaceNavDef(MOD_CLIENTES,      "workspace.taller.nav.clients",   "fas fa-users"),
        WorkspaceNavDef(MOD_SERVICIOS,     "workspace.taller.nav.services",  "fas fa-tools"),
        WorkspaceNavDef(MOD_REPUESTOS,     "workspace.taller.nav.parts",     "fas fa-cogs"),
        WorkspaceNavDef(MOD_FLOTA,         "workspace.taller.nav.fleet",     "fas fa-truck"),
        WorkspaceNavDef(MOD_REPORTES,      "workspace.taller.nav.reports",   "fas fa-chart-bar"),
        WorkspaceNavDef(MOD_CONFIGURACION, "workspace.taller.nav.settings",  "fas fa-cog"),
    ),
    widget_keys=(
        WGT_KPI_OT_OPEN,
        WGT_KPI_DOCS_TODAY,
        WGT_KPI_SALES_TODAY,
        WGT_KPI_CLIENTS_MONTH,
    ),
    quick_actions=(
        WorkspaceActionDef("workspace.taller.action.new_document", "fas fa-file-plus",  "documentos/form/"),
        WorkspaceActionDef("workspace.taller.action.new_vehicle",  "fas fa-car",        "vehiculos/crear/"),
        WorkspaceActionDef("workspace.taller.action.new_client",   "fas fa-user-plus",  "clientes/crear/"),
    ),
    theme={"--eg-primary": "#00f5ff", "--eg-accent": "#b026ff"},
)

WORKSPACE_DESARMADURIA = WorkspaceDef(
    product_key=PRODUCT_DESARMADURIA,
    brand=WorkspaceBrand(
        name_key="workspace.desarm.brand.name",
        tagline_key="workspace.desarm.brand.tagline",
        icon="fas fa-car-crash",
        color_class="orange",
    ),
    nav=(
        WorkspaceNavDef(MOD_INICIO,        "workspace.desarm.nav.home",      "fas fa-home"),
        WorkspaceNavDef(MOD_DESARME,       "workspace.desarm.nav.vehicles",  "fas fa-car-crash"),
        WorkspaceNavDef(MOD_REPUESTOS,     "workspace.desarm.nav.parts",     "fas fa-boxes"),
        WorkspaceNavDef(MOD_DOCUMENTOS,    "workspace.desarm.nav.documents", "fas fa-shopping-cart"),
        WorkspaceNavDef(MOD_CLIENTES,      "workspace.desarm.nav.clients",   "fas fa-users"),
        WorkspaceNavDef(MOD_REPORTES,      "workspace.desarm.nav.reports",   "fas fa-chart-bar"),
        WorkspaceNavDef(MOD_CONFIGURACION, "workspace.desarm.nav.settings",  "fas fa-cog"),
    ),
    widget_keys=(
        WGT_KPI_DESARM_AVAIL,
        WGT_KPI_INVENTORY_VALUE,
        WGT_KPI_DOCS_TODAY,
        WGT_KPI_CLIENTS_MONTH,
    ),
    quick_actions=(
        WorkspaceActionDef("workspace.desarm.action.new_vehicle",    "fas fa-plus-circle",   "desarme/crear/"),
        WorkspaceActionDef("workspace.desarm.action.new_sale",       "fas fa-shopping-cart", "documentos/form/"),
        WorkspaceActionDef("workspace.desarm.action.view_inventory", "fas fa-boxes",         "repuestos/"),
    ),
    theme={"--eg-primary": "#fb923c", "--eg-accent": "#f97316"},
)

WORKSPACE_CASA_REPUESTOS = WorkspaceDef(
    product_key=PRODUCT_CASA_REPUESTOS,
    brand=WorkspaceBrand(
        name_key="workspace.parts.brand.name",
        tagline_key="workspace.parts.brand.tagline",
        icon="fas fa-boxes",
        color_class="lime",
    ),
    nav=(
        WorkspaceNavDef(MOD_INICIO,        "workspace.parts.nav.home",      "fas fa-home"),
        WorkspaceNavDef(MOD_REPUESTOS,     "workspace.parts.nav.parts",     "fas fa-boxes"),
        WorkspaceNavDef(MOD_DOCUMENTOS,    "workspace.parts.nav.documents", "fas fa-shopping-cart"),
        WorkspaceNavDef(MOD_CLIENTES,      "workspace.parts.nav.clients",   "fas fa-users"),
        WorkspaceNavDef(MOD_REPORTES,      "workspace.parts.nav.reports",   "fas fa-chart-bar"),
        WorkspaceNavDef(MOD_CONFIGURACION, "workspace.parts.nav.settings",  "fas fa-cog"),
    ),
    widget_keys=(
        WGT_KPI_SALES_TODAY,
        WGT_KPI_MARGIN_MONTH,
        WGT_KPI_STOCK_CRITICAL,
        WGT_KPI_QUOTES_PENDING,
    ),
    quick_actions=(
        WorkspaceActionDef("workspace.parts.action.new_quote",      "fas fa-file-invoice",  "documentos/form/?tipo=PRES"),
        WorkspaceActionDef("workspace.parts.action.new_parts_sale", "fas fa-shopping-cart", "documentos/form/?tipo=PTS"),
        WorkspaceActionDef("workspace.parts.action.add_part",       "fas fa-plus",          "repuestos/nuevo/"),
        WorkspaceActionDef("workspace.parts.action.view_inventory", "fas fa-boxes",         "repuestos/"),
    ),
    theme={"--eg-primary": "#84cc16", "--eg-accent": "#65a30d"},
)

WORKSPACE_CARWASH = WorkspaceDef(
    product_key=PRODUCT_CARWASH,
    brand=WorkspaceBrand(
        name_key="workspace.carwash.brand.name",
        tagline_key="workspace.carwash.brand.tagline",
        icon="fas fa-tint",
        color_class="blue",
    ),
    nav=(
        WorkspaceNavDef(MOD_INICIO,        "workspace.carwash.nav.home",      "fas fa-home"),
        WorkspaceNavDef(MOD_DOCUMENTOS,    "workspace.carwash.nav.documents", "fas fa-cash-register"),
        WorkspaceNavDef(MOD_CLIENTES,      "workspace.carwash.nav.clients",   "fas fa-users"),
        WorkspaceNavDef(MOD_SERVICIOS,     "workspace.carwash.nav.services",  "fas fa-tint"),
        WorkspaceNavDef(MOD_REPORTES,      "workspace.carwash.nav.reports",   "fas fa-chart-bar"),
        WorkspaceNavDef(MOD_CONFIGURACION, "workspace.carwash.nav.settings",  "fas fa-cog"),
    ),
    widget_keys=(
        WGT_KPI_SERVICES_TODAY,
        WGT_KPI_SALES_TODAY,
        WGT_KPI_CLIENTS_MONTH,
        WGT_KPI_DOCS_TODAY,
    ),
    quick_actions=(
        WorkspaceActionDef("workspace.carwash.action.new_service", "fas fa-tint",      "documentos/form/"),
        WorkspaceActionDef("workspace.carwash.action.new_client",  "fas fa-user-plus", "clientes/crear/"),
    ),
    theme={"--eg-primary": "#3b82f6", "--eg-accent": "#1d4ed8"},
)


# ---------------------------------------------------------------------------
# Registry — maps product key to its WorkspaceDef.
# Add a new product here without touching anything else.
# ---------------------------------------------------------------------------

WORKSPACE_DEFINITIONS: dict[str, WorkspaceDef] = {
    PRODUCT_TALLER:         WORKSPACE_TALLER,
    PRODUCT_DESARMADURIA:   WORKSPACE_DESARMADURIA,
    PRODUCT_CASA_REPUESTOS: WORKSPACE_CASA_REPUESTOS,
    PRODUCT_CARWASH:        WORKSPACE_CARWASH,
}


def get_workspace_def(rubro: str | None) -> WorkspaceDef:
    """Returns the WorkspaceDef for a rubro_principal value. Never None."""
    product_key = RUBRO_TO_PRODUCT.get(rubro or "WORKSHOP", DEFAULT_PRODUCT)
    return WORKSPACE_DEFINITIONS[product_key]
