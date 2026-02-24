from django import template
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

register = template.Library()


def _country_ns_from_path(path: str) -> str:
    """
    Devuelve el namespace del país según el prefijo de la ruta actual.
    Considera el segmento de idioma si está presente.
    """
    if path.startswith("/us/en/") or path == "/us/en":
        return "usa"  # usa_en no existe, usar usa
    elif path.startswith("/us/es/") or path == "/us/es":
        return "usa"  # usa_es no existe, usar usa
    elif path.startswith("/us/") or path == "/us":
        return "usa"
    elif path.startswith("/cl/es/") or path == "/cl/es":
        return "chile"
    elif path.startswith("/cl/") or path == "/cl":
        return "chile"
    return "chile"


def _extract_lang_from_path(path: str) -> str:
    """
    Extrae el código de idioma del path si está presente.
    Retorna 'en' o 'es' si se encuentra, None en caso contrario.
    """
    if path.startswith("/us/en/") or path == "/us/en":
        return "en"
    elif path.startswith("/us/es/") or path == "/us/es":
        return "es"
    elif path.startswith("/cl/es/") or path == "/cl/es":
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

    # view_path puede ser "clientes:lista_clientes" o "lista_clientes"
    if ":" in view_path:
        # Si ya tiene namespace (ej: vehiculos:lista_vehiculos), agregar el país y app_namespace
        if app_namespace == "direct" or app_namespace == "":
            # Para URLs definidas directamente en el namespace del país (ej: usa:ajax:vehiculos_por_cliente)
            full_name = f"{country_ns}:{view_path}"
        else:
            # URLs definidas en sub-namespaces (ej: usa:taller:documentos:lista)
            full_name = f"{country_ns}:{app_namespace}:{view_path}"
    else:
        # Sin subnamespace
        if app_namespace == "direct":
            # Para URLs definidas directamente en el namespace del país (ej: usa:futuristic_company_settings)
            full_name = f"{country_ns}:{view_path}"
        else:
            # URLs definidas en sub-namespaces (ej: usa:taller:company_settings)
            full_name = f"{country_ns}:{app_namespace}:{view_path}"

    # Convertir args de tuple a lista para evitar problemas con reverse
    args_list = list(args) if args else []

    # Si estamos en una ruta USA con idioma, intentar pasar lang como parámetro si la URL lo requiere
    # Primero intentar sin lang, si falla, agregar lang
    try:
        return reverse(full_name, args=args_list, kwargs=kwargs)
    except NoReverseMatch as e:
        # Si falla con NoReverseMatch y el error menciona 'lang', intentar agregar lang
        error_msg = str(e).lower()
        if "lang" in error_msg and request:
            lang = _extract_lang_from_path(request.path or "/")
            if lang and "lang" not in kwargs:
                kwargs_with_lang = {**kwargs, "lang": lang}
                try:
                    return reverse(full_name, args=args_list, kwargs=kwargs_with_lang)
                except NoReverseMatch:
                    # Si aún falla, re-lanzar el error original
                    raise e
        # Si no es un error relacionado con lang, re-lanzar
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
