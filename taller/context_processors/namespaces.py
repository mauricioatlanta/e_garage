from django.urls import resolve


def ui_namespaces(request):
    path = request.path_info.lstrip("/")
    first = path.split("/", 1)[0].lower()
    if first == "cl":
        taller_ns = "taller"
    elif first == "us":
        taller_ns = "taller"  # O 'taller_usa' si usas namespaces distintos
    else:
        taller_ns = "taller"
    return {"taller_ns": taller_ns}
