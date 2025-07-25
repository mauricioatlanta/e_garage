
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from taller.models.vehiculos import Vehiculo
from taller.forms.vehiculo import VehiculoForm
from taller.models.perfilusuario import PerfilUsuario

def lista_vehiculos(request):

@login_required
def lista_vehiculos(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        vehiculos = Vehiculo.objects.all()
    else:
        vehiculos = Vehiculo.objects.filter(empresa=perfil.empresa)
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

def crear_vehiculo(request):

@login_required
def crear_vehiculo(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa = perfil.empresa
            vehiculo.save()
            return redirect('vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'vehiculos/crear_vehiculo.html', {'form': form})

def detalle_vehiculo(request, vehiculo_id):

@login_required
def detalle_vehiculo(request, vehiculo_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if perfil.es_superadmin:
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    else:
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=perfil.empresa)
    return render(request, 'vehiculos/detalle_vehiculo.html', {'vehiculo': vehiculo})
