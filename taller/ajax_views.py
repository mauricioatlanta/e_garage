from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from taller.models.marca import Marca


@login_required
@require_http_methods(["GET"])
def ajax_marcas(request):
    """Endpoint AJAX para obtener marcas de vehículos"""
    try:
        # Obtener país del usuario desde el middleware
        country = getattr(request, "country", "CL")

        # Obtener marcas de la base de datos ordenadas alfabéticamente
        marcas_db = Marca.objects.filter(country=country)

        # Convertir a formato esperado por el frontend
        marcas = []
        for marca in marcas_db:
            marcas.append(
                {
                    "id": marca.nombre,  # Frontend espera nombre como ID
                    "nombre": marca.nombre,
                }
            )

        return JsonResponse({"success": True, "marcas": marcas})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_modelos(request):
    """Endpoint AJAX para obtener modelos según marca"""
    try:
        marca_id = request.GET.get("marca_id", "")

        # Modelos predefinidos por marca
        modelos_por_marca = {
            "Toyota": [
                {"id": "Corolla", "nombre": "Corolla"},
                {"id": "Yaris", "nombre": "Yaris"},
                {"id": "Hilux", "nombre": "Hilux"},
                {"id": "RAV4", "nombre": "RAV4"},
                {"id": "Camry", "nombre": "Camry"},
                {"id": "Prius", "nombre": "Prius"},
                {"id": "Land Cruiser", "nombre": "Land Cruiser"},
            ],
            "Ford": [
                {"id": "Fiesta", "nombre": "Fiesta"},
                {"id": "Focus", "nombre": "Focus"},
                {"id": "Ranger", "nombre": "Ranger"},
                {"id": "EcoSport", "nombre": "EcoSport"},
                {"id": "Escape", "nombre": "Escape"},
                {"id": "Mustang", "nombre": "Mustang"},
                {"id": "F-150", "nombre": "F-150"},
            ],
            "Chevrolet": [
                {"id": "Spark", "nombre": "Spark"},
                {"id": "Sail", "nombre": "Sail"},
                {"id": "Cruze", "nombre": "Cruze"},
                {"id": "Captiva", "nombre": "Captiva"},
                {"id": "Camaro", "nombre": "Camaro"},
                {"id": "Silverado", "nombre": "Silverado"},
            ],
            "Hyundai": [
                {"id": "Accent", "nombre": "Accent"},
                {"id": "Elantra", "nombre": "Elantra"},
                {"id": "Tucson", "nombre": "Tucson"},
                {"id": "Santa Fe", "nombre": "Santa Fe"},
                {"id": "i10", "nombre": "i10"},
                {"id": "i30", "nombre": "i30"},
            ],
            "Nissan": [
                {"id": "March", "nombre": "March"},
                {"id": "Versa", "nombre": "Versa"},
                {"id": "Sentra", "nombre": "Sentra"},
                {"id": "X-Trail", "nombre": "X-Trail"},
                {"id": "Altima", "nombre": "Altima"},
                {"id": "Frontier", "nombre": "Frontier"},
            ],
        }

        modelos = modelos_por_marca.get(marca_id, [])

        return JsonResponse({"success": True, "modelos": modelos})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_motores(request):
    """Endpoint AJAX para obtener motores filtrados por modelo"""
    try:
        modelo_id = request.GET.get("modelo_id")

        if modelo_id:
            # Filtrar motores por modelo específico
            from taller.models.extras_vehiculo import MotorVehiculo
            from taller.models.modelo import Modelo

            try:
                modelo = Modelo.objects.get(id=modelo_id)
                motores_queryset = MotorVehiculo.objects.filter(
                    modelos=modelo
                ).order_by("nombre")

                motores = [
                    {"id": motor.id, "nombre": motor.nombre}
                    for motor in motores_queryset
                ]
            except Modelo.DoesNotExist:
                motores = []
        else:
            # Si no se especifica modelo, devolver lista vacía
            motores = []

        return JsonResponse({"success": True, "motores": motores})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_cajas(request):
    """Endpoint AJAX para obtener cajas filtradas por modelo"""
    try:
        modelo_id = request.GET.get("modelo_id")

        if modelo_id:
            # Filtrar cajas por modelo específico
            from taller.models.extras_vehiculo import CajaVehiculo
            from taller.models.modelo import Modelo

            try:
                modelo = Modelo.objects.get(id=modelo_id)
                cajas_queryset = CajaVehiculo.objects.filter(modelos=modelo).order_by(
                    "nombre"
                )

                cajas = [
                    {"id": caja.id, "nombre": caja.nombre} for caja in cajas_queryset
                ]
            except Modelo.DoesNotExist:
                cajas = []
        else:
            # Si no se especifica modelo, devolver lista vacía
            cajas = []

        return JsonResponse({"success": True, "cajas": cajas})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


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
        modelo_id = request.GET.get("modelo_id")

        if modelo_id:
            # Filtrar motores y cajas por modelo específico
            from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
            from taller.models.modelo import Modelo

            try:
                modelo = Modelo.objects.get(id=modelo_id)

                # Obtener motores para este modelo
                motores_queryset = MotorVehiculo.objects.filter(
                    modelos=modelo
                ).order_by("nombre")
                motores = [
                    {"id": motor.id, "nombre": motor.nombre}
                    for motor in motores_queryset
                ]

                # Obtener cajas para este modelo
                cajas_queryset = CajaVehiculo.objects.filter(modelos=modelo).order_by(
                    "nombre"
                )
                cajas = [
                    {"id": caja.id, "nombre": caja.nombre} for caja in cajas_queryset
                ]

                return JsonResponse(
                    {
                        "success": True,
                        "motores": motores,
                        "cajas": cajas,
                        "modelo": modelo.nombre,
                        "marca": modelo.marca.nombre if modelo.marca else "N/A",
                    }
                )

            except Modelo.DoesNotExist:
                return JsonResponse(
                    {
                        "success": True,
                        "motores": [],
                        "cajas": [],
                        "error": "Modelo no encontrado",
                    }
                )
        else:
            # Si no se especifica modelo, devolver listas vacías
            return JsonResponse({"success": True, "motores": [], "cajas": []})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
