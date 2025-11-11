"""
Vistas para crear nuevos motores y cajas dinámicamente
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from taller.models.extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo
from taller.models.modelo import Modelo

# from taller.views_extra.views_utils import get_or_create_empresa

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def crear_motor(request):
    """
    Crear un nuevo motor para un modelo específico
    """
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        modelo_id = data.get("modelo_id")

        if not nombre:
            return JsonResponse({"success": False, "error": "El nombre del motor es requerido"})

        if not modelo_id:
            return JsonResponse({"success": False, "error": "El modelo es requerido"})

        # Verificar que el modelo existe
        try:
            modelo = Modelo.objects.get(id=modelo_id)
        except Modelo.DoesNotExist:
            return JsonResponse({"success": False, "error": "Modelo no encontrado"})

        # Verificar que no existe un motor con el mismo nombre para este modelo específico
        if MotorVehiculo.objects.filter(nombre=nombre, modelos=modelo).exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": f'Ya existe un motor con el nombre "{nombre}" para el modelo {modelo.nombre}',
                }
            )

        # Crear el nuevo motor
        motor = MotorVehiculo.objects.create(nombre=nombre)

        # Asociar el motor al modelo usando la relación ManyToMany
        motor.modelos.add(modelo)

        logger.info(
            f"Motor creado: {nombre} para modelo {modelo.nombre} por usuario {request.user.username}"
        )

        return JsonResponse(
            {
                "success": True,
                "motor_id": motor.id,
                "message": f'Motor "{nombre}" creado exitosamente',
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos JSON inválidos"})
    except Exception as e:
        logger.error(f"Error creando motor: {str(e)}")
        return JsonResponse({"success": False, "error": "Error interno del servidor"})


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def crear_caja(request):
    """
    Crear una nueva caja para un modelo específico
    """
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        modelo_id = data.get("modelo_id")

        if not nombre:
            return JsonResponse({"success": False, "error": "El nombre de la caja es requerido"})

        if not modelo_id:
            return JsonResponse({"success": False, "error": "El modelo es requerido"})

        # Verificar que el modelo existe
        try:
            modelo = Modelo.objects.get(id=modelo_id)
        except Modelo.DoesNotExist:
            return JsonResponse({"success": False, "error": "Modelo no encontrado"})

        # Verificar que no existe una caja con el mismo nombre para este modelo específico
        if CajaVehiculo.objects.filter(nombre=nombre, modelos=modelo).exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": f'Ya existe una caja con el nombre "{nombre}" para el modelo {modelo.nombre}',
                }
            )

        # Crear la nueva caja
        caja = CajaVehiculo.objects.create(nombre=nombre)

        # Asociar la caja al modelo usando la relación ManyToMany
        caja.modelos.add(modelo)

        logger.info(
            f"Caja creada: {nombre} para modelo {modelo.nombre} por usuario {request.user.username}"
        )

        return JsonResponse(
            {
                "success": True,
                "caja_id": caja.id,
                "message": f'Caja "{nombre}" creada exitosamente',
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos JSON inválidos"})
    except Exception as e:
        logger.error(f"Error creando caja: {str(e)}")
        return JsonResponse({"success": False, "error": "Error interno del servidor"})


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def crear_color(request):
    """
    Crear un nuevo color
    """
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()

        if not nombre:
            return JsonResponse({"success": False, "error": "El nombre del color es requerido"})

        # Verificar que no existe un color con el mismo nombre
        if ColorVehiculo.objects.filter(nombre=nombre).exists():
            return JsonResponse({"success": False, "error": "Ya existe un color con este nombre"})

        # Crear el nuevo color
        color = ColorVehiculo.objects.create(nombre=nombre)

        logger.info(f"Color creado: {nombre} por usuario {request.user.username}")

        return JsonResponse(
            {
                "success": True,
                "color_id": color.id,
                "message": f'Color "{nombre}" creado exitosamente',
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos JSON inválidos"})
    except Exception as e:
        logger.error(f"Error creando color: {str(e)}")
        return JsonResponse({"success": False, "error": "Error interno del servidor"})
