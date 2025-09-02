
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.vehiculos.forms import VehiculoForm
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.models.extras_vehiculo import ColorVehiculo

@login_required
def lista_vehiculos(request):
    # Lógica exclusiva para USA: mostrar marcas y modelos
    marcas = MarcaVehiculo.objects.filter(activa=True)
    modelos = ModeloVehiculo.objects.filter(activo=True)
    return render(request, 'taller/vehiculos/vehiculos.html', {'marcas': marcas, 'modelos': modelos})

@login_required
def crear_vehiculo(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )

    country = 'US'

    if request.method == 'POST':
        form = VehiculoForm(request.POST, user=request.user)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa = empresa
            vehiculo.save()
            messages.success(request, "🚗 Vehicle registered successfully.")
            return redirect('vehiculos_usa:lista_vehiculos')
        # Si hay errores, el formulario los mostrará automáticamente
    else:
        form = VehiculoForm(user=request.user)

    return render(request, 'taller/vehiculos/crear_vehiculo.html', {
        'form': form,
        'country': country,
        'clientes': Cliente.objects.filter(empresa=request.user.empresa),  # BLINDAJE: Filtrado por empresa
        'marcas_usa': MarcaVehiculo.objects.filter(activa=True).order_by('nombre'),
        'modelos_usa': ModeloVehiculo.objects.filter(activo=True).order_by('nombre'),
        'colores': ColorVehiculo.get_colores_para_pais('US'),  # CORREGIDO: Colores por país
    })
