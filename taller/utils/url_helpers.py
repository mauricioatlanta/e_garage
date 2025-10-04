from django.urls import reverse


def reverse_country(request, view_path, app_namespace="taller", *args, **kwargs):
    """
    Construye una URL namespaced con el país actual desde Python (vistas).

    Args:
        request: HttpRequest object
        view_path: String como "clientes:lista_clientes" o "lista_clientes"
        app_namespace: Namespace de la app (default: "taller")
        *args, **kwargs: Argumentos para reverse()

    Returns:
        URL string

    Ejemplos:
        return redirect(reverse_country(request, "clientes:lista_clientes"))
        return redirect(reverse_country(request, "company_settings"))
    """
    country_ns = "usa" if request.path.startswith("/us/") else "chile"

    if ":" in view_path:
        name = f"{country_ns}:{app_namespace}:{view_path}"
    else:
        name = f"{country_ns}:{app_namespace}:{view_path}"

    return reverse(name, args=args, kwargs=kwargs)


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


















