"""
🎯 VISTAS AJAX: Sistema Jerárquico de Formularios de Vehículos
📅 Diciembre 2024
🔧 Propósito: Proporcionar endpoints para cargar datos dinámicamente en formularios

Endpoints disponibles:
1. load_modelos: Carga modelos basado en marca seleccionada
2. load_motores: Carga motores basado en modelo seleccionado  
3. load_cajas: Carga cajas basado en modelo seleccionado
4. load_motores_cajas: Carga motores Y cajas en una sola llamada
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo


@require_GET
def load_modelos(request):
    """
    Carga modelos basado en la marca seleccionada
    
    Parámetros:
    - marca_id: ID de la marca seleccionada
    
    Retorna:
    - JSON con lista de modelos [{"id": int, "nombre": str}, ...]
    """
    marca_id = request.GET.get('marca_id')
    
    if not marca_id:
        return JsonResponse([], safe=False)
    
    try:
        marca = get_object_or_404(Marca, id=marca_id)
        modelos = Modelo.objects.filter(marca=marca).order_by('nombre')
        
        data = [
            {
                'id': modelo.id,
                'nombre': modelo.nombre,
                'country': modelo.country
            }
            for modelo in modelos
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)


@require_GET
def load_motores(request):
    """
    Carga motores basado en el modelo seleccionado
    
    Parámetros:
    - modelo_id: ID del modelo seleccionado
    
    Retorna:
    - JSON con lista de motores [{"id": int, "nombre": str}, ...]
    """
    modelo_id = request.GET.get('modelo_id')
    
    if not modelo_id:
        return JsonResponse([], safe=False)
    
    try:
        modelo = get_object_or_404(Modelo, id=modelo_id)
        motores = MotorVehiculo.objects.filter(modelo=modelo).order_by('nombre')
        
        data = [
            {
                'id': motor.id,
                'nombre': motor.nombre,
                'country': motor.country
            }
            for motor in motores
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)


@require_GET
def load_cajas(request):
    """
    Carga cajas basado en el modelo seleccionado
    
    Parámetros:
    - modelo_id: ID del modelo seleccionado
    
    Retorna:
    - JSON con lista de cajas [{"id": int, "nombre": str}, ...]
    """
    modelo_id = request.GET.get('modelo_id')
    
    if not modelo_id:
        return JsonResponse([], safe=False)
    
    try:
        modelo = get_object_or_404(Modelo, id=modelo_id)
        cajas = CajaVehiculo.objects.filter(modelo=modelo).order_by('nombre')
        
        data = [
            {
                'id': caja.id,
                'nombre': caja.nombre,
                'country': caja.country
            }
            for caja in cajas
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)


@require_GET
def load_motores_cajas(request):
    """
    Carga motores Y cajas basado en el modelo seleccionado (endpoint combinado)
    
    Parámetros:
    - modelo_id: ID del modelo seleccionado
    
    Retorna:
    - JSON con {"motores": [...], "cajas": [...]}
    """
    modelo_id = request.GET.get('modelo_id')
    
    if not modelo_id:
        return JsonResponse({'motores': [], 'cajas': []})
    
    try:
        modelo = get_object_or_404(Modelo, id=modelo_id)
        
        # Obtener motores
        motores = MotorVehiculo.objects.filter(modelo=modelo).order_by('nombre')
        motores_data = [
            {
                'id': motor.id,
                'nombre': motor.nombre,
                'country': motor.country
            }
            for motor in motores
        ]
        
        # Obtener cajas
        cajas = CajaVehiculo.objects.filter(modelo=modelo).order_by('nombre')
        cajas_data = [
            {
                'id': caja.id,
                'nombre': caja.nombre,
                'country': caja.country
            }
            for caja in cajas
        ]
        
        return JsonResponse({
            'motores': motores_data,
            'cajas': cajas_data
        })
        
    except Exception as e:
        return JsonResponse({'motores': [], 'cajas': []})
