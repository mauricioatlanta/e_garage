# -*- coding: utf-8 -*-
"""
Views de compatibilidad para APIs por país (BR, VE, PE)

Mantiene las views por país existentes por 1 release,
pero internamente redirigen a la API unificada.

Estrategia:
1. Mantener URLs legacy por país (/br/api/..., /ve/api/..., /pe/api/...)
2. Internamente, usar la API unificada (/api/locations)
3. Agregar deprecation warnings en logs
4. Después de 1 release, deprecar completamente

Ejemplo:
    # OLD (mantener por 1 release):
    /br/api/estados/  → api_estados_compat('BR')

    # NEW (recomendar):
    /api/locations?country=BR
"""
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from taller.ubicacion.api import locations

logger = logging.getLogger(__name__)


# === BRASIL ===


@require_GET
def api_estados_br_compat(request):
    """
    [DEPRECATED] API de estados de Brasil (compatibilidad).

    Usar en su lugar: /api/locations?country=BR

    Esta view se mantendrá por 1 release y luego será removida.
    """
    logger.warning(
        "[DEPRECATED] /br/api/estados/ está deprecated. "
        "Usar /api/locations?country=BR en su lugar."
    )

    # Redirigir internamente a API unificada
    request.GET = request.GET.copy()
    request.GET["country"] = "BR"

    response = locations(request)

    # Transformar respuesta de API unificada a formato legacy
    if response.status_code == 200:
        data = response.json()
        if "states" in data:
            # Formato legacy: {'estados': [...]}
            legacy_data = {"estados": data["states"]}
            return JsonResponse(legacy_data)

    return response


@require_GET
def api_cidades_br_compat(request, estado_id):
    """
    [DEPRECATED] API de ciudades de Brasil por estado (compatibilidad).

    Usar en su lugar: /api/locations?country=BR&state=XX

    Esta view se mantendrá por 1 release y luego será removida.
    """
    logger.warning(
        "[DEPRECATED] /br/api/cidades/<estado_id>/ está deprecated. "
        "Usar /api/locations?country=BR&state=XX en su lugar."
    )

    # Obtener código de estado desde ID
    from taller.models import Estado

    try:
        estado = Estado.objects.get(id=estado_id, pais="BR")
        state_code = estado.codigo
    except Estado.DoesNotExist:
        return JsonResponse({"error": "Estado no encontrado"}, status=404)

    # Redirigir internamente a API unificada
    request.GET = request.GET.copy()
    request.GET["country"] = "BR"
    request.GET["state"] = state_code

    response = locations(request)

    # Transformar respuesta de API unificada a formato legacy
    if response.status_code == 200:
        data = response.json()
        if "cities" in data:
            # Formato legacy: {'ciudades': [...]}
            legacy_data = {"ciudades": data["cities"]}
            return JsonResponse(legacy_data)

    return response


# === VENEZUELA ===


@require_GET
def api_estados_ve_compat(request):
    """
    [DEPRECATED] API de estados de Venezuela (compatibilidad).

    Usar en su lugar: /api/locations?country=VE
    """
    logger.warning(
        "[DEPRECATED] /ve/api/estados/ está deprecated. "
        "Usar /api/locations?country=VE en su lugar."
    )

    request.GET = request.GET.copy()
    request.GET["country"] = "VE"

    response = locations(request)

    if response.status_code == 200:
        data = response.json()
        if "states" in data:
            return JsonResponse({"estados": data["states"]})

    return response


@require_GET
def api_cidades_ve_compat(request, estado_id):
    """
    [DEPRECATED] API de ciudades de Venezuela por estado (compatibilidad).

    Usar en su lugar: /api/locations?country=VE&state=XX
    """
    logger.warning(
        "[DEPRECATED] /ve/api/cidades/<estado_id>/ está deprecated. "
        "Usar /api/locations?country=VE&state=XX en su lugar."
    )

    from taller.models import Estado

    try:
        estado = Estado.objects.get(id=estado_id, pais="VE")
        state_code = estado.codigo
    except Estado.DoesNotExist:
        return JsonResponse({"error": "Estado no encontrado"}, status=404)

    request.GET = request.GET.copy()
    request.GET["country"] = "VE"
    request.GET["state"] = state_code

    response = locations(request)

    if response.status_code == 200:
        data = response.json()
        if "cities" in data:
            return JsonResponse({"ciudades": data["cities"]})

    return response


