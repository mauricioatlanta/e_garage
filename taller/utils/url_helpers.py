from django.urls import reverse


def get_country_ns_from_path(path: str) -> str:
    """
    Devuelve el namespace del país según el prefijo de la ruta.
    Debe coincidir con taller.templatetags.country_url._country_ns_from_path
    para que reverse_country y {% country_url %} resuelvan igual.
    """
    path = (path or "/").strip()
    if path.startswith("/us/en/") or path == "/us/en":
        return "us_en"
    if path.startswith("/us/es/") or path == "/us/es":
        return "us_es"
    if path.startswith("/us/") or path == "/us":
        return "usa"
    if path.startswith("/cl/es/") or path == "/cl/es":
        return "chile"
    if path.startswith("/cl/") or path == "/cl":
        return "chile"
    return "chile"


def reverse_country(request, view_path, app_namespace="taller", *args, **kwargs):
    """
    Construye una URL namespaced con el país actual desde Python (vistas).

    Args:
        request: HttpRequest object
        view_path: String como "clientes:lista_clientes" o "desarme:mapa_piezas"
        app_namespace: Namespace de la app (default: "taller"). Se omite para us_en/us_es.
        *args, **kwargs: Argumentos para reverse(). Soporta kwargs={"pk": n} o pk=n.

    Returns:
        URL string

    Ejemplos:
        return redirect(reverse_country(request, "desarme:dashboard_financiero", kwargs={"pk": vehiculo.pk}))
        return redirect(reverse_country(request, "repuestos:lista_repuestos"))

    Nota: us_en y us_es incluyen taller.urls directamente (no tienen "taller" en el medio).
    """
    country_ns = get_country_ns_from_path(getattr(request, "path", None) or "/")

    # us_en y us_es: include directo de taller.urls, estructura country:desarme:mapa
    if country_ns in ("us_en", "us_es"):
        full_name = f"{country_ns}:{view_path}"
    elif app_namespace == "direct" or app_namespace == "":
        full_name = f"{country_ns}:{view_path}"
    else:
        full_name = f"{country_ns}:{app_namespace}:{view_path}"

    # Soportar kwargs={"pk": n} (común) sin que se pase mal a reverse()
    url_kwargs = kwargs.pop("kwargs", None)
    if url_kwargs is not None:
        kwargs = url_kwargs

    return reverse(full_name, args=args, kwargs=kwargs)


def get_country_from_path(path: str) -> str:
    """
    Obtiene el país desde la ruta.

    Args:
        path: String de la ruta (ej: "/us/clientes/", "/cl/es/clientes/")

    Returns:
        "usa" o "chile"
    """
    if path.startswith("/us/") or path == "/us":
        return "usa"
    return "chile"
