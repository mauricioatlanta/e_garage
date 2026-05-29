# taller/vehiculos/views_create_parts.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from taller.models.extras_vehiculo import (  # usa SIEMPRE extras_vehiculo
    CajaVehiculo,
    MotorVehiculo,
)
from taller.models.modelo import Modelo


@login_required
def crear_motor(request):
    modelo_id = request.GET.get("modelo") or request.POST.get("modelo")
    modelo = get_object_or_404(Modelo, pk=modelo_id)
    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        if not nombre:
            return render(
                request,
                "taller/vehiculos/crear_motor_simple.html",
                {"modelo": modelo, "error": "Nombre requerido"},
            )
        motor, _ = MotorVehiculo.objects.get_or_create(nombre=nombre)
        motor.modelos.add(modelo)  # ASOCIAR!
        return render(
            request,
            "taller/vehiculos/close_and_notify.html",
            {
                "kind": "motor",
                "obj": motor,
            },
        )
    return render(request, "taller/vehiculos/crear_motor_simple.html", {"modelo": modelo})


@login_required
def crear_caja(request):
    modelo_id = request.GET.get("modelo") or request.POST.get("modelo")
    modelo = get_object_or_404(Modelo, pk=modelo_id)
    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        if not nombre:
            return render(
                request,
                "taller/vehiculos/crear_caja_simple.html",
                {"modelo": modelo, "error": "Nombre requerido"},
            )
        caja, _ = CajaVehiculo.objects.get_or_create(nombre=nombre)
        caja.modelos.add(modelo)  # ASOCIAR!
        return render(
            request,
            "taller/vehiculos/close_and_notify.html",
            {
                "kind": "caja",
                "obj": caja,
            },
        )
    return render(request, "taller/vehiculos/crear_caja_simple.html", {"modelo": modelo})
