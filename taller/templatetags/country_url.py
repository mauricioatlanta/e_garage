from django import template
from django.urls import reverse

register = template.Library()


def _country_ns_from_path(path: str) -> str:
    """
    Devuelve 'usa' o 'chile' según el prefijo de la ruta actual
    """
    if path.startswith("/us/") or path == "/us":
        return "usa"
    return "chile"


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
        # Si ya tiene namespace (ej: vehiculos:lista_vehiculos), agregar el país y taller
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

    return reverse(full_name, args=args_list, kwargs=kwargs)


@register.simple_tag(takes_context=True)
def country_url_direct(context, view_path, *args, app_namespace="taller", **kwargs):
    """
    Versión directa que retorna la URL sin usar 'as' variable.
    Útil para casos donde necesitas la URL directamente en el template.

    Ejemplo:
      <a href="{% country_url_direct 'clientes:lista_clientes' %}">Clientes</a>
    """
    return country_url(context, view_path, app_namespace, *args, **kwargs)
