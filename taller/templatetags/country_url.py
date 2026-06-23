from django import template
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

register = template.Library()


def _country_ns_from_path(path: str) -> str:
    """
    Devuelve el namespace del país según el prefijo de la ruta actual.
    """
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
    elif path.startswith("/br/") or path == "/br":
        return "brasil"
    return "chile"


def _country_ns_from_empresa(empresa) -> str:
    """
    Devuelve el namespace del país según la empresa del documento (empresa.pais),
    para que los enlaces públicos (PDF, QR, etc.) sean coherentes con el país de la
    empresa y no con la ruta por la que entró el usuario.

    Empresa US → /us/... (us_es por defecto)
    Empresa CL → /cl/... (chile)
    Empresa UY → /uy/... (uruguay)
    """
    if not empresa:
        return "chile"
    pais = (getattr(empresa, "pais", None) or "").upper()
    country = (getattr(empresa, "country", None) or "").upper()
    if pais == "US" or country == "US":
        return "us_es"
    if pais == "UY" or country == "UY":
        return "uruguay"
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


def reverse_country_url(request, view_path, *args, **kwargs):
    """
    Resuelve una URL con el namespace del país actual (para uso en vistas Python).

    Uso:
        from taller.templatetags.country_url import reverse_country_url
        return redirect(reverse_country_url(request, "servicios:otros_servicios_menu"))
    """
    context = {"request": request} if request else {}
    return country_url(context, view_path, *args, **kwargs)


def _extract_lang_from_path(path: str) -> str:
    """
    Extrae el código de idioma del path si está presente.
    """
    if path.startswith("/us/en/") or path == "/us/en":
        return "en"
    elif path.startswith("/us/es/") or path == "/us/es":
        return "es"
    elif path.startswith("/cl/es/") or path == "/cl/es":
        return "es"
    elif path.startswith("/uy/es/") or path == "/uy/es":
        return "es"
    elif path.startswith("/mx/es/") or path == "/mx/es":
        return "es"
    return None


@register.simple_tag(takes_context=True)
def country_url(context, view_path, *args, app_namespace="taller", **kwargs):
    """
    Construye una URL namespaced con el país actual.

    Ejemplos de uso:
      {% country_url 'clientes:lista_clientes' as url_clientes %}
      {% country_url 'documentos:lista_documentos' app_namespace='taller' %}
      {% country_url 'company_settings' %}
      {% country_url 'vehiculos:lista_vehiculos' %}
      {% country_url 'clientes:ver_cliente' cliente.pk %}
    """
    request = context.get("request")
    if not request:
        # Fallback conservador a chile
        country_ns = "chile"
    else:
        country_ns = _country_ns_from_path(request.path or "/")

    # Normalizar servicios: y repuestos: según el país
    # Chile/Uruguay: viven bajo country:taller: (chile:taller:servicios:...)
    # USA (us_en/us_es): viven directo bajo country: (us_en:servicios:...)
    if country_ns in ("us_en", "us_es"):
        # USA: servicios y repuestos directos, sin sub-namespace taller
        view_path_for_ns = view_path
    else:
        # Chile, Uruguay, etc.: rutas que viven bajo chile:taller: (include taller.urls)
        if view_path.startswith(("servicios:", "repuestos:", "team:")):
            view_path_for_ns = f"taller:{view_path}"
        else:
            view_path_for_ns = view_path

    # usa y chile montan clientes/vehiculos/documentos directamente
    if country_ns in ("us_en", "us_es"):
        full_name = f"{country_ns}:{view_path_for_ns}"
    elif country_ns == "usa":
        # Caso especial: las URLs de desarme bajo /us/ viven en usa:taller:desarme:...
        if view_path.startswith("desarme:"):
            full_name = f"{country_ns}:taller:{view_path}"
        else:
            full_name = f"{country_ns}:{view_path}"
    elif country_ns in ("chile", "uruguay", "uruguay_es", "mexico"):
        if view_path.startswith("desarme:"):
            full_name = f"{country_ns}:taller:{view_path}"
        elif view_path_for_ns.startswith("taller:"):
            full_name = f"{country_ns}:{view_path_for_ns}"
        else:
            full_name = f"{country_ns}:{view_path}"
    else:
        # view_path puede ser "clientes:lista_clientes" o "lista_clientes"
        if ":" in view_path:
            if app_namespace == "direct" or app_namespace == "":
                full_name = f"{country_ns}:{view_path}"
            else:
                full_name = f"{country_ns}:{app_namespace}:{view_path}"
        else:
            if app_namespace == "direct":
                full_name = f"{country_ns}:{view_path}"
            else:
                full_name = f"{country_ns}:{app_namespace}:{view_path}"

    # Convertir args de tuple a lista para evitar problemas con reverse
    args_list = list(args) if args else []

    # Si estamos en us_en/us_es y falla (p. ej. desarme está en us_es:desarme:*, no en us_es:taller:desarme:*),
    # reintentar sin sub-namespace taller. No depender del texto del error para mayor robustez.
    try:
        return reverse(full_name, args=args_list, kwargs=kwargs)
    except NoReverseMatch as e:
        error_msg = str(e).lower()
        if country_ns in ("us_en", "us_es"):
            full_name_fallback = f"{country_ns}:{view_path}"
            try:
                return reverse(full_name_fallback, args=args_list, kwargs=kwargs)
            except NoReverseMatch:
                pass
        # Si falla con NoReverseMatch y el error menciona 'lang', intentar agregar lang
        if "lang" in error_msg and request:
            lang = _extract_lang_from_path(request.path or "/")
            if lang and "lang" not in kwargs:
                kwargs_with_lang = {**kwargs, "lang": lang}
                try:
                    return reverse(full_name, args=args_list, kwargs=kwargs_with_lang)
                except NoReverseMatch:
                    pass
        raise


