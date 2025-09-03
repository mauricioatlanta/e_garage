
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from taller.vehiculos.forms import VehiculoForm  # Este formulario ya tiene la lógica de país
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
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

@login_required
def editar_vehiculo(request, vehiculo_id):
    """Vista específica para editar vehículos en USA"""
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
    
    # Obtener el vehículo a editar
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id, empresa=empresa)

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo, user=request.user)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa = empresa
            vehiculo.save()
            form.save_m2m()
            messages.success(request, "🚗 Vehicle updated successfully.")
            return redirect('taller:vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo, user=request.user)

    # El formulario ya está configurado con marca_texto y modelo_texto para USA
    return render(request, 'taller/vehiculos/editar_vehiculo.html', {
        'form': form,
        'vehiculo': vehiculo,
        'country': country,
        'clientes': Cliente.objects.filter(empresa=request.user.empresa),
        'colores': ColorVehiculo.get_colores_para_pais('US'),
    })
