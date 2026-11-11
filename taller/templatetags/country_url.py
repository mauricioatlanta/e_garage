def _safe_reverse(viewname, args_list, kwargs_dict):
    clean_kwargs = {k: v for k, v in kwargs_dict.items() if v is not None} if kwargs_dict else {}
    if clean_kwargs and args_list:
        # Si vienen ambos, priorizar kwargs o combinar según corresponda
        return reverse(viewname, kwargs=clean_kwargs)
    elif clean_kwargs:
        return reverse(viewname, kwargs=clean_kwargs)
    elif args_list:
        return reverse(viewname, args=args_list)
    return reverse(viewname)

import re
from django import template
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

register = template.Library()

def _country_ns_from_path(path: str) -> str:
    """Devuelve el namespace del país según el prefijo de la ruta actual."""
    if not path:
        return "chile"
    if path.startswith("/us/en/") or path == "/us/en":
        return "us_en"
    elif path.startswith("/us/es/") or path == "/us/es":
        return "us_es"
    elif path.startswith("/us/") or path == "/us":
        return "usa"
    elif path.startswith("/uy/es/") or path == "/uy/es":
        return "uruguay_es"
    elif path.startswith("/uy/") or path == "/uy":
        return "uruguay"
    elif path.startswith("/co/es/") or path == "/co/es":
        return "colombia"
    elif path.startswith("/co/") or path == "/co":
        return "colombia"
    elif path.startswith("/cl/es/") or path == "/cl/es":
        return "chile"
    elif path.startswith("/cl/") or path == "/cl":
        return "chile"
    elif path.startswith("/mx/es/") or path == "/mx/es":
        return "mexico"
    elif path.startswith("/mx/") or path == "/mx":
        return "mexico"
    elif path.startswith("/ar/es/") or path == "/ar/es":
        return "argentina_es"
    elif path.startswith("/ar/") or path == "/ar":
        return "argentina"
    elif path.startswith("/ve/es/") or path == "/ve/es":
        return "venezuela"
    elif path.startswith("/ve/") or path == "/ve":
        return "venezuela"
    elif path.startswith("/pe/") or path == "/pe":
        return "peru"
    elif path.startswith("/ec/") or path == "/ec":
        return "ecuador"
    elif path.startswith("/br/") or path == "/br":
        return "brasil"
    return "chile"

def _country_ns_from_empresa(empresa) -> str:
    """Devuelve el namespace según la empresa."""
    if not empresa:
        return "chile"
    pais = (getattr(empresa, "pais", None) or "").upper()
    country = (getattr(empresa, "country", None) or "").upper()
    if pais == "US" or country == "US":
        return "us_es"
    if pais == "UY" or country == "UY":
        return "uruguay"
    if pais == "CO" or country == "CO":
        return "colombia"
    if pais == "EC" or country == "EC":
        return "ecuador"
    if pais == "PE" or country == "PE":
        return "peru"
    if pais == "CL" or country == "CL":
        return "chile"
    if pais == "MX" or country == "MX":
        return "mexico"
    if pais == "AR" or country == "AR":
        return "argentina"
    if pais == "VE" or country == "VE":
        return "venezuela"
    if pais == "PE" or country == "PE":
        return "peru"
    if pais == "BR" or country == "BR":
        return "brasil"
    return "chile"

def _extract_lang_from_path(path: str) -> str:
    """Extrae el código de idioma del path si está presente."""
    if not path:
        return None
    if "/en/" in path:
        return "en"
    elif "/es/" in path:
        return "es"
    return None

def reverse_country_url(request, view_path, *args, **kwargs):
    """Resuelve una URL con el namespace del país actual (para vistas Python)."""
    context = {"request": request} if request else {}
    return country_url(context, view_path, *args, **kwargs)

@register.simple_tag(takes_context=True)
def country_url(context, view_name, *args, **kwargs):
    request = context.get("request")
    context_empresa = context.get("empresa")

    # 1. Prioridad: Ruta de USA (/us/) o Modo Soporte USA para Superusuario
    p_act = getattr(request, "path_info", "") or getattr(request, "path", "") or "/"
    is_us = p_act.startswith("/us/") or p_act == "/us"
    is_support_us = (
        getattr(request, "user", None)
        and getattr(request.user, "is_superuser", False)
        and ((request.session.get("modo_soporte_pais") == "us" or request.session.get("support_country") == "us") if hasattr(request, "session") and request.session else False)
    )

    # FIX: URL manda primero para TODOS los paises, no solo USA
    # Antes: /ve/ ignoraba la URL y usaba empresa.pais (CL) -> mandaba a /cl/es/clientes/
    # Ahora: /ve/es/ -> venezuela, /cl/es/ -> chile, /mx/es/ -> mexico, etc.
    # Solo si la URL no tiene pais, usar empresa como fallback
    known_prefixes = ('/ve/', '/cl/', '/mx/', '/pe/', '/br/', '/ar/', '/uy/', '/ec/', '/co/', '/us/')
    has_country_in_url = any(p_act.startswith(x) or p_act == x.rstrip('/') for x in known_prefixes)
    if is_us or is_support_us:
        lang_act = _extract_lang_from_path(p_act) or getattr(request, "LANGUAGE_CODE", "es")
        country_ns = "us_en" if str(lang_act).lower() == "en" else "us_es"
    elif has_country_in_url:
        country_ns = _country_ns_from_path(p_act)
        # Ajustar idioma para US ya cubierto arriba, para otros mantener namespace de path
        # Si el namespace es venezuela etc, no cambiar por idioma
    else:
        active_empresa = context_empresa or getattr(request, "empresa", None)
        if active_empresa:
            country_ns = _country_ns_from_empresa(active_empresa)
            if country_ns == "us_es" and getattr(request, "LANGUAGE_CODE", "") == "en":
                country_ns = "us_en"
        else:
            country_ns = _country_ns_from_path(p_act)

    args_list = list(args)

    # Construir nombres de namespace candidatos
    if ":" in str(view_name):
        full_name = f"{country_ns}:{view_name}"
    else:
        full_name = f"{country_ns}:{view_name}"

    # Resolución protegida contra NoReverseMatch
    try:
        return _safe_reverse(full_name, args_list, kwargs)
    except NoReverseMatch:
        pass

    try:
        return _safe_reverse(view_name, args_list, kwargs)
    except NoReverseMatch:
        pass

    # Fallbacks inteligentes para fallos comunes de view_name
    view_str = str(view_name)
    if "crear" in view_str:
        if "cliente" in view_str or "clientes" in view_str:
            for c_try in [f"{country_ns}:clientes:crear_cliente", f"{country_ns}:clientes:crear", "clientes:crear_cliente"]:
                try:
                    return _safe_reverse(c_try, args_list, kwargs)
                except NoReverseMatch:
                    pass
            return f"/{country_ns[:2]}/es/clientes/crear/"
        if "vehiculo" in view_str or "vehiculos" in view_str:
            for c_try in [f"{country_ns}:vehiculos:crear_vehiculo", f"{country_ns}:vehiculos:crear", "vehiculos:crear_vehiculo"]:
                try:
                    return _safe_reverse(c_try, args_list, kwargs)
                except NoReverseMatch:
                    pass
            return f"/{country_ns[:2]}/es/vehiculos/crear/"

    return "#"
