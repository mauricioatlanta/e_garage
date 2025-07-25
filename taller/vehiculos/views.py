from django.http import JsonResponse
from taller.models.clientes import Cliente
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from dal import autocomplete
from taller.utils.pais_utils import get_marcas_por_pais, get_configuracion_pais

@login_required
def api_busqueda_clientes(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get('q', '').strip()
    # Filtrar solo clientes de la empresa del usuario
    clientes = Cliente.objects.filter(empresa=empresa)
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(email__icontains=q)
        )
    data = [
        {
            'id': c.pk,
            'nombre': c.nombre,
            'apellido': c.apellido,
            'email': c.email
        } for c in clientes[:12]
    ]
    return JsonResponse(data, safe=False)
from django.shortcuts import render, redirect
from taller.vehiculos.forms import VehiculoForm
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo
from taller.models.marca import Marca
@login_required
def api_marcas(request):
    # Las marcas son globales, pero requieren autenticación
    q = request.GET.get('q', '').strip()
    marcas = Marca.objects.all()
    if q:
        marcas = marcas.filter(nombre__icontains=q)
    data = [
        {'id': m.pk, 'nombre': m.nombre} for m in marcas[:12]
    ]
    return JsonResponse(data, safe=False)
from taller.models.modelo import Modelo

@login_required
def crear_vehiculo(request):
    from taller.models.clientes import Cliente
    from taller.models.marca import Marca
    from taller.models.modelo import Modelo
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    def get_or_create_fk(model, value, **kwargs):
        """Función auxiliar segura - solo usada dentro de vistas autenticadas"""
        if not value:
            return None
        obj, _ = model.objects.get_or_create(nombre=value, **kwargs)
        return obj

    if request.method == 'POST':
        post = request.POST.copy()
        color_val = post.get('color')
        color_nuevo = post.get('color_nuevo', '').strip()
        motor_val = post.get('motor')
        caja_val = post.get('caja')
        modelo_id = post.get('modelo')
        modelo_obj = None
        nuevo_color_id = None
        if modelo_id and modelo_id.isdigit():
            try:
                modelo_obj = Modelo.objects.get(id=modelo_id)
            except Modelo.DoesNotExist:
                modelo_obj = None
        # Procesar color: si seleccionó 'Agregar nuevo color...', usar el input y evitar duplicados
        if color_val == '__nuevo__' and color_nuevo:
            color_obj, created = ColorVehiculo.objects.get_or_create(nombre=color_nuevo)
            post['color'] = color_obj.pk
            nuevo_color_id = color_obj.pk
        elif color_val and not color_val.isdigit():
            color_obj = get_or_create_fk(ColorVehiculo, color_val)
            post['color'] = color_obj.pk if color_obj else ''
        if motor_val and not motor_val.isdigit() and modelo_obj:
            motor_obj = get_or_create_fk(MotorVehiculo, motor_val, modelo=modelo_obj)
            post['motor'] = motor_obj.pk if motor_obj else ''
        if caja_val and not caja_val.isdigit() and modelo_obj:
            caja_obj = get_or_create_fk(CajaVehiculo, caja_val, modelo=modelo_obj)
            post['caja'] = caja_obj.pk if caja_obj else ''
        form = VehiculoForm(post)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa = empresa  # Asignar empresa del usuario
            vehiculo.save()
            # Siempre redirigir a la lista de vehículos
            return redirect('vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm()
    
    # Filtrar datos solo de la empresa del usuario
    clientes = Cliente.objects.filter(empresa=empresa)
    # Catálogos globales (marcas, modelos, colores son compartidos entre empresas)
    marcas = Marca.objects.all()  # Global: catálogo común
    modelos = Modelo.objects.all()  # Global: catálogo común
    colores = ColorVehiculo.objects.all()  # Global: catálogo común
    return render(request, 'taller/vehiculos/crear_vehiculo.html', {
        'form': form,
        'clientes': clientes,
        'marcas': marcas,
        'modelos': modelos,
        'colores': colores
    })
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from taller.models.clientes import Cliente
from taller.vehiculos.forms import VehiculoForm
from taller.forms.clientes import ClienteForm
from dal import autocomplete

@login_required
def crear_vehiculo_para_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.cliente = cliente  # Asigna automáticamente el cliente
            vehiculo.save()
            messages.success(request, "🚗 Vehículo registrado correctamente.")
            return redirect(' vehiculos:lista_vehiculos', cliente_id=cliente.id)
    else:
        form = VehiculoForm()
        form.fields.pop('cliente', None)  # Oculta cliente en el formulario

    return render(request, 'taller/vehiculos/formulario_vehiculo.html', {
        'form': form,
        'cliente': cliente
    })

def registrar_cliente_y_vehiculo(request):
    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST)
        vehiculo_form = VehiculoForm(request.POST)
        if cliente_form.is_valid() and vehiculo_form.is_valid():
            cliente = cliente_form.save()
            vehiculo = vehiculo_form.save(commit=False)
            vehiculo.cliente = cliente
            vehiculo.save()
            return redirect('vehiculos:lista_vehiculos')  # Ajusta la redirección según tu proyecto
    else:
        cliente_form = ClienteForm()
        vehiculo_form = VehiculoForm()
    return render(request, 'vehiculos/registrar_cliente_y_vehiculo.html', {
        'cliente_form': cliente_form,
        'vehiculo_form': vehiculo_form
    })

