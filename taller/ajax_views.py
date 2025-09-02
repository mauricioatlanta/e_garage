from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
@require_http_methods(["GET"])
def ajax_marcas(request):
    """Endpoint AJAX para obtener marcas de vehículos desde la base de datos"""
    try:
        from taller.models.marca import Marca
        
        # Obtener marcas de la base de datos ordenadas alfabéticamente
        marcas_qs = Marca.objects.filter(country='CL').order_by('nombre')
        
        marcas = [
            {'id': marca.id, 'nombre': marca.nombre}
            for marca in marcas_qs
        ]
        
        return JsonResponse({
            'success': True,
            'marcas': marcas
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_modelos(request):
    """Endpoint AJAX para obtener modelos según marca desde la base de datos"""
    try:
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo
        
        marca_id = request.GET.get('marca_id', '')
        
        if not marca_id:
            return JsonResponse([])
        
        # Si marca_id es un nombre de marca (string), buscar por nombre
        if isinstance(marca_id, str) and not marca_id.isdigit():
            try:
                marca = Marca.objects.get(nombre=marca_id, country='CL')
                marca_id = marca.id
            except Marca.DoesNotExist:
                return JsonResponse([])
        
        # Obtener modelos de la base de datos
        modelos_qs = Modelo.objects.filter(
            marca_id=marca_id,
            country='CL'
        ).order_by('nombre')
        
        modelos = [
            {'id': modelo.id, 'nombre': modelo.nombre}
            for modelo in modelos_qs
        ]
        
        return JsonResponse({
            'success': True,
            'modelos': modelos
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_motores(request):
    """Endpoint AJAX para obtener tipos de motor"""
    try:
        motores = [
            {'id': '1.0L', 'nombre': '1.0L'},
            {'id': '1.2L', 'nombre': '1.2L'},
            {'id': '1.4L', 'nombre': '1.4L'},
            {'id': '1.6L', 'nombre': '1.6L'},
            {'id': '1.8L', 'nombre': '1.8L'},
            {'id': '2.0L', 'nombre': '2.0L'},
            {'id': '2.4L', 'nombre': '2.4L'},
            {'id': '2.5L', 'nombre': '2.5L'},
            {'id': '3.0L V6', 'nombre': '3.0L V6'},
            {'id': '3.5L V6', 'nombre': '3.5L V6'},
            {'id': '4.0L V6', 'nombre': '4.0L V6'},
            {'id': '5.0L V8', 'nombre': '5.0L V8'},
            {'id': '1.6L Turbo', 'nombre': '1.6L Turbo'},
            {'id': '2.0L Turbo', 'nombre': '2.0L Turbo'},
            {'id': 'Híbrido', 'nombre': 'Híbrido'},
            {'id': 'Eléctrico', 'nombre': 'Eléctrico'},
            {'id': 'Diesel 2.0L', 'nombre': 'Diesel 2.0L'},
            {'id': 'Diesel 2.5L', 'nombre': 'Diesel 2.5L'},
        ]
        
        return JsonResponse({
            'success': True,
            'motores': motores
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_cajas(request):
    """Endpoint AJAX para obtener tipos de caja de cambios"""
    try:
        cajas = [
            {'id': 'Manual 5 velocidades', 'nombre': 'Manual 5 velocidades'},
            {'id': 'Manual 6 velocidades', 'nombre': 'Manual 6 velocidades'},
            {'id': 'Automática 4 velocidades', 'nombre': 'Automática 4 velocidades'},
            {'id': 'Automática 5 velocidades', 'nombre': 'Automática 5 velocidades'},
            {'id': 'Automática 6 velocidades', 'nombre': 'Automática 6 velocidades'},
            {'id': 'Automática 8 velocidades', 'nombre': 'Automática 8 velocidades'},
            {'id': 'Automática CVT', 'nombre': 'Automática CVT'},
            {'id': 'Secuencial', 'nombre': 'Secuencial'},
            {'id': 'Tiptronic', 'nombre': 'Tiptronic'},
            {'id': 'DSG', 'nombre': 'DSG'},
            {'id': 'PDK', 'nombre': 'PDK'},
        ]
        
        return JsonResponse({
            'success': True,
            'cajas': cajas
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# =============================================================================
# FUNCIONES DE COMPATIBILIDAD PARA URLs ANTIGUAS
# =============================================================================

def load_modelos(request):
    """Función de compatibilidad para URLs antiguas que usan load_modelos"""
    return ajax_modelos(request)

def load_marcas(request):
    """Función de compatibilidad para URLs antiguas que usan load_marcas"""
    return ajax_marcas(request)

def load_motores(request):
    """Función de compatibilidad para URLs antiguas que usan load_motores"""
    return ajax_motores(request)

def load_cajas(request):
    """Función de compatibilidad para URLs antiguas que usan load_cajas"""
    return ajax_cajas(request)

def load_motores_cajas(request):
    """Función de compatibilidad que combina motores y cajas en una respuesta"""
    try:
        # Obtener datos de motores
        motores_response = ajax_motores(request)
        motores_data = json.loads(motores_response.content.decode('utf-8'))
        
        # Obtener datos de cajas
        cajas_response = ajax_cajas(request)
        cajas_data = json.loads(cajas_response.content.decode('utf-8'))
        
        # Combinar respuestas
        return JsonResponse({
            'success': True,
            'motores': motores_data.get('motores', []),
            'cajas': cajas_data.get('cajas', [])
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
