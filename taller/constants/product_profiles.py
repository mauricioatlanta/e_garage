"""
Product profiles — groups rubros into named product experiences.

Each profile defines:
  - nav: ordered list of {key, label, icon} for the sidebar; labels/icons
    override the generic defaults in business_modules.NAV_ITEMS.
  - kpi_labels: ordered list of KPI titles for the dashboard header.
  - quick_access: shortcut actions for the dashboard home.

No database columns are touched; profiles are derived purely from
ConfiguracionEmpresa.rubro_principal at request time.
"""

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

PRODUCT_TALLER         = "TALLER"
PRODUCT_DESARMADURIA   = "DESARMADURIA"
PRODUCT_CASA_REPUESTOS = "CASA_REPUESTOS"
PRODUCT_CARWASH        = "CARWASH"

# Maps every rubro_principal value to a product family.
RUBRO_TO_PRODUCT = {
    "WORKSHOP":            PRODUCT_TALLER,
    "WORKSHOP_MOTO":       PRODUCT_TALLER,
    "WORKSHOP_HEAVY":      PRODUCT_TALLER,
    "EXHAUST":             PRODUCT_TALLER,
    "BODYSHOP":            PRODUCT_TALLER,
    "ELECTRIC":            PRODUCT_TALLER,
    "GLASS_AUDIO":         PRODUCT_TALLER,
    "SUSPENSION_STEERING": PRODUCT_TALLER,
    "BRAKES":              PRODUCT_TALLER,
    "OBD_DIAGNOSTIC":      PRODUCT_TALLER,
    "CLASSIC_CARS":        PRODUCT_TALLER,
    "AUDIO_ENTERTAINMENT": PRODUCT_TALLER,
    "GAS_CONVERSION":      PRODUCT_TALLER,
    "BODY_GLASS":          PRODUCT_TALLER,
    "TUNING":              PRODUCT_TALLER,
    "FLEET":               PRODUCT_TALLER,
    "FLEET_REPAIR":        PRODUCT_TALLER,
    "MIXED":               PRODUCT_DESARMADURIA,
    "PARTS":               PRODUCT_CASA_REPUESTOS,
    "TIRE":                PRODUCT_CASA_REPUESTOS,
    "DETAILING":           PRODUCT_CARWASH,
}

