import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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
    """Endpoint AJAX para obtener tipos de motor"""
    try:
        motores = [
            {"id": "1.0L", "nombre": "1.0L"},
            {"id": "1.2L", "nombre": "1.2L"},
            {"id": "1.4L", "nombre": "1.4L"},
            {"id": "1.6L", "nombre": "1.6L"},
            {"id": "1.8L", "nombre": "1.8L"},
            {"id": "2.0L", "nombre": "2.0L"},
            {"id": "2.4L", "nombre": "2.4L"},
            {"id": "2.5L", "nombre": "2.5L"},
            {"id": "3.0L V6", "nombre": "3.0L V6"},
            {"id": "3.5L V6", "nombre": "3.5L V6"},
            {"id": "4.0L V6", "nombre": "4.0L V6"},
            {"id": "5.0L V8", "nombre": "5.0L V8"},
            {"id": "1.6L Turbo", "nombre": "1.6L Turbo"},
            {"id": "2.0L Turbo", "nombre": "2.0L Turbo"},
            {"id": "Híbrido", "nombre": "Híbrido"},
            {"id": "Eléctrico", "nombre": "Eléctrico"},
            {"id": "Diesel 2.0L", "nombre": "Diesel 2.0L"},
            {"id": "Diesel 2.5L", "nombre": "Diesel 2.5L"},
        ]

        return JsonResponse({"success": True, "motores": motores})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def ajax_cajas(request):
    """Endpoint AJAX para obtener tipos de caja de cambios"""
    try:
        cajas = [
            {"id": "Manual 5 velocidades", "nombre": "Manual 5 velocidades"},
            {"id": "Manual 6 velocidades", "nombre": "Manual 6 velocidades"},
            {"id": "Automática 4 velocidades", "nombre": "Automática 4 velocidades"},
            {"id": "Automática 5 velocidades", "nombre": "Automática 5 velocidades"},
            {"id": "Automática 6 velocidades", "nombre": "Automática 6 velocidades"},
            {"id": "Automática 8 velocidades", "nombre": "Automática 8 velocidades"},
            {"id": "Automática CVT", "nombre": "Automática CVT"},
            {"id": "Secuencial", "nombre": "Secuencial"},
            {"id": "Tiptronic", "nombre": "Tiptronic"},
            {"id": "DSG", "nombre": "DSG"},
            {"id": "PDK", "nombre": "PDK"},
        ]

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
        # Obtener datos de motores
        motores_response = ajax_motores(request)
        motores_data = json.loads(motores_response.content.decode("utf-8"))

        # Obtener datos de cajas
        cajas_response = ajax_cajas(request)
        cajas_data = json.loads(cajas_response.content.decode("utf-8"))

        # Combinar respuestas
        return JsonResponse(
            {
                "success": True,
                "motores": motores_data.get("motores", []),
                "cajas": cajas_data.get("cajas", []),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
