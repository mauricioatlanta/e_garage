# --- API para marcas ---
from taller.models.marca import Marca
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages

def api_marcas(request):
    """
    API para obtener marcas disponibles
    BLINDAJE MULTI-TENANT: Verificar autenticación
    """
    # BLINDAJE: Verificar autenticación del usuario
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    
    # Las marcas pueden ser globales, pero verificamos autenticación
    marcas = list(Marca.objects.values('id', 'nombre'))
    return JsonResponse(marcas, safe=False)

import logging
from .views_cbv import (
    VehiculoListView, VehiculoDetailView, VehiculoCreateView, VehiculoUpdateView
)
from django.views.generic import DeleteView
from taller.models.vehiculos import Vehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.extras_vehiculo import ColorVehiculo
from .forms import VehiculoForm
from taller.models.clientes import Cliente
from taller.models.vehiculos import ColorVehiculo

# Importar modelos del catálogo
try:
    from taller.models.catalogo import CatalogoModeloAuto
except ImportError:
    CatalogoModeloAuto = None

try:
    from taller.models.marcas_usa import MarcaVehiculo as MarcaUSA
except ImportError:
    MarcaUSA = None

log = logging.getLogger(__name__)

def lista_vehiculos(request, *args, **kwargs):
    log.info("FBV shim: lista_vehiculos")
    return VehiculoListView.as_view()(request, *args, **kwargs)

def ver_vehiculo(request, *args, **kwargs):
    log.info("FBV shim: ver_vehiculo")
    return VehiculoDetailView.as_view()(request, *args, **kwargs)

@login_required
def crear_vehiculo(request):
    """Vista para creación de vehículos usando formulario"""
    empresa = getattr(request.user, "empresa", None)

    if request.method == "POST":
        print('POST VEHICULO:', request.POST.dict())
        print('Campos recibidos:', list(request.POST.keys()))
        
        # Verificar campos requeridos para Chile
        required_fields = ['cliente', 'marca', 'modelo', 'anio', 'patente']
        missing_fields = [field for field in required_fields if field not in request.POST]
        if missing_fields:
            print('❌ Campos faltantes:', missing_fields)
        
        form = VehiculoForm(request.POST, user=request.user)
        print(f'Formulario válido: {form.is_valid()}')
        
        if form.is_valid():
            print('✅ Formulario válido, guardando...')
            vehiculo = form.save(commit=False)
            # 🔒 Consistencia multi-tenant
            vehiculo.empresa = empresa
            vehiculo.save()
            form.save_m2m()
            messages.success(request, "Vehículo creado correctamente.")
            print(f'✅ Vehículo guardado exitosamente - ID: {vehiculo.pk}')
            # ✅ Redirigir a la lista
            return redirect("taller:vehiculos:lista_vehiculos")
        else:
            print('❌ ERRORES FORM:', form.errors.as_json())
            print('❌ Errores por campo:')
            for field, errors in form.errors.items():
                print(f'  {field}: {errors}')
            messages.error(request, "Revisa los errores del formulario.")
    else:
        form = VehiculoForm(user=request.user)

        # Detectar país del usuario
    raw_country = getattr(empresa, 'pais', None) or 'CL'
    country = str(raw_country).strip().upper()
    
    if country not in ('CL', 'US'):
        log.warning("[crear_vehiculo] country desconocido '%s' normalizado a 'CL'", country)
        country = 'CL'
    
    # Contexto base
    ctx = {
        'form': form,
        'clientes': Cliente.objects.filter(empresa=empresa).order_by("nombre"),
        'country': country,
        'SHOW_DEBUG': True,
        'debug_empresa_pais': f"empresa={getattr(empresa,'id',None)} pais={country} usuario={request.user.username}",
    }
    
    # Contexto específico por país
    if country == 'US':
        # Usar nuestro catálogo importado para USA
        if CatalogoModeloAuto:
            ctx['marcas_usa'] = CatalogoModeloAuto.get_marcas_activas()[:500]
            ctx['usa_catalogo_disponible'] = True
        elif MarcaUSA:
            ctx['marcas_usa'] = MarcaUSA.objects.filter(activa=True).order_by('nombre')[:500]
    else:
        # Chile - usar modelos tradicionales  
        ctx['marcas'] = Marca.objects.filter(country='CL').order_by('nombre')
        ctx['colores'] = ColorVehiculo.get_colores_para_pais(country)

    return render(request, 'taller/vehiculos/crear_vehiculo.html', ctx)


