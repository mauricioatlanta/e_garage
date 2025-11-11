from django.http import JsonResponse
from django.shortcuts import render

from .forms import UbicacionForm
from .models import Ciudad


def registro_ubicacion(request):
    if request.method == "POST":
        form = UbicacionForm(request.POST)
        if form.is_valid():
            estado = form.cleaned_data["estado"]
            ciudad_nombre = form.cleaned_data["ciudad"]
            zip_code = form.cleaned_data["zip_code"]
            # Buscar ciudad sin importar mayúsculas/minúsculas
            ciudad = Ciudad.objects.filter(nombre__iexact=ciudad_nombre, estado=estado).first()
            if ciudad:
                zip_code = ciudad.zip_code  # ya existe, usamos su zip
            else:
                ciudad = Ciudad.objects.create(
                    nombre=ciudad_nombre, estado=estado, zip_code=zip_code
                )
    else:
        form = UbicacionForm()
    return render(request, "ubicacion/registro_ubicacion.html", {"form": form})


def ciudades_por_estado(request, estado_id):
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values("nombre")
    return JsonResponse(list(ciudades), safe=False)


def zip_code_por_ciudad(request, ciudad_nombre):
    try:
        ciudad = Ciudad.objects.get(nombre__iexact=ciudad_nombre)
        return JsonResponse({"zip_code": ciudad.zip_code})
    except Ciudad.DoesNotExist:
        return JsonResponse({"zip_code": None})