@register.simple_tag(takes_context=True)
def country_url_direct(context, view_path, *args, app_namespace="taller", **kwargs):
    """
    Versión directa que retorna la URL sin usar 'as' variable.
    Útil para casos donde necesitas la URL directamente en el template.

    Ejemplo:
      <a href="{% country_url_direct 'clientes:lista_clientes' %}">Clientes</a>
    """
    return country_url(context, view_path, app_namespace, *args, **kwargs)


def _nav_prefix_from_path(path: str) -> str:
    """Devuelve el prefijo país/idioma canónico para la navegación principal."""
    normalized = (path or "").lower()
    if normalized.startswith("/us/en/") or normalized == "/us/en":
        return "/us/en"
    elif normalized.startswith("/us/es/") or normalized == "/us/es":
        return "/us/es"
    elif normalized.startswith("/us/") or normalized == "/us":
        return "/us/en"

    segments = normalized.strip("/").split("/") if normalized else []
    country = segments[0] if segments else "cl"
    lang = segments[1] if len(segments) > 1 else "es"

    if country == "br":
        return "/br/pt"
    if country in ("cl", "uy", "mx", "pe", "co", "ec", "ar", "ve"):
        return f"/{country}/{lang if lang in ('es', 'en', 'pt') else 'es'}"
    return "/cl/es"


@register.simple_tag(takes_context=True)
def nav_url(context, section: str) -> str:
    """
    URL canónica para la navegación principal.

    Evita depender de namespaces heterogéneos entre módulos antiguos
    (`/cl/es/...`) y módulos montados directamente por país (`/cl/documentos/`,
    `/cl/reportes/`).
    """
    request = context.get("request")
    path = getattr(request, "path", "") if request else ""
    prefix = _nav_prefix_from_path(path)

    routes = {
        "settings": f"{prefix}/settings/",
        "center": f"{prefix}/centro-operaciones-espacial/",
        "clients": f"{prefix}/clientes/",
        "documents": f"{prefix}/documentos/",
        "extra": f"{prefix}/servicios/otros-servicios/",
        "parts": f"{prefix}/repuestos/",
        "reports": f"{prefix}/reportes/",
        "services": f"{prefix}/servicios/",
        "disassembly": f"{prefix}/desarme/",
        "vehicles": f"{prefix}/vehiculos/",
        "team": f"{prefix}/equipo/",
    }
    return routes.get(section, f"{prefix}/workspace/")
