# -*- coding: utf-8 -*-
"""
Vistas para ubicación.

NOTA: Las vistas legacy (ciudades_por_estado, zip_code_por_ciudad) están deprecadas.
Usa la nueva API en api.py: /api/locations?country=XX&state=YY
"""
from django.http import JsonResponse
from django.shortcuts import render

from taller.models.ubicacion import Ciudad

from .forms import UbicacionForm


def registro_ubicacion(request):
    """
    Vista legacy para registro de ubicación.
    
    NOTA: Esta vista puede estar deprecada. Considera usar la API nueva.
    """
    if request.method == "POST":
        form = UbicacionForm(request.POST)
        if form.is_valid():
            estado = form.cleaned_data["estado"]
            ciudad = form.cleaned_data.get("ciudad")
            zip_code = form.cleaned_data.get("zip_code", "")
            
            # Si se seleccionó una ciudad, usar su zip_code si existe
            if ciudad:
                # La ciudad ya viene del select, no necesitamos crearla
                # zip_code se puede obtener de la ciudad si tiene ese campo
                pass
    else:
        form = UbicacionForm()
    return render(request, "ubicacion/registro_ubicacion.html", {"form": form})


def ciudades_por_estado(request, estado_id):
    """
    Vista legacy - DEPRECADA.
    
    Usa la nueva API: /api/locations/cities/<state_id>/ o
    /api/locations?country=XX&state=YY
    """
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values("id", "nombre")
    return JsonResponse(list(ciudades), safe=False)


def zip_code_por_ciudad(request, ciudad_nombre):
    """
    Vista legacy - DEPRECADA.
    
    Usa la nueva API para obtener información de ciudades.
    """
    try:
        ciudad = Ciudad.objects.get(nombre__iexact=ciudad_nombre)
        # Nota: El modelo Ciudad de taller puede no tener zip_code
        # Si lo necesitas, agrégalo al modelo o usa otro campo
        zip_code = getattr(ciudad, "zip_code", None)
        return JsonResponse({"zip_code": zip_code})
    except Ciudad.DoesNotExist:
        return JsonResponse({"zip_code": None})
