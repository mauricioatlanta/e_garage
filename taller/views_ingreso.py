from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from taller.models.vehiculos import Vehiculo


def ingreso_centro(request, *args, **kwargs):
    # Evitar loops: nunca redirigir a la ruta canónica /workspace/
    path = (request.path or "").lower()
    if path.startswith("/us/"):
        return redirect("/us/dashboard/")
    if path.startswith("/cl/"):
        return redirect("/cl/es/dashboard/")
    # Fallback seguro para /workspace/ y otros casos
    return redirect("/cl/es/dashboard/")


def ingreso_buscar(request, *args, **kwargs):
    query = request.GET.urlencode()
    url = "/workspace/buscar/"
    if query:
        url = f"{url}?{query}"
    return HttpResponseRedirect(url)


def panel_ingreso_vehiculo(request, pk, *args, **kwargs):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)

    posibles_rutas = [
        "vehiculos:ver_vehiculo",
        "vehiculos:detalle",
        "vehiculos:vehiculo_detalle",
        "taller:vehiculo_detalle",
        "vehiculo_detalle",
    ]

    for ruta in posibles_rutas:
        try:
            return redirect(ruta, vehiculo_id=vehiculo.pk)
        except Exception:
            continue

    return redirect("/")
