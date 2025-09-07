# taller/views/demo_catalogo.py
from django.shortcuts import render


def demo_catalogo_vehiculos(request):
    """
    Vista demo para mostrar el catálogo de vehículos con autocompletado
    """
    context = {
        "title": "Demo Catálogo de Vehículos - eGarage",
        "description": "Sistema de autocompletado con 5,008 modelos de vehículos",
    }
    return render(request, "demo_catalogo_vehiculos.html", context)
