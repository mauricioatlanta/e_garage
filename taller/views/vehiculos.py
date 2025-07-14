from django.shortcuts import render, redirect, get_object_or_404
from taller.models.vehiculos import Vehiculo
from taller.vehiculos.forms import VehiculoForm

def crear_vehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'crear_vehiculo.html', {'form': form})