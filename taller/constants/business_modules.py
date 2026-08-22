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
MOD_FLOTA = "flota"
MOD_REPORTES = "reportes"
MOD_CONFIGURACION = "configuracion"

# Navigation item definitions: label, URL path suffix, icon CSS class, display order.
# Labels/icons here are defaults; product profiles may override them per rubro.
NAV_ITEMS = {
    MOD_INICIO:        {"label": "Inicio",        "path": "dashboard/",       "icon": "fas fa-home",         "order": 1},
    MOD_CLIENTES:      {"label": "Clientes",      "path": "clientes/",        "icon": "fas fa-users",        "order": 2},
    MOD_VEHICULOS:     {"label": "Vehículos",     "path": "vehiculos/",       "icon": "fas fa-car",          "order": 3},
    MOD_DOCUMENTOS:    {"label": "Documentos",    "path": "documentos/form/", "icon": "fas fa-file-invoice", "order": 4},
    MOD_REPUESTOS:     {"label": "Repuestos",     "path": "repuestos/",       "icon": "fas fa-cogs",         "order": 5},
    MOD_SERVICIOS:     {"label": "Servicios",     "path": "servicios/",       "icon": "fas fa-tools",        "order": 6},
    MOD_DESARME:       {"label": "Desarme",       "path": "desarme/",         "icon": "fas fa-car-crash",    "order": 7},
    MOD_FLOTA:         {"label": "Flota",         "path": "flota/",           "icon": "fas fa-truck",        "order": 8},
    MOD_REPORTES:      {"label": "Reportes",      "path": "reportes/",        "icon": "fas fa-chart-bar",    "order": 9},
    MOD_CONFIGURACION: {"label": "Configuración", "path": "settings/",        "icon": "fas fa-cog",          "order": 99},
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
    MOD_FLOTA:         "/flota",
    MOD_REPORTES:      "/reportes",
    MOD_CONFIGURACION: "/settings",
}

# Modules unlocked per rubro (added to ALWAYS_ON)
MODULES_BY_RUBRO = {
    "WORKSHOP":            frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "WORKSHOP_MOTO":       frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "WORKSHOP_HEAVY":      frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "EXHAUST":             frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "PARTS":               frozenset({MOD_REPUESTOS}),
    "RECYCLING":           frozenset({MOD_REPUESTOS}),
    "TIRE":                frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "BODYSHOP":            frozenset({MOD_VEHICULOS, MOD_SERVICIOS}),
    "DETAILING":           frozenset({MOD_VEHICULOS, MOD_SERVICIOS}),
    "ELECTRIC":            frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "GLASS_AUDIO":         frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "FLEET":               frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS, MOD_FLOTA}),
    "FLEET_REPAIR":        frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS, MOD_FLOTA}),
    "SUSPENSION_STEERING": frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "BRAKES":              frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "OBD_DIAGNOSTIC":      frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "CLASSIC_CARS":        frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "AUDIO_ENTERTAINMENT": frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "GAS_CONVERSION":      frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "BODY_GLASS":          frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "TUNING":              frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS}),
    "DESARMADURIA":        frozenset({MOD_DESARME, MOD_REPUESTOS}),
    "MIXED":               frozenset({MOD_VEHICULOS, MOD_REPUESTOS, MOD_SERVICIOS, MOD_DESARME}),
}
