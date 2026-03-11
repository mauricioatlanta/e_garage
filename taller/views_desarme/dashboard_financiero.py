"""
Dashboard financiero del vehículo de desarme.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from taller.models import CostoVehiculoDesarme, Vehiculo
from taller.services.desarme_kpis import (
    build_vehicle_desarme_kpis,
    build_vehicle_piece_summary,
    build_vehicle_sales_summary,
)
from taller.utils.empresa import get_or_create_empresa


def _get_vehiculo_desarme(request, pk):
    empresa = get_or_create_empresa(request)
    return get_object_or_404(
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso="desarme",
    )


@login_required
def dashboard_vehiculo_desarme(request, pk):
    """Dashboard financiero: costos, ingresos, utilidad, piezas, últimas ventas."""
    vehiculo = _get_vehiculo_desarme(request, pk)
    kpis = build_vehicle_desarme_kpis(vehiculo)
    piece_summary = build_vehicle_piece_summary(vehiculo)
    last_sales = build_vehicle_sales_summary(vehiculo, limit=15)
    costos_adicionales = list(
        CostoVehiculoDesarme.objects.filter(vehiculo=vehiculo).order_by("-fecha", "-id")[:50]
    )
    cerrado = (vehiculo.estado_desarme or "").strip() == "cerrado"
    can_edit = not cerrado

    context = {
        "vehiculo": vehiculo,
        "kpis": kpis,
        "piece_summary": piece_summary,
        "last_sales": last_sales,
        "costos_adicionales": costos_adicionales,
        "cerrado": cerrado,
        "can_edit": can_edit,
    }
    return render(
        request,
        "taller/desarme/dashboard_financiero.html",
        context,
    )
