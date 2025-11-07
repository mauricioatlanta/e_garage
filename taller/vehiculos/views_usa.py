# Views específicas para USA - usan templates localizados
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.vehiculos.forms import VehiculoForm

log = logging.getLogger(__name__)


@login_required
def lista_vehiculos(request):
    """Lista vehículos para USA."""
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "User has no assigned company")
        return redirect("/")
    
    vehiculos = Vehiculo.objects.filter(empresa=empresa).select_related(
        "cliente", "marca", "modelo", "motor", "caja", "color"
    ).order_by("-id")
    
    return render(request, "taller/us/en/vehiculos/lista_vehiculos.html", {"vehiculos": vehiculos})


@login_required
def crear_vehiculo(request):
    """Crear vehículo para USA."""
    empresa = getattr(request.user, "empresa", None)
    
    if not empresa:
        messages.error(request, "User has no assigned company")
        return redirect("/")

    if request.method == "POST":
        form = VehiculoForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    vehiculo = form.save(commit=False)
                    vehiculo.empresa = empresa
                    vehiculo.save()
                    
                    messages.success(request, f"Vehicle {vehiculo.patente or 'without plate'} created successfully")
                    return redirect("vehiculos_usa:lista_vehiculos")
            except Exception as e:
                log.error(f"Error creating vehicle: {e}")
                messages.error(request, f"Error creating vehicle: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form")
    else:
        form = VehiculoForm(user=request.user)
    
    ctx = {
        "form": form,
        "country": "US",
        "empresa": empresa,
    }
    
    return render(request, "taller/us/en/vehiculos/crear_vehiculo.html", ctx)


@login_required
def ver_vehiculo(request, pk):
    """Ver detalles de un vehículo (USA)."""
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=pk, empresa=empresa)
    
    return render(request, "taller/us/en/vehiculos/detalle.html", {"vehiculo": vehiculo})


@login_required
def editar_vehiculo(request, vehiculo_id):
    """Editar un vehículo (USA)."""
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)
    
    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, f"Vehicle {vehiculo.patente or 'without plate'} updated successfully")
                    return redirect("vehiculos_usa:lista_vehiculos")
            except Exception as e:
                log.error(f"Error updating vehicle: {e}")
                messages.error(request, f"Error updating vehicle: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form")
    else:
        form = VehiculoForm(instance=vehiculo, user=request.user)
    
    return render(request, "taller/us/en/vehiculos/editar_vehiculo.html", {
        "form": form,
        "vehiculo": vehiculo
    })