def _render_form_with_context(request, form, country, empresa):
    """Helper para renderizar el formulario con el contexto adecuado"""
    SHOW_DEBUG = True
    
    # Contexto base
    ctx = {
        'country': country,
        'SHOW_DEBUG': SHOW_DEBUG,
        'debug_empresa_pais': f"empresa={getattr(empresa,'id',None)} pais={country} usuario={request.user.username}",
        'clientes': Cliente.objects.filter(empresa=empresa)[:500],  # BLINDAJE: Filtrado por empresa
        'colores': ColorVehiculo.get_colores_para_pais(country),  # CORREGIDO: Colores por país
        'form': form,
    }
    
    # Contexto específico por país
    if country == 'US':
        # Usar nuestro catálogo importado para USA
        if CatalogoModeloAuto:
            ctx['marcas_usa'] = CatalogoModeloAuto.get_marcas_activas()[:500]
            ctx['usa_catalogo_disponible'] = True
        elif MarcaUSA:
            ctx['marcas_usa'] = MarcaUSA.objects.filter(activa=True).order_by('nombre')[:500]
    else:
        # Chile - usar modelos tradicionales  
        ctx['marcas'] = Marca.objects.filter(country='CL').order_by('nombre')

    return render(request, 'taller/vehiculos/crear_vehiculo.html', ctx)

def editar_vehiculo(request, *args, **kwargs):
    log.info("FBV shim: editar_vehiculo")
    
    # Obtener empresa del usuario para detectar país
    empresa = getattr(request.user, "empresa", None)
    raw_country = getattr(empresa, 'pais', None) or 'CL'
    country = str(raw_country).strip().upper()
    
    if country not in ('CL', 'US'):
        log.warning("[editar_vehiculo] country desconocido '%s' normalizado a 'CL'", country)
        country = 'CL'
    
    # 🔴 REDIRIGIR A LA VISTA ESPECÍFICA SEGÚN EL PAÍS
    if country == 'US':
        from taller.vehiculos.views_usa import editar_vehiculo as editar_vehiculo_usa
        return editar_vehiculo_usa(request, **kwargs)
    else:
        # Normalizar nombre de argumento a 'pk' para compatibilidad con UpdateView
        vehiculo_id = kwargs.pop('vehiculo_id', None)
        if vehiculo_id is not None:
            kwargs['pk'] = vehiculo_id
        return VehiculoUpdateView.as_view()(request, *args, **kwargs)


def eliminar_vehiculo(request, vehiculo_id, *args, **kwargs):
    log.info("FBV shim: eliminar_vehiculo")
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    if request.method == "POST":
        vehiculo.delete()
        messages.success(request, f"Vehículo {vehiculo.patente} eliminado correctamente.")
        # Redirigir a la lista de vehículos después de eliminar
        return redirect("vehiculos:lista_vehiculos")
    # Si no es POST, mostrar template de confirmación
    return render(request, 'taller/vehiculos/eliminar_confirmar.html', {'object': vehiculo})


# --- API para búsqueda de clientes ---
from django.http import JsonResponse
from taller.models.clientes import Cliente
from django.db import models

def api_busqueda_clientes(request):
    """
    Endpoint simple para buscar clientes por nombre, apellido, email o teléfono.
    Parámetro GET: q (query de búsqueda)
    BLINDAJE MULTI-TENANT: Solo clientes de la empresa del usuario
    """
    # BLINDAJE MULTI-TENANT: Verificar autenticación y empresa
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    
    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        return JsonResponse([], safe=False)
    
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
        
    # BLINDAJE: Filtrar SOLO por empresa del usuario
    clientes = Cliente.objects.filter(
        empresa=empresa
    ).filter(
        models.Q(nombre__icontains=q) |
        models.Q(apellido__icontains=q) |
        models.Q(email__icontains=q) |
        models.Q(telefono__icontains=q)
    )[:20]
    
    data = [
        {
            "id": c.pk,
            "nombre": c.nombre,
            "apellido": c.apellido,
            "email": c.email,
            "telefono": c.telefono,
        }
        for c in clientes
    ]
    return JsonResponse(data, safe=False)


def api_modelos_usa(request):
    """API para cargar modelos USA basados en marca seleccionada"""
    marca = request.GET.get('marca', '').strip()
    if not marca:
        return JsonResponse({'results': []})
    
    try:
        if CatalogoModeloAuto:
            # Usar catálogo importado
            modelos = CatalogoModeloAuto.get_modelos_por_marca(marca)
            results = [{'id': modelo, 'text': modelo} for modelo in modelos]
        else:
            # Fallback sin catálogo
            results = []
        
        return JsonResponse({'results': results})
    except Exception as e:
        log.error(f"Error en api_modelos_usa: {e}")
        return JsonResponse({'results': [], 'error': str(e)})

