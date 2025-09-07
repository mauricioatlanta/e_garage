from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def country_url(context, url_name, *args, **kwargs):
    """
    Genera URLs con namespace específico del país
    Uso: {% country_url 'nombre_url' app_namespace='app' %}
    """
    request = context.get("request")
    if not request:
        return ""

    # Extraer app_namespace de los kwargs
    app_namespace = kwargs.pop("app_namespace", None)

    path = request.path
    # Detecta prefijo de país
    if path.startswith("/cl/"):
        country_ns = "chile"
    elif path.startswith("/us/"):
        country_ns = "usa"
    else:
        country_ns = None

    # Manejar namespaces específicos por país
    if country_ns and app_namespace:
        # Mapeo especial para vehículos
        if app_namespace == "vehiculos":
            if country_ns == "usa":
                app_namespace = "vehiculos_usa"
            # Chile mantiene 'vehiculos'

        # Mapeo especial para reportes
        if app_namespace == "reportes":
            if country_ns == "chile":
                app_namespace = "reportes_cl"
            elif country_ns == "usa":
                app_namespace = "reportes_us"

        # Mapeo especial para taller - en USA las URLs de taller están directamente bajo el namespace usa
        if app_namespace == "taller" and country_ns == "usa":
            full_url_name = f"{country_ns}:{url_name}"
        else:
            full_url_name = f"{country_ns}:{app_namespace}:{url_name}"
    elif country_ns:
        full_url_name = f"{country_ns}:{url_name}"
    elif app_namespace:
        full_url_name = f"{app_namespace}:{url_name}"
    else:
        full_url_name = url_name

    # Intentar resolver la URL
    try:
        return reverse(full_url_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        # Fallback: intentar sin namespace de país
        if app_namespace:
            try:
                return reverse(f"{app_namespace}:{url_name}", args=args, kwargs=kwargs)
            except NoReverseMatch:
                pass
        # Último fallback: URL básica
        try:
            return reverse(url_name, args=args, kwargs=kwargs)
        except NoReverseMatch:
            return ""
