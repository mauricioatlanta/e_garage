from django.utils.translation import gettext_lazy as _
"""
Business module definitions for eGarage.

Maps rubros to active navigation items and feature capabilities.
Each MOD_* constant is a stable key used across the service,
context processor, and templates.
"""

MOD_INICIO = "inicio"
MOD_CLIENTES = "clientes"
MOD_VEHICULOS = "vehiculos"
MOD_DOCUMENTOS = "documentos"
MOD_REPUESTOS = "repuestos"
MOD_SERVICIOS = "servicios"
MOD_DESARME = "desarme"
MOD_RECICLAJE = "reciclaje"
MOD_FLOTA = "flota"
MOD_REPORTES = "reportes"
MOD_CONFIGURACION = "configuracion"
MOD_GRUAS = "gruas"

# Navigation item definitions: label, URL path suffix, icon CSS class, display order.
# Labels/icons here are defaults; product profiles may override them per rubro.
NAV_ITEMS = {
    MOD_INICIO:        {"label": "Inicio",        "path": "dashboard/",       "icon": "fas fa-home",         "order": 1},
    MOD_CLIENTES:      {"label": _("Clientes"),      "path": "clientes/",        "icon": "fas fa-users",        "order": 2},
    MOD_VEHICULOS:     {"label": _("Vehículos"),     "path": "vehiculos/",       "icon": "fas fa-car",          "order": 3},
    MOD_DOCUMENTOS:    {"label": "Documentos",    "path": "documentos/form/", "icon": "fas fa-file-invoice", "order": 4},
    MOD_REPUESTOS:     {"label": _("Repuestos"),     "path": "repuestos/",       "icon": "fas fa-cogs",         "order": 5},
    MOD_SERVICIOS:     {"label": _("Servicios"),     "path": "servicios/",       "icon": "fas fa-tools",        "order": 6},
    MOD_DESARME:       {"label": "Desarme",       "path": "desarme/",         "icon": "fas fa-car-crash",    "order": 7},
    MOD_RECICLAJE:     {"label": "Reciclaje",     "path": "reciclaje/",       "icon": "fas fa-recycle",      "order": 10},
    MOD_FLOTA:         {"label": "Flota",         "path": "flota/",           "icon": "fas fa-truck",        "order": 8},
    MOD_REPORTES:      {"label": _("Reportes"),      "path": "reportes/",        "icon": "fas fa-chart-bar",    "order": 9},
    MOD_CONFIGURACION: {"label": "Configuración", "path": "settings/",        "icon": "fas fa-cog",          "order": 99},
    MOD_GRUAS:         {"label": "Grúas",         "path": "gruas/",           "icon": "fas fa-truck-pickup",  "order": 6},
}

# Always shown regardless of rubro
ALWAYS_ON = frozenset({MOD_INICIO, MOD_CLIENTES, MOD_DOCUMENTOS, MOD_REPORTES, MOD_CONFIGURACION})

# Path fragments used to detect the active nav item from request.path
PATH_HINTS = {
    MOD_INICIO:        "/dashboard",
    MOD_CLIENTES:      "/clientes",
    MOD_VEHICULOS:     "/vehiculos",
    MOD_DOCUMENTOS:    "/documentos",
    MOD_REPUESTOS:     "/repuestos",
    MOD_SERVICIOS:     "/servicios",
    MOD_DESARME:       "/desarme",
    MOD_RECICLAJE:     "/reciclaje",
    MOD_FLOTA:         "/flota",
    MOD_REPORTES:      "/reportes",
    MOD_CONFIGURACION: "/settings",
    MOD_GRUAS:         "/gruas",
}

# Modules unlocked per rubro (added to ALWAYS_ON)
MODULES_BY_RUBRO = {
    "WORKSHOP":            frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS, MOD_FLOTA}),
    "WORKSHOP_MOTO":       frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "WORKSHOP_HEAVY":      frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "BODYSHOP":            frozenset({MOD_VEHICULOS, MOD_SERVICIOS}),
    "GLASS":               frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "ELECTRIC":            frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "FLEET":               frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS, MOD_FLOTA}),
    "DESARMADURIA":        frozenset({MOD_DESARME, MOD_REPUESTOS}),
    "PARTS":               frozenset({MOD_REPUESTOS}),
    "TIRE":                frozenset({MOD_REPUESTOS, MOD_SERVICIOS}),  # Vulcanizacion: sin Vehiculos, sin Desarme, sin Flota
    "DETAILING":           frozenset({MOD_VEHICULOS, MOD_SERVICIOS}),
    "CARWASH":             frozenset({MOD_VEHICULOS, MOD_SERVICIOS}),  # Carwash: alias de DETAILING, igual módulos
    "RECYCLING":           frozenset({MOD_RECICLAJE}),
    "RECICLAJE":           frozenset({MOD_RECICLAJE}),  # Reciclaje: alias de RECYCLING
    "TOWING":              frozenset({MOD_GRUAS, MOD_CLIENTES, MOD_REPORTES}),
    "GRUAS":               frozenset({MOD_GRUAS, MOD_CLIENTES, MOD_REPORTES}),  # Grúas: alias de TOWING
    "MIXED":               frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS, MOD_DESARME}),
}
