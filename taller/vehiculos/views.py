# --- API para marcas ---
from taller.models.marca import Marca
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages

def api_marcas(request):
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
@transaction.atomic
def crear_vehiculo(request):
    """Vista unificada country-aware para creación de vehículos"""
    # Detectar país del usuario
    empresa = getattr(request.user, 'empresa', None)
    raw_country = getattr(empresa, 'pais', None) or 'CL'
    country = str(raw_country).strip().upper()
    
    # Flag de diagnóstico para forzar USA (solo staff & DEBUG)
    if request.GET.get('force_us') == '1' and request.user.is_staff:
        log.warning("[FORCE_US] Forzando country=US para usuario=%s (valor real=%s)", request.user.username, country)
        country = 'US'

    if country not in ('CL', 'US'):
        log.warning("[crear_vehiculo] country desconocido '%s' normalizado a 'CL' (usuario=%s, empresa=%s)", 
                   country, request.user.username, getattr(empresa,'id',None))
        country = 'CL'
    
    SHOW_DEBUG = True
    
    # Banner de confirmación - LOG IMPORTANTE
    print('[DEBUG crear_vehiculo] user=', request.user.username, 
          'empresa_pais=', getattr(request.user.empresa, 'pais', None),
          'country_ctx=', country)
    
    if request.method == 'POST':
        form = VehiculoForm(user=request.user, data=request.POST)
        if form.is_valid():
            # Guardar sin commit para poder asignar FKs
            vehiculo = form.save(commit=False)
            
            # 1) Obtener el nombre de la marca desde los campos USA o fallback
            marca_name = (request.POST.get('marca_usa') or request.POST.get('marca') or '').strip()
            if not marca_name:
                form.add_error('marca_usa', 'Selecciona una marca')
                return _render_form_with_context(request, form, country, empresa)
            
            # 2) Resolver/crear la Marca para el país actual
            country_code = 'US' if country == 'US' else 'CL'
            try:
                marca_obj = Marca.objects.get(nombre__iexact=marca_name, country=country_code)
            except Marca.DoesNotExist:
                marca_obj = Marca.objects.create(nombre=marca_name, country=country_code)
                log.info(f"Marca creada: {marca_obj.nombre} para país {country_code}")
            
            # 3) Asignar la FK de marca
            vehiculo.marca = marca_obj
            
            # 4) Resolver/crear el Modelo si se proporcionó
            modelo_name = (request.POST.get('modelo_usa') or request.POST.get('modelo') or '').strip()
            if modelo_name:
                try:
                    modelo_obj = Modelo.objects.get(nombre__iexact=modelo_name, marca=marca_obj)
                except Modelo.DoesNotExist:
                    modelo_obj = Modelo.objects.create(
                        nombre=modelo_name, 
                        marca=marca_obj,
                        country=country_code
                    )
                    log.info(f"Modelo creado: {modelo_obj.nombre} para marca {marca_obj.nombre}")
                vehiculo.modelo = modelo_obj
            
            # 5) Resolver/crear el Color si se proporcionó
            color_id = request.POST.get('color', '').strip()
            if color_id == '__nuevo__':
                # Usuario seleccionó "Agregar nuevo color"
                color_nuevo = request.POST.get('color_nuevo', '').strip()
                if color_nuevo:
                    color_obj, created = ColorVehiculo.objects.get_or_create(
                        nombre=color_nuevo,
                        defaults={'nombre': color_nuevo}
                    )
                    vehiculo.color = color_obj
                    if created:
                        log.info(f"Color creado: {color_obj.nombre}")
            elif color_id:
                # Usuario seleccionó un color existente
                try:
                    color_obj = ColorVehiculo.objects.get(id=color_id)
                    vehiculo.color = color_obj
                except ColorVehiculo.DoesNotExist:
                    log.warning(f"Color con ID {color_id} no encontrado")
            
            # 6) Asignar empresa si no viene del form
            if empresa:
                vehiculo.empresa = empresa
            
            # 7) Guardar el vehículo
            vehiculo.save()
            log.info(f"Vehículo creado: {vehiculo}")
            
            return redirect('taller:vehiculos:lista_vehiculos')
        else:
            # Errores de formulario
            return _render_form_with_context(request, form, country, empresa)
    
    else:
        # GET request - crear formulario nuevo
        form = VehiculoForm(user=request.user)
        return _render_form_with_context(request, form, country, empresa)


def _render_form_with_context(request, form, country, empresa):
    """Helper para renderizar el formulario con el contexto adecuado"""
    SHOW_DEBUG = True
    
    # Contexto base
    ctx = {
        'country': country,
        'SHOW_DEBUG': SHOW_DEBUG,
        'debug_empresa_pais': f"empresa={getattr(empresa,'id',None)} pais={country} usuario={request.user.username}",
        'clientes': Cliente.objects.all()[:500],
        'colores': ColorVehiculo.objects.all(),
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
    """
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
    clientes = Cliente.objects.filter(
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

