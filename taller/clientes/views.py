from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from taller.forms.clientes import ClienteForm
from taller.models.region_ciudad import TallerRegion, TallerCiudad
from django.contrib import messages
from taller.models.clientes import Cliente
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.db.models import Q
from django.contrib.auth.decorators import login_required


@login_required
def lista_clientes(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get("q", "").strip()
    # Filtrar clientes solo de la empresa del usuario
    clientes = Cliente.objects.filter(empresa=empresa)

    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(telefono__icontains=q) |
            Q(email__icontains=q) |
            Q(direccion__icontains=q) |
            Q(ciudad__nombre__icontains=q) |
            Q(region__nombre__icontains=q)
        )

    paginator = Paginator(clientes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "taller/clientes/lista_clientes.html", {
        "page_obj": page_obj,
        "clientes": page_obj,  # <-- Esto permite que el for funcione
        "q": q,
    })


@login_required
def crear_cliente(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        print(f"🔍 POST Data recibido:")
        for key, value in request.POST.items():
            print(f"   {key}: {value}")
        
        print(f"🔍 Form valid: {form.is_valid()}")
        
        if not form.is_valid():
            print(f"❌ Form errors: {form.errors}")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        if form.is_valid():
            try:
                cliente = form.save(commit=False)
                cliente.empresa = empresa  # Asignar empresa del usuario
                print(f"💾 Guardando cliente: {cliente.nombre} {cliente.apellido}")
                print(f"   Empresa: {cliente.empresa}")
                print(f"   Región: {cliente.region}")
                print(f"   Ciudad: {cliente.ciudad}")
                cliente.save()
                print(f"✅ Cliente guardado con ID: {cliente.pk}")
                messages.success(request, '✅ Cliente creado exitosamente.')
                return redirect('clientes:lista_clientes')
            except Exception as e:
                print(f"❌ Error al guardar cliente: {e}")
                messages.error(request, f'Error al guardar cliente: {e}')
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


@login_required
def ver_cliente(request, pk):
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
    cliente = get_object_or_404(Cliente, pk=pk, empresa=empresa)
    return render(request, 'taller/clientes/ver_cliente.html', {'cliente': cliente})


def api_ciudades(request):
    region_id = request.GET.get('region_id')
    print(f"🔍 API Ciudades - region_id recibido: {region_id}")
    ciudades = []
    if region_id:
        try:
            ciudades_qs = TallerCiudad.objects.filter(region_id=region_id).order_by('nombre')
            ciudades = [{"id": c.pk, "nombre": c.nombre} for c in ciudades_qs]
            print(f"✅ Ciudades encontradas: {len(ciudades)}")
        except Exception as e:
            print(f"❌ Error en API ciudades: {e}")
    else:
        print("⚠️ No se proporcionó region_id")
    return JsonResponse({"ciudades": ciudades})


@require_GET
@login_required
def ajax_buscar_clientes(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get("q", "").strip()
    # Filtrar solo clientes de la empresa del usuario
    clientes = Cliente.objects.filter(empresa=empresa)
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(telefono__icontains=q) |
            Q(email__icontains=q) |
            Q(direccion__icontains=q) |
            Q(ciudad__nombre__icontains=q) |
            Q(region__nombre__icontains=q)
        )
    paginator = Paginator(clientes, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    html = render_to_string("taller/clientes/_tabla_clientes.html", {"clientes": page_obj})
    return JsonResponse({"html": html})
