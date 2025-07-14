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

def ver_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
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

