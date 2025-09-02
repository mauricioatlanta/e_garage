from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.extras_vehiculo import ColorVehiculo
from .forms import VehiculoForm

@login_required
def lista_vehiculos(request):
    # Lógica exclusiva para Chile
    vehiculos = Vehiculo.objects.filter(pais='CL')
    return render(request, 'taller/vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

@login_required
def crear_vehiculo(request):
    """Formulario creación de vehículo para país CL usando VehiculoForm personalizado."""
    empresa = getattr(request, 'empresa', getattr(request.user, 'empresa', None))
    if request.method == 'POST':
        form = VehiculoForm(request.POST, user=request.user)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            if empresa:
                vehiculo.empresa = empresa
            vehiculo.save()
            messages.success(request, '🚗 Vehículo creado correctamente.')
            return redirect('vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm(user=request.user)
    context = {
        'form': form,
        'country': 'CL',
        'clientes': Cliente.objects.filter(empresa=request.user.empresa),  # BLINDAJE: Filtrado por empresa
        'marcas': Marca.objects.filter(country='CL').order_by('nombre'),
        'colores': ColorVehiculo.get_colores_para_pais('CL'),  # CORREGIDO: Colores en español
    }
    return render(request, 'taller/vehiculos/crear_vehiculo.html', context)
