from django.shortcuts import render, redirect, get_object_or_404
from taller.models.vehiculos import Vehiculo
from taller.vehiculos.forms import VehiculoForm

def crear_vehiculo(request):
    if request.method == 'POST':
        data = request.POST.copy()
        modelo_id = data.get('modelo')
        # Motor
        if data.get('motor') == '__nuevo__' and data.get('motor_nuevo'):
            from taller.models.extras_vehiculo import MotorVehiculo
            motor_obj, _ = MotorVehiculo.objects.get_or_create(
                nombre=data['motor_nuevo'], modelo_id=modelo_id
            )
            data['motor'] = motor_obj.pk
        # Caja
        if data.get('caja') == '__nuevo__' and data.get('caja_nueva'):
            from taller.models.extras_vehiculo import CajaVehiculo
            caja_obj, _ = CajaVehiculo.objects.get_or_create(
                nombre=data['caja_nueva'], modelo_id=modelo_id
            )
            data['caja'] = caja_obj.pk
        form = VehiculoForm(data)
        if form.is_valid():
            form.instance.empresa = request.empresa
            form.save()
            return redirect('vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'crear_vehiculo.html', {'form': form})