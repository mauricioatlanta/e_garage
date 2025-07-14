from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from taller.forms.clientes import ClienteForm
from taller.models.clientes import Cliente
from taller.models.region_ciudad import TallerRegion, TallerCiudad
from django.contrib import messages
from taller.vehiculos.forms import VehiculoForm

def lista_clientes(request):
    q = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all()

    if q:
        clientes = clientes.filter(nombre__icontains=q) | clientes.filter(apellido__icontains=q)

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "taller/clientes/lista_clientes.html", {
        "page_obj": page_obj,
        "clientes": page_obj,
        "q": q,
    })

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Cliente creado exitosamente.')
            return redirect('clientes:lista_clientes')
    else:
        form = ClienteForm()

    return render(request, 'taller/clientes/crear_cliente.html', {
        'form': form,
    })

def obtener_ciudades(request):
    region_id = request.GET.get("region_id")
    ciudades = TallerCiudad.objects.filter(region_id=region_id).values("id", "nombre")
    return JsonResponse(list(ciudades), safe=False)

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Cliente actualizado exitosamente.')
            return redirect('clientes:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'taller/clientes/editar_cliente.html', {
        'form': form,
        'cliente': cliente,
    })

def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.delete()
    messages.success(request, '🗑️ Cliente eliminado exitosamente.')
    return redirect('clientes:lista_clientes')

def ver_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'taller/clientes/ver_cliente.html', {'cliente': cliente})

def api_ciudades(request):
    region_id = request.GET.get('region_id')
    ciudades = []
    if region_id:
        ciudades_qs = TallerCiudad.objects.filter(region_id=region_id).order_by('nombre')
        ciudades = [{"id": c.id, "nombre": c.nombre} for c in ciudades_qs]
    return JsonResponse({"ciudades": ciudades})

def obtener_modelos_por_marca(request):
    marca_id = request.GET.get('marca_id')
    modelos = []
    if marca_id:
        modelos_qs = Modelo.objects.filter(marca_id=marca_id).order_by('nombre')
        modelos = [{"id": m.id, "nombre": m.nombre} for m in modelos_qs]
    return JsonResponse(modelos, safe=False)

def test_autocomplete_minimal(request):
    form = VehiculoForm()
    return render(request, 'taller/vehiculos/test_autocomplete_minimal.html', {'form': form})

