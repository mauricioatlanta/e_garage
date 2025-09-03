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
@transaction.atomic
def crear_vehiculo(request):
    """Vista simplificada para creación de vehículos"""
    from taller.models.vehiculos import Vehiculo
    
    # Detectar país del usuario
    empresa = getattr(request.user, 'empresa', None)
    raw_country = getattr(empresa, 'pais', None) or 'CL'
    country = str(raw_country).strip().upper()
    
    if country not in ('CL', 'US'):
        log.warning("[crear_vehiculo] country desconocido '%s' normalizado a 'CL'", country)
        country = 'CL'
    
    print('[DEBUG crear_vehiculo] user=', request.user.username, 
          'empresa_pais=', getattr(request.user.empresa, 'pais', None),
          'country_ctx=', country)
    
    if request.method == 'POST':
        print('[DEBUG POST] Datos recibidos:')
        for key, value in request.POST.items():
            print(f'  {key}: {value}')
        
        try:
            # Crear vehículo directamente con los datos del POST
            vehiculo = Vehiculo()
            
            # Cliente (requerido)
            cliente_id = request.POST.get('cliente')
            if not cliente_id:
                messages.error(request, 'Debe seleccionar un cliente')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            try:
                vehiculo.cliente = Cliente.objects.get(id=cliente_id, empresa=empresa)
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente no válido')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            # Marca (requerida)
            marca_id = request.POST.get('marca')
            if not marca_id:
                messages.error(request, 'Debe seleccionar una marca')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            try:
                vehiculo.marca = Marca.objects.get(id=marca_id)
            except Marca.DoesNotExist:
                messages.error(request, 'Marca no válida')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            # Modelo (requerido)
            modelo_id = request.POST.get('modelo')
            if not modelo_id:
                messages.error(request, 'Debe seleccionar un modelo')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            try:
                vehiculo.modelo = Modelo.objects.get(id=modelo_id, marca=vehiculo.marca)
            except Modelo.DoesNotExist:
                messages.error(request, 'Modelo no válido')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            # Color (requerido)
            color_id = request.POST.get('color')
            if not color_id:
                messages.error(request, 'Debe seleccionar un color')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            if color_id == '__nuevo__':
                # Crear nuevo color
                color_nuevo = request.POST.get('color_nuevo', '').strip()
                if not color_nuevo:
                    messages.error(request, 'Debe especificar el nombre del nuevo color')
                    form = VehiculoForm(user=request.user)
                    return _render_form_with_context(request, form, country, empresa)
                
                color_obj, created = ColorVehiculo.objects.get_or_create(
                    nombre=color_nuevo,
                    defaults={'nombre': color_nuevo}
                )
                vehiculo.color = color_obj
                if created:
                    log.info(f"Color creado: {color_obj.nombre}")
            else:
                try:
                    vehiculo.color = ColorVehiculo.objects.get(id=color_id)
                except ColorVehiculo.DoesNotExist:
                    messages.error(request, 'Color no válido')
                    form = VehiculoForm(user=request.user)
                    return _render_form_with_context(request, form, country, empresa)
            
            # Patente (requerida)
            patente = request.POST.get('patente', '').strip()
            if not patente:
                messages.error(request, 'Debe especificar la patente')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            vehiculo.patente = patente
            
            # Año (requerido)
            anio = request.POST.get('anio')  # Corregido: 'anio' en lugar de 'ano'
            if not anio:
                messages.error(request, 'Debe seleccionar el año')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            try:
                vehiculo.anio = int(anio)  # Corregido: 'anio' en lugar de 'ano'
            except ValueError:
                messages.error(request, 'Año no válido')
                form = VehiculoForm(user=request.user)
                return _render_form_with_context(request, form, country, empresa)
            
            # Campos opcionales
            vehiculo.vin = request.POST.get('vin', '').strip()
            # Eliminado 'observaciones' - no existe en el modelo Vehiculo
            
            # Motor (opcional)
            motor_id = request.POST.get('motor')
            if motor_id and motor_id != '':
                try:
                    from taller.models.extras_vehiculo import MotorVehiculo
                    vehiculo.motor = MotorVehiculo.objects.get(id=motor_id)
                except:
                    pass  # Motor es opcional
            
            # Caja (opcional)
            caja_id = request.POST.get('caja')
            if caja_id and caja_id != '':
                try:
                    from taller.models.extras_vehiculo import CajaVehiculo
                    vehiculo.caja = CajaVehiculo.objects.get(id=caja_id)
                except:
                    pass  # Caja es opcional
            
            # Asignar empresa
            vehiculo.empresa = empresa
            
            # Guardar vehículo
            vehiculo.save()
            
            messages.success(request, f'Vehículo {vehiculo.patente} creado exitosamente')
            log.info(f"Vehículo creado: {vehiculo}")
            
            return redirect('taller:vehiculos:lista_vehiculos')
            
        except Exception as e:
            log.error(f"Error creando vehículo: {e}")
            messages.error(request, f'Error al crear el vehículo: {str(e)}')
            form = VehiculoForm(user=request.user)
            return _render_form_with_context(request, form, country, empresa)
    
    else:
        # GET request - mostrar formulario
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

