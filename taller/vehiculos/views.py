from django.shortcuts import render, redirect
from taller.vehiculos.forms import VehiculoForm
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo
from taller.models.modelo import Modelo

def crear_vehiculo(request):
    def get_or_create_fk(model, value, **kwargs):
        if not value:
            return None
        obj, _ = model.objects.get_or_create(nombre=value, **kwargs)
        return obj

    if request.method == 'POST':
        post = request.POST.copy()
        color_val = post.get('color')
        motor_val = post.get('motor')
        caja_val = post.get('caja')
        modelo_id = post.get('modelo')
        modelo_obj = None
        if modelo_id and modelo_id.isdigit():
            try:
                modelo_obj = Modelo.objects.get(id=modelo_id)
            except Modelo.DoesNotExist:
                modelo_obj = None
        if color_val and not color_val.isdigit():
            color_obj = get_or_create_fk(ColorVehiculo, color_val)
            post['color'] = color_obj.id
        if motor_val and not motor_val.isdigit() and modelo_obj:
            motor_obj = get_or_create_fk(MotorVehiculo, motor_val, modelo=modelo_obj)
            post['motor'] = motor_obj.id
        if caja_val and not caja_val.isdigit() and modelo_obj:
            caja_obj = get_or_create_fk(CajaVehiculo, caja_val, modelo=modelo_obj)
            post['caja'] = caja_obj.id
        form = VehiculoForm(post)
        if form.is_valid():
            form.save()
            return redirect('vehiculos:lista_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'taller/vehiculos/crear_vehiculo.html', {'form': form})
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from taller.models.clientes import Cliente
from taller.vehiculos.forms import VehiculoForm
from taller.forms.clientes import ClienteForm
from dal import autocomplete

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


def eliminar_vehiculo(request, vehiculo_id):
    try:
        vehiculo = Vehiculo.objects.get(pk=vehiculo_id)
        vehiculo.delete()
        messages.success(request, "Vehículo eliminado correctamente.")
    except Vehiculo.DoesNotExist:
        messages.error(request, "El vehículo no existe o ya fue eliminado.")
    
    return redirect('vehiculos:lista_vehiculos')


def agregar_vehiculo(request):
    return render(request, 'vehiculos/agregar.html')  # ✅ Renderiza la plantilla agregar.html

from taller.models.vehiculos import Vehiculo

def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.all().select_related('marca', 'modelo', 'cliente')
    return render(request, 'taller/vehiculos/vehiculos.html', {'vehiculos': vehiculos})

def ver_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    vehiculos = Vehiculo.objects.filter(cliente=cliente)
    return render(request, 'taller/clientes/ver_cliente.html', {
        'cliente': cliente,
        'vehiculos': vehiculos
    })

def obtener_modelos(request):
    marca_id = request.GET.get('marca_id')
    modelos = []
    
    if marca_id:
        modelos = list(Modelo.objects.filter(marca_id=marca_id).values('id', 'nombre'))
    
    return JsonResponse(modelos, safe=False)

def ver_vehiculo(request, pk):
    from taller.models.vehiculos import Vehiculo
    from django.shortcuts import get_object_or_404, render
    vehiculo = get_object_or_404(Vehiculo, id=pk)
    return render(request, 'taller/vehiculos/detalle.html', {'vehiculo': vehiculo})


def obtener_modelos_por_marca(request):
    marca_id = request.GET.get('marca_id')
    modelos = []
    if marca_id:
        modelos_qs = Modelo.objects.filter(marca_id=marca_id).order_by('nombre')
        modelos = [{"id": m.pk, "nombre": m.nombre} for m in modelos_qs]
    return JsonResponse(modelos, safe=False)


class MarcaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Marca.objects.all()
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

class ModeloAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Modelo.objects.all()
        marca_id = self.forwarded.get('marca', None)
        if marca_id:
            qs = qs.filter(marca_id=marca_id)
        if self.q:
            qs = qs.filter(nombre__icontains=self.q)
        return qs

