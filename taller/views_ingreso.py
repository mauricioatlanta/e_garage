"""
Vistas para el Centro de Ingreso Vehicular.

Hub de ingreso: omnibox HTMX + accesos OCR/QR/búsqueda cliente/nuevo vehículo.
Panel de vehículo: historial de documentos en el tiempo.
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from taller.auth.decorators import login_required_default
from taller.models import Documento, Vehiculo


@login_required_default
def ingreso_centro(request):
    """
    HUB del ingreso: omnibox + accesos a OCR/QR + búsqueda.
    """
    return render(request, "taller/ingreso/centro_ingreso.html")


@login_required_default
def ingreso_buscar(request):
    """
    Endpoint HTMX: entrega sugerencias en vivo.
    """
    q = (request.GET.get("q") or "").strip()
    if not q:
        return render(
            request,
            "taller/ingreso/partials/resultados_busqueda.html",
            {"vehiculos": []},
        )

    try:
        empresa = request.user.empresa
    except Exception:
        return render(
            request,
            "taller/ingreso/partials/resultados_busqueda.html",
            {"vehiculos": []},
        )

    vehiculos = (
        Vehiculo.objects.filter(empresa=empresa)
        .select_related("cliente")
        .filter(
            Q(patente__icontains=q)
            | Q(vin__icontains=q)
            | Q(cliente__nombre__icontains=q)
            | Q(cliente__telefono__icontains=q)
        )
        .order_by("patente")[:8]
    )
    return render(
        request,
        "taller/ingreso/partials/resultados_busqueda.html",
        {"vehiculos": vehiculos},
    )


@login_required_default
def panel_ingreso_vehiculo(request, pk: int):
    """
    Panel del vehículo: historial a través del tiempo.
    """
    try:
        empresa = request.user.empresa
    except Exception:
        if "/us/" in (request.path or ""):
            return redirect("usa:configuracion")
        return redirect("chile:configuracion")

    vehiculo = get_object_or_404(
        Vehiculo.objects.select_related("cliente").filter(empresa=empresa),
        pk=pk,
    )

    # Historial de documentos por fecha_emision (KPI estándar eGarage)
    docs = (
        Documento.objects.filter(vehiculo=vehiculo, empresa=empresa)
        .select_related("cliente", "vehiculo")
        .order_by("-fecha_emision")[:50]
    )

    return render(
        request,
        "taller/ingreso/panel_vehiculo_ingreso.html",
        {"vehiculo": vehiculo, "docs": docs},
    )
