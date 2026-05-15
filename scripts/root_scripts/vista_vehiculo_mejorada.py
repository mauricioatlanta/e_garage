#!/usr/bin/env python3
"""
Vista mejorada para crear vehículos siguiendo las especificaciones
"""

vista_mejorada = '''
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import transaction
from taller.vehiculos.forms import VehiculoForm
from taller.models.clientes import Cliente
from taller.utils.pais_utils import get_marcas_por_pais, get_configuracion_pais
from taller.models.extras_vehiculo import ColorVehiculo
import logging

log = logging.getLogger(__name__)

@login_required
@transaction.atomic
def crear_vehiculo(request):
    """Vista para crear vehículos con FormVehiculo"""
    empresa = getattr(request.user, "empresa", None)

    if not empresa:
        messages.error(request, "No tienes una empresa asignada")
        return redirect('taller:dashboard')

    if request.method == "POST":
        print('[DEBUG POST] Datos recibidos:', dict(request.POST))

        form = VehiculoForm(request.POST, user=request.user)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            # 🔒 Consistencia multi-tenant
            vehiculo.empresa = empresa
            vehiculo.save()
            form.save_m2m()
            messages.success(request, "Vehículo creado correctamente.")
            log.info(f"Vehículo creado: {vehiculo}")
            # ✅ Redirigir a la lista
            return redirect("chile:taller:vehiculos:lista_vehiculos")
        else:
            messages.error(request, "Revisa los errores del formulario.")
            print('[DEBUG] Errores del formulario:', form.errors)
    else:
        form = VehiculoForm(user=request.user)

    # Detectar país para contexto
    country = getattr(empresa, 'pais', 'CL')

    # Si usas el combo manual de clientes en el template:
    clientes = Cliente.objects.filter(empresa=empresa).order_by("nombre")

    # Obtener marcas según país
    marcas = get_marcas_por_pais(country)

    # Colores globales
    colores = ColorVehiculo.objects.all()

    return render(
        request,
        "taller/vehiculos/crear_vehiculo.html",
        {
            "form": form,
            "clientes": clientes,
            "marcas": marcas,
            "colores": colores,
            # Si usas lógica por país en el template:
            "country": country,
            "SHOW_DEBUG": True,
        },
    )
'''

print("📝 Vista mejorada para crear vehículos:")
print("=" * 60)
print(vista_mejorada)
print("=" * 60)

print("\n🔧 Puntos clave de la vista mejorada:")
print("• Usa VehiculoForm(request.POST, user=request.user)")
print("• Establece vehiculo.empresa antes de save()")
print("• Redirige a 'taller:vehiculos:lista_vehiculos' tras éxito")
print("• Incluye logging detallado para debug")
print("• Maneja errores de validación con mensajes")
print("• Pasa contexto necesario al template")

print("\n🎯 Para implementar esta vista:")
print("1. Reemplaza la función crear_vehiculo en taller/vehiculos/views.py")
print("2. Asegúrate de que VehiculoForm esté importado correctamente")
print("3. Verifica que el template use los campos del form correctamente")