PRODUCT_PROFILES = {
    PRODUCT_TALLER: {
        "name":          "eGarage Taller",
        "tagline":       "Gestión integral de tu taller",
        "icon":          "fas fa-wrench",
        "color_class":   "cyan",
        "default_rubro": "WORKSHOP",
        "nav": [
            {"key": MOD_INICIO,        "label": "Inicio",          "icon": "fas fa-home"},
            {"key": MOD_DOCUMENTOS,    "label": "Presupuestos/OT", "icon": "fas fa-file-invoice"},
            {"key": MOD_VEHICULOS,     "label": "Vehículos",       "icon": "fas fa-car"},
            {"key": MOD_CLIENTES,      "label": "Clientes",        "icon": "fas fa-users"},
            {"key": MOD_SERVICIOS,     "label": "Servicios",       "icon": "fas fa-tools"},
            {"key": MOD_REPUESTOS,     "label": "Repuestos",       "icon": "fas fa-cogs"},
            {"key": MOD_FLOTA,         "label": "Flota",           "icon": "fas fa-truck"},
            {"key": MOD_REPORTES,      "label": "Reportes",        "icon": "fas fa-chart-bar"},
            {"key": MOD_CONFIGURACION, "label": "Configuración",   "icon": "fas fa-cog"},
        ],
        "kpi_labels": ["OT Abiertas", "OT Terminadas", "Vehículos en espera", "Ventas del día"],
        "quick_access": [
            {"label": "Nueva OT",        "icon": "fas fa-file-plus",  "path": "documentos/form/"},
            {"label": "Nuevo Vehículo",  "icon": "fas fa-car",        "path": "vehiculos/crear/"},
            {"label": "Nuevo Cliente",   "icon": "fas fa-user-plus",  "path": "clientes/crear/"},
        ],
    },

    PRODUCT_DESARMADURIA: {
        "name":          "eGarage Desarmaduría",
        "tagline":       "Control total de tu desarmaduría",
        "icon":          "fas fa-car-crash",
        "color_class":   "orange",
        "default_rubro": "MIXED",
        "nav": [
            {"key": MOD_INICIO,        "label": "Inicio",               "icon": "fas fa-home"},
            {"key": MOD_DESARME,       "label": "Vehículos de Desarme", "icon": "fas fa-car-crash"},
            {"key": MOD_REPUESTOS,     "label": "Inventario",           "icon": "fas fa-boxes"},
            {"key": MOD_DOCUMENTOS,    "label": "Ventas",               "icon": "fas fa-shopping-cart"},
            {"key": MOD_CLIENTES,      "label": "Clientes",             "icon": "fas fa-users"},
            {"key": MOD_REPORTES,      "label": "Reportes",             "icon": "fas fa-chart-bar"},
            {"key": MOD_CONFIGURACION, "label": "Configuración",        "icon": "fas fa-cog"},
        ],
        "kpi_labels": ["Vehículos disponibles", "Valor inventario", "Piezas vendidas hoy", "Vehículos sin movimiento"],
        "quick_access": [
            {"label": "Ingresar Vehículo", "icon": "fas fa-plus-circle",   "path": "desarme/crear/"},
            {"label": "Registrar Venta",   "icon": "fas fa-shopping-cart", "path": "documentos/form/"},
            {"label": "Ver Inventario",    "icon": "fas fa-boxes",         "path": "repuestos/"},
        ],
    },

    PRODUCT_CASA_REPUESTOS: {
        "name":          "eGarage Repuestos",
        "tagline":       "Tu casa de repuestos digitalizada",
        "icon":          "fas fa-boxes",
        "color_class":   "lime",
        "default_rubro": "PARTS",
        "nav": [
            {"key": MOD_INICIO,        "label": "Inicio",        "icon": "fas fa-home"},
            {"key": MOD_REPUESTOS,     "label": "Inventario",    "icon": "fas fa-boxes"},
            {"key": MOD_DOCUMENTOS,    "label": "Ventas",        "icon": "fas fa-shopping-cart"},
            {"key": MOD_CLIENTES,      "label": "Clientes",      "icon": "fas fa-users"},
            {"key": MOD_REPORTES,      "label": "Reportes",      "icon": "fas fa-chart-bar"},
            {"key": MOD_CONFIGURACION, "label": "Configuración", "icon": "fas fa-cog"},
        ],
        "kpi_labels": ["Ventas hoy", "Productos críticos", "Rotación", "Clientes frecuentes"],
        "quick_access": [
            {"label": "Nueva Venta",      "icon": "fas fa-shopping-cart", "path": "documentos/form/"},
            {"label": "Agregar Repuesto", "icon": "fas fa-plus",          "path": "repuestos/nuevo/"},
            {"label": "Ver Inventario",   "icon": "fas fa-boxes",         "path": "repuestos/"},
        ],
    },

    PRODUCT_CARWASH: {
        "name":          "eGarage Carwash",
        "tagline":       "Gestión simple para tu carwash",
        "icon":          "fas fa-tint",
        "color_class":   "blue",
        "default_rubro": "DETAILING",
        "nav": [
            {"key": MOD_INICIO,        "label": "Inicio",        "icon": "fas fa-home"},
            {"key": MOD_DOCUMENTOS,    "label": "Caja",          "icon": "fas fa-cash-register"},
            {"key": MOD_CLIENTES,      "label": "Clientes",      "icon": "fas fa-users"},
            {"key": MOD_SERVICIOS,     "label": "Servicios",     "icon": "fas fa-tint"},
            {"key": MOD_REPORTES,      "label": "Reportes",      "icon": "fas fa-chart-bar"},
            {"key": MOD_CONFIGURACION, "label": "Configuración", "icon": "fas fa-cog"},
        ],
        "kpi_labels": ["Servicios hoy", "Ingresos hoy", "Clientes hoy", "Servicios semana"],
        "quick_access": [
            {"label": "Registrar Servicio", "icon": "fas fa-tint",      "path": "documentos/form/"},
            {"label": "Nuevo Cliente",      "icon": "fas fa-user-plus", "path": "clientes/crear/"},
        ],
    },
}

DEFAULT_PRODUCT = PRODUCT_TALLER
