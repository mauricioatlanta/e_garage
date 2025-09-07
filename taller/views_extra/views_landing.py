"""
Vista para la landing page de eGarage
"""

from django.shortcuts import render


def landing_egarage(request):
    """Vista para servir la landing page profesional de eGarage"""
    from django.conf import settings

    context = {
        "title": "eGarage - Software N°1 para Talleres Mecánicos",
        "description": "El software más completo para talleres mecánicos. Presupuestos, órdenes de trabajo, control de repuestos y más.",
        "debug": settings.DEBUG,
    }
    return render(request, "landing_egarage.html", context)
