"""
Views para envío de mensajes de WhatsApp
"""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from taller.models.documento import Documento
from taller.models.clientes import Cliente
from .whatsapp import WhatsAppGateway
from .models import CasaRepuestos, WhatsAppEnvio


@login_required
@require_POST
def enviar_whatsapp_cliente(request, documento_id):
    """
    Envía mensaje de WhatsApp al cliente con link para ver su presupuesto.

    Endpoint: POST /marketplace/whatsapp/cliente/<documento_id>/
    """
    try:
        empresa = request.user.empresa
        documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)

        # Obtener teléfono del cliente
        cliente = documento.cliente
        telefono = getattr(cliente, "telefono", None) or getattr(cliente, "celular", None)

        if not telefono:
            return JsonResponse(
                {"success": False, "error": "Cliente no tiene teléfono registrado"}, status=400
            )

        # Verificar "Factor Fatiga" - Rate limiting (30 minutos)
        limite_tiempo = timezone.now() - timedelta(minutes=30)
        ultimo_envio = (
            WhatsAppEnvio.objects.filter(
                empresa=empresa,
                telefono_destino=telefono,
                tipo_envio="cliente",
                fecha_envio__gte=limite_tiempo,
                exito=True,
            )
            .order_by("-fecha_envio")
            .first()
        )

        if ultimo_envio:
            minutos_transcurridos = int(
                (timezone.now() - ultimo_envio.fecha_envio).total_seconds() / 60
            )
            return JsonResponse(
                {
                    "success": False,
                    "error": "rate_limit",
                    "message": f"Ya se envió un mensaje hace {minutos_transcurridos} minutos",
                    "ultimo_envio": ultimo_envio.fecha_envio.isoformat(),
                    "minutos_restantes": 30 - minutos_transcurridos,
                    "allow_force": True,  # Permite reenviar si el usuario confirma
                },
                status=429,
            )  # 429 Too Many Requests

        # Generar link para ver detalle (sin costos técnicos)
        link_ver_detalle = (
            request.build_absolute_uri(reverse("publico:ver_documento", args=[documento.uuid]))
            if hasattr(documento, "uuid")
            else request.build_absolute_uri(f"/portal/documentos/{documento.id}/")
        )

        # Enviar mensaje
        gateway = WhatsAppGateway(empresa)
        resultado = gateway.enviar_mensaje_cliente(telefono, documento, link_ver_detalle)

        if resultado.get("success"):
            # Registrar envío en la base de datos (para rate limiting)
            WhatsAppEnvio.objects.create(
                empresa=empresa,
                telefono_destino=telefono,
                tipo_envio="cliente",
                documento_id=documento.id,
                mensaje_id=resultado.get("message_id"),
                exito=True,
            )

            # Opcional: Actualizar estado del documento
            if documento.estado == "PENDIENTE":
                documento.estado = "ENVIADO"
                documento.save(update_fields=["estado"])

            return JsonResponse(
                {
                    "success": True,
                    "message": "Mensaje enviado correctamente",
                    "message_id": resultado.get("message_id"),
                }
            )
        else:
            return JsonResponse(
                {"success": False, "error": resultado.get("error", "Error desconocido")}, status=500
            )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def enviar_whatsapp_proveedor(request, casa_repuestos_id, part_number):
    """
    Envía mensaje de WhatsApp al proveedor con pedido y link para confirmar stock.

    Endpoint: POST /marketplace/whatsapp/proveedor/<casa_repuestos_id>/<part_number>/
    """
    try:
        empresa = request.user.empresa
        casa_repuestos = get_object_or_404(CasaRepuestos, id=casa_repuestos_id, empresa=empresa)

        # Obtener teléfono del proveedor
        telefono = casa_repuestos.telefono
        if not telefono:
            return JsonResponse(
                {"success": False, "error": "Casa de repuestos no tiene teléfono registrado"},
                status=400,
            )

        # Obtener documento actual (si existe en el contexto)
        documento_id = request.POST.get("documento_id")
        documento = None
        if documento_id:
            documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
        else:
            # Crear documento temporal para el mensaje
            from taller.models.documento import Documento

            documento = Documento(empresa=empresa, tipo="OT", numero="TEMP", total=0)

        # Generar link para confirmar stock
        link_confirmar = request.build_absolute_uri(
            reverse("marketplace:confirmar_stock", args=[casa_repuestos_id, part_number])
        )

        # Enviar mensaje
        gateway = WhatsAppGateway(empresa)
        resultado = gateway.enviar_mensaje_proveedor(
            telefono, documento, part_number, link_confirmar
        )

        if resultado.get("success"):
            # Registrar envío en la base de datos (para rate limiting)
            WhatsAppEnvio.objects.create(
                empresa=empresa,
                telefono_destino=telefono,
                tipo_envio="proveedor",
                documento_id=documento.id if documento and hasattr(documento, "id") else None,
                mensaje_id=resultado.get("message_id"),
                exito=True,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Mensaje enviado al proveedor",
                    "message_id": resultado.get("message_id"),
                }
            )
        else:
            # Registrar envío fallido
            WhatsAppEnvio.objects.create(
                empresa=empresa,
                telefono_destino=telefono,
                tipo_envio="proveedor",
                documento_id=documento.id if documento and hasattr(documento, "id") else None,
                exito=False,
            )

            return JsonResponse(
                {"success": False, "error": resultado.get("error", "Error desconocido")}, status=500
            )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
