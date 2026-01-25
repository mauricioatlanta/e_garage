"""
Vistas para el ingreso de vehículos al taller mediante foto de patente.
"""

import json
import logging
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo
from taller.utils.pais_utils import get_configuracion_pais
from whatsapp.services.ocr import OCRProcessor

logger = logging.getLogger(__name__)


@login_required
def ingreso_vehiculo_foto(request):
    """
    Vista principal para el ingreso de vehículos mediante foto de patente.
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return render(
            request,
            "taller/vehiculos/error.html",
            {"error": "No tienes una empresa asignada"},
            status=400,
        )

    # Detectar país
    country = getattr(empresa, "pais", "CL")
    country_config = get_configuracion_pais(country)

    # Detectar idioma desde la URL o configuración
    path_parts = request.path.strip("/").split("/")
    lang = "es"
    if len(path_parts) >= 2 and path_parts[1] in ["es", "en"]:
        lang = path_parts[1]

    context = {
        "empresa": empresa,
        "country": country,
        "country_config": country_config,
        "lang": lang,
    }

    template = f"taller/vehiculos/ingreso_foto_patente.html"
    return render(request, template, context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def api_procesar_foto_patente(request):
    """
    API endpoint para procesar foto de patente y buscar/crear vehículo.

    POST /api/vehiculos/procesar-foto-patente/
    Body: FormData con 'foto' (archivo de imagen)

    Returns JSON:
    {
        "success": true,
        "patente": "ABCD12",
        "vehiculo": {
            "id": 123,
            "patente": "ABCD12",
            "marca": "Toyota",
            "modelo": "Corolla",
            "cliente": {
                "id": 456,
                "nombre": "Juan Pérez"
            }
        },
        "existe": true,
        "mensaje": "Vehículo encontrado"
    }
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse(
            {"success": False, "error": "No tienes una empresa asignada"}, status=400
        )

    # Verificar que se subió un archivo
    if "foto" not in request.FILES:
        return JsonResponse({"success": False, "error": "No se recibió ninguna imagen"}, status=400)

    imagen = request.FILES["foto"]

    # Validar tipo de archivo
    if not imagen.content_type.startswith("image/"):
        return JsonResponse(
            {"success": False, "error": "El archivo debe ser una imagen"}, status=400
        )

    # Leer bytes de la imagen
    try:
        image_bytes = imagen.read()
        if len(image_bytes) == 0:
            return JsonResponse({"success": False, "error": "La imagen está vacía"}, status=400)
    except Exception as e:
        logger.error(f"Error leyendo imagen: {e}")
        return JsonResponse({"success": False, "error": "Error procesando la imagen"}, status=500)

    # Procesar OCR
    ocr_processor = OCRProcessor()
    patente = ocr_processor.extract_plate(image_bytes)

    if not patente:
        return JsonResponse(
            {
                "success": False,
                "error": "No se pudo detectar la patente en la imagen. Por favor, intenta con una foto más clara.",
            },
            status=400,
        )

    # Buscar vehículo por patente en la empresa
    try:
        vehiculo = (
            Vehiculo.objects.filter(empresa=empresa, patente__iexact=patente)
            .select_related("cliente", "marca", "modelo")
            .first()
        )

        if vehiculo:
            # Vehículo encontrado
            cliente = vehiculo.cliente
            return JsonResponse(
                {
                    "success": True,
                    "patente": patente,
                    "vehiculo": {
                        "id": vehiculo.id,
                        "patente": vehiculo.patente,
                        "marca": vehiculo.get_marca_display(),
                        "modelo": vehiculo.get_modelo_display(),
                        "anio": vehiculo.anio,
                        "cliente": {
                            "id": cliente.id,
                            "nombre": cliente.nombre,
                            "apellido": cliente.apellido or "",
                            "telefono": cliente.telefono or "",
                        },
                    },
                    "existe": True,
                    "mensaje": "Vehículo encontrado en la base de datos",
                }
            )
        else:
            # Vehículo no encontrado - retornar patente para crear nuevo
            return JsonResponse(
                {
                    "success": True,
                    "patente": patente,
                    "vehiculo": None,
                    "existe": False,
                    "mensaje": f"Patente {patente} no encontrada. ¿Deseas crear un nuevo vehículo?",
                }
            )

    except Exception as e:
        logger.error(f"Error buscando vehículo: {e}")
        return JsonResponse(
            {"success": False, "error": "Error buscando vehículo en la base de datos"}, status=500
        )


@login_required
def procesar_patente_identificada(request):
    """
    Vista que se muestra después de identificar una patente.
    Permite:
    1. Si el vehículo existe: mostrar info y preguntar si quiere crear documento
    2. Si no existe: redirigir a formulario para crear vehículo/cliente
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return render(
            request,
            "taller/vehiculos/error.html",
            {"error": "No tienes una empresa asignada"},
            status=400,
        )

    patente = request.GET.get("patente", "").strip().upper()
    vehiculo_id = request.GET.get("vehiculo_id")

    if not patente:
        return render(
            request,
            "taller/vehiculos/error.html",
            {"error": "No se proporcionó una patente"},
            status=400,
        )

    # Detectar país e idioma
    country = getattr(empresa, "pais", "CL")
    country_config = get_configuracion_pais(country)
    path_parts = request.path.strip("/").split("/")
    lang = "es"
    if len(path_parts) >= 2 and path_parts[1] in ["es", "en"]:
        lang = path_parts[1]

    context = {
        "empresa": empresa,
        "patente": patente,
        "country": country,
        "country_config": country_config,
        "lang": lang,
    }

    # Si hay vehículo_id, cargar información del vehículo
    if vehiculo_id:
        try:
            vehiculo = (
                Vehiculo.objects.filter(id=vehiculo_id, empresa=empresa)
                .select_related("cliente", "marca", "modelo")
                .first()
            )

            if vehiculo:
                context["vehiculo"] = vehiculo
                context["cliente"] = vehiculo.cliente
        except Exception as e:
            logger.error(f"Error cargando vehículo: {e}")

    template = f"taller/vehiculos/patente_identificada.html"
    return render(request, template, context)