# === PERÚ ===


@require_GET
def api_estados_pe_compat(request):
    """
    [DEPRECATED] API de estados (departamentos) de Perú (compatibilidad).

    Usar en su lugar: /api/locations?country=PE
    """
    logger.warning(
        "[DEPRECATED] /pe/api/estados/ está deprecated. "
        "Usar /api/locations?country=PE en su lugar."
    )

    request.GET = request.GET.copy()
    request.GET["country"] = "PE"

    response = locations(request)

    if response.status_code == 200:
        data = response.json()
        if "states" in data:
            return JsonResponse({"estados": data["states"]})

    return response


@require_GET
def api_cidades_pe_compat(request, estado_id):
    """
    [DEPRECATED] API de ciudades de Perú por departamento (compatibilidad).

    Usar en su lugar: /api/locations?country=PE&state=XX
    """
    logger.warning(
        "[DEPRECATED] /pe/api/cidades/<estado_id>/ está deprecated. "
        "Usar /api/locations?country=PE&state=XX en su lugar."
    )

    from taller.models import Estado

    try:
        estado = Estado.objects.get(id=estado_id, pais="PE")
        state_code = estado.codigo
    except Estado.DoesNotExist:
        return JsonResponse({"error": "Departamento no encontrado"}, status=404)

    request.GET = request.GET.copy()
    request.GET["country"] = "PE"
    request.GET["state"] = state_code

    response = locations(request)

    if response.status_code == 200:
        data = response.json()
        if "cities" in data:
            return JsonResponse({"ciudades": data["cities"]})

    return response


# === HELPER: Deprecation Notice ===


def get_deprecation_notice(old_url: str, new_url: str) -> dict:
    """
    Genera un aviso de deprecación para incluir en respuestas JSON.

    Args:
        old_url: URL antigua (deprecated)
        new_url: URL nueva (recomendada)

    Returns:
        dict: Información de deprecación

    Ejemplo:
        response_data = {...}
        response_data['_deprecation'] = get_deprecation_notice(
            '/br/api/estados/',
            '/api/locations?country=BR'
        )
    """
    return {
        "deprecated": True,
        "old_endpoint": old_url,
        "new_endpoint": new_url,
        "message": f"This endpoint is deprecated. Please use {new_url} instead.",
        "removal_date": "2026-01-01",  # Ejemplo: 1 release después
    }


# === Middleware para agregar deprecation headers ===


class DeprecationWarningMiddleware:
    """
    Middleware que agrega headers de deprecación a respuestas de APIs legacy.

    Agregar en settings.py:
        MIDDLEWARE = [
            ...
            'taller.views_extra.api_compat.DeprecationWarningMiddleware',
        ]

    Headers agregados:
        Warning: "299 - \"Endpoint deprecated. Use /api/locations instead.\""
        Deprecation: "true"
        Sunset: "Sat, 01 Jan 2026 00:00:00 GMT"
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URLs deprecated (mantener por 1 release)
        self.deprecated_paths = [
            "/br/api/estados/",
            "/br/api/cidades/",
            "/ve/api/estados/",
            "/ve/api/cidades/",
            "/pe/api/estados/",
            "/pe/api/cidades/",
        ]

    def __call__(self, request):
        response = self.get_response(request)

        # Verificar si la ruta es deprecated
        for deprecated_path in self.deprecated_paths:
            if request.path.startswith(deprecated_path):
                # Agregar headers de deprecación
                response["Warning"] = (
                    '299 - "This endpoint is deprecated. ' 'Use /api/locations instead."'
                )
                response["Deprecation"] = "true"
                response["Sunset"] = "Sat, 01 Jan 2026 00:00:00 GMT"
                break

        return response
