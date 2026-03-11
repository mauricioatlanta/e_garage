"""
Home / portal principal del módulo de desarmaduría.
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from taller.models import Vehiculo, Repuesto
from taller.utils.empresa import get_or_create_empresa


@login_required
def home_desarme(request):
    """
    Centro de Desarme / Disassembly Center.

    Muestra KPIs globales del módulo de desarmaduría y accesos rápidos a:
    - Ingresar vehículo de desarme
    - Listado de vehículos de desarme
    - Plantillas de desarme
    """
    empresa = get_or_create_empresa(request)

    vehiculos_qs = Vehiculo.objects.filter(empresa=empresa, tipo_uso="desarme")

    total_vehiculos = vehiculos_qs.count()
    estados = (
        vehiculos_qs.values("estado_desarme")
        .annotate(cantidad=Count("id"))
        .order_by("estado_desarme")
    )
    total_cerrados = vehiculos_qs.filter(estado_desarme="cerrado").count()

    total_repuestos_desarme = Repuesto.objects.filter(
        empresa=empresa,
        tipo_origen="desarme",
    ).count()

    context = {
        "total_vehiculos_desarme": total_vehiculos,
        "estados_desarme_counts": estados,
        "total_vehiculos_cerrados": total_cerrados,
        "total_repuestos_desarme": total_repuestos_desarme,
    }
    return render(request, "taller/desarme/home.html", context)