def editar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado correctamente 🛠️")
            return redirect('vehiculos:listar_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo)

    return render(request, 'taller/vehiculos/crear_vehiculo.html', {
        'form': form,
        'titulo': 'Editar Vehículo',
        'modo': 'editar'
    })


@login_required
def eliminar_vehiculo(request, vehiculo_id):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    try:
        vehiculo = Vehiculo.objects.get(pk=vehiculo_id, empresa=empresa)  # 🔒 FILTRO EMPRESA
        vehiculo.delete()
        messages.success(request, "Vehículo eliminado correctamente.")
    except Vehiculo.DoesNotExist:
        messages.error(request, "El vehículo no existe o ya fue eliminado.")
    
    return redirect('vehiculos:lista_vehiculos')


def agregar_vehiculo(request):
    return render(request, 'vehiculos/agregar.html')  # ✅ Renderiza la plantilla agregar.html

from taller.models.vehiculos import Vehiculo

@login_required
def lista_vehiculos(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    # Filtrar vehículos solo de la empresa del usuario
    vehiculos = Vehiculo.objects.filter(empresa=empresa).select_related('marca', 'modelo', 'cliente')
    
    # Obtener marcas disponibles según el país
    marcas_disponibles = get_marcas_por_pais(request.user)
    
    # Obtener configuración del país
    config_pais = get_configuracion_pais(empresa)
    
    context = {
        'vehiculos': vehiculos,
        'marcas_disponibles': marcas_disponibles,
        'configuracion_pais': config_pais,
        'es_usa': empresa.pais == 'US',
        'es_chile': empresa.pais == 'CL',
    }
    
    return render(request, 'taller/vehiculos/vehiculos.html', context)

@login_required
def ver_cliente(request, cliente_id):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    # Verificar que el cliente pertenece a la empresa del usuario
    cliente = get_object_or_404(Cliente, id=cliente_id, empresa=empresa)
    # Filtrar vehículos solo de la empresa del usuario
    vehiculos = Vehiculo.objects.filter(cliente=cliente, empresa=empresa)
    return render(request, 'taller/clientes/ver_cliente.html', {
        'cliente': cliente,
        'vehiculos': vehiculos
    })

@login_required
def obtener_modelos(request):
    # Los modelos son globales, pero requieren autenticación
    marca_id = request.GET.get('marca_id')
    modelos = []
    
    if marca_id:
        modelos = list(Modelo.objects.filter(marca_id=marca_id).values('id', 'nombre'))
    
    return JsonResponse(modelos, safe=False)

@login_required
def ver_vehiculo(request, pk):
    from taller.models.vehiculos import Vehiculo
    from django.shortcuts import get_object_or_404, render
    
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    # Filtrar vehículo por empresa para seguridad
    vehiculo = get_object_or_404(Vehiculo, id=pk, empresa=empresa)
    return render(request, 'taller/vehiculos/detalle.html', {'vehiculo': vehiculo})

@login_required
def obtener_modelos_por_marca(request):
    # Los modelos son globales, pero requieren autenticación
    marca_id = request.GET.get('marca_id')
    modelos = []
    if marca_id:
        modelos_qs = Modelo.objects.filter(marca_id=marca_id).order_by('nombre')
        modelos = [{"id": m.pk, "nombre": m.nombre} for m in modelos_qs]
    return JsonResponse(modelos, safe=False)


class MarcaAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Las marcas son globales, pero requieren autenticación
        qs = Marca.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

class ModeloAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Los modelos son globales, pero requieren autenticación
        qs = Modelo.objects.all()
        marca_id = self.forwarded.get('marca', None)
        if marca_id:
            qs = qs.filter(marca_id=marca_id)
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

