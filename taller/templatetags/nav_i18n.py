from django import template

register = template.Library()

MAPA_EN = {
    "ajustes": "Settings",
    "equipo": "Team",
    "centro": "Operations",
    "clientes": "Clients",
    "trabajos": "Work",
    "work": "Work",
    "extra": "Extra",
    "repuestos": "Parts",
    "reportes": "Reports",
    "servicios": "Services",
    "vehículos": "Vehicles",
    "vehiculos": "Vehicles",
    "salir": "Logout",
    "logout": "Logout",
    "inicio": "Home",
    "ventas": "Sales",
    "configuración": "Settings",
    "configuracion": "Settings",
}

MAPA_ES = {
    "work": "Trabajos",
    "settings": "Ajustes",
    "team": "Equipo",
    "operations": "Centro",
    "clients": "Clientes",
    "parts": "Repuestos",
    "reports": "Reportes",
    "services": "Servicios",
    "vehicles": "Vehículos",
    "logout": "Salir",
    "home": "Inicio",
    "sales": "Ventas",
}

@register.filter(name="translate_nav")
def translate_nav(value, request_or_lang=None):
    if not value or not isinstance(value, str):
        return value
    
    val_clean = value.strip().lower()
    
    # Determinar si es inglés
    is_en = False
    if request_or_lang:
        if isinstance(request_or_lang, str) and request_or_lang.lower().startswith("en"):
            is_en = True
        elif hasattr(request_or_lang, "path") and "/en/" in request_or_lang.path:
            is_en = True
        elif hasattr(request_or_lang, "LANGUAGE_CODE") and request_or_lang.LANGUAGE_CODE == "en":
            is_en = True

    if is_en:
        return MAPA_EN.get(val_clean, value)
    else:
        return MAPA_ES.get(val_clean, value)
