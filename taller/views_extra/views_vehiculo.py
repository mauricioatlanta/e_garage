
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.vehiculos import Vehiculo
from taller.vehiculos.forms import VehiculoForm
from taller.models.perfil_usuario import PerfilUsuario
from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.extras_vehiculo import ColorVehiculo


@login_required
def lista_vehiculos(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        vehiculos = Vehiculo.objects.all()
    else:
        vehiculos = Vehiculo.objects.filter(empresa=perfil.empresa)
    return render(request, 'taller/vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})


@login_required
def crear_vehiculo(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, user=request.user)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa = perfil.empresa
            vehiculo.save()
            return redirect('vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm(user=request.user)
    # FILTRADO POR EMPRESA - No exponer todos los clientes
    clientes = Cliente.objects.filter(empresa=perfil.empresa)
    marcas = Marca.objects.filter(country='CL').order_by('nombre')
    colores = ColorVehiculo.objects.all()
    return render(request, 'taller/vehiculos/crear_vehiculo.html', {'form': form, 'clientes': clientes, 'marcas': marcas, 'colores': colores})


@login_required
def detalle_vehiculo(request, vehiculo_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    else:
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=perfil.empresa)
    return render(request, 'taller/vehiculos/detalle_vehiculo.html', {'vehiculo': vehiculo})
