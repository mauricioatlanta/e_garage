"""
Compat legacy: centro de trabajo / workspace.
Stub temporal hasta restaurar vistas reales.
"""

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from taller.models.vehiculos import Vehiculo
from taller.views_ingreso import ingreso_centro, ingreso_buscar


centro_trabajo = ingreso_centro
centro_trabajo_buscar = ingreso_buscar


def vehiculo_historial(request, vehiculo_id, *args, **kwargs):
    """
    Compat temporal. Redirige al detalle del vehículo.
    """
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    try:
        return redirect("vehiculos:ver_vehiculo", vehiculo_id=vehiculo.pk)
    except Exception:
        return redirect("/")
