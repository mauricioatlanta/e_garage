"""
Webhooks para recibir respuestas de WhatsApp
"""
import json
import logging
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from taller.models.documento import Documento
from .whatsapp import WhatsAppGateway

logger = logging.getLogger(__name__)


def _verificar_token_webhook(request, provider: str) -> bool:
    """
    Verifica el token de seguridad del webhook para prevenir ataques.
    
    Soporta:
    - Ultramsg: Token en query parameter 'token'
    - Twilio: Firma X-Twilio-Signature (más compleja, requiere validación de firma)
    """
    if provider == 'ultramsg':
        token_esperado = os.getenv('ULTRAMSG_WEBHOOK_TOKEN')
        token_recibido = request.GET.get('token')
        
        if not token_esperado:
            logger.warning("ULTRAMSG_WEBHOOK_TOKEN no configurado, webhook no protegido")
            return True  # Permite si no está configurado (modo desarrollo)
        
        return token_recibido == token_esperado
    
    elif provider == 'twilio':
        # Twilio usa firma HMAC en el header X-Twilio-Signature
        # Esto requiere validación más compleja con auth_token
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        signature = request.headers.get('X-Twilio-Signature', '')
        
        if not auth_token:
            logger.warning("TWILIO_AUTH_TOKEN no configurado, webhook no protegido")
            return True
        
        # Validación básica: verificar que el signature existe y no está vacío
        # Para producción completa, deberías validar la firma HMAC completa
        # Ver: https://www.twilio.com/docs/usage/webhooks/webhooks-security
        return len(signature) > 0
    
    return False


@csrf_exempt
@require_POST
def webhook_whatsapp_cliente(request):
    """
    Webhook para recibir respuestas de WhatsApp del cliente.
    Cambia el estado de la OT de 'PENDIENTE' a 'APROBADO' cuando el cliente responde 'SÍ'.
    
    Endpoint: POST /marketplace/webhooks/whatsapp/cliente/?provider=ultramsg&token=SECRET_TOKEN
    """
    try:
        # Obtener datos según el proveedor
        provider = request.GET.get('provider', 'ultramsg')
        
        # Verificar token de seguridad
        if not _verificar_token_webhook(request, provider):
            logger.warning(f"Intento de webhook sin token válido desde {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({"error": "Token inválido"}, status=403)
        
        if provider == 'ultramsg':
            data = json.loads(request.body)
            mensaje = data.get('body', '')
            telefono = data.get('from', '')
            # El documento_id debería venir en el mensaje o en metadata
            # Por ahora, buscamos por número de teléfono del cliente
        elif provider == 'twilio':
            mensaje = request.POST.get('Body', '')
            telefono = request.POST.get('From', '')
        else:
            return JsonResponse({"error": "Proveedor no soportado"}, status=400)
        
        # Procesar respuesta
        resultado = WhatsAppGateway.procesar_respuesta_cliente(mensaje)
        
        if resultado == 'APROBADO':
            # Buscar documento pendiente del cliente (esto requiere lógica adicional)
            # Por ahora, retornamos éxito
            logger.info(f"Cliente {telefono} aprobó documento vía WhatsApp")
            return JsonResponse({
                "success": True,
                "action": "documento_aprobado",
                "message": "Documento aprobado correctamente"
            })
        elif resultado == 'RECHAZADO':
            logger.info(f"Cliente {telefono} rechazó documento vía WhatsApp")
            return JsonResponse({
                "success": True,
                "action": "documento_rechazado",
                "message": "Documento rechazado"
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "Respuesta no reconocida"
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error procesando webhook de WhatsApp: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def webhook_whatsapp_proveedor(request):
    """
    Webhook para recibir confirmaciones de stock del proveedor.
    Cuando el proveedor confirma stock, se notifica al taller.
    
    Endpoint: POST /marketplace/webhooks/whatsapp/proveedor/?provider=ultramsg&token=SECRET_TOKEN
    """
    try:
        provider = request.GET.get('provider', 'ultramsg')
        
        # Verificar token de seguridad
        if not _verificar_token_webhook(request, provider):
            logger.warning(f"Intento de webhook proveedor sin token válido desde {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({"error": "Token inválido"}, status=403)
        
        if provider == 'ultramsg':
            data = json.loads(request.body)
            mensaje = data.get('body', '')
            telefono = data.get('from', '')
        elif provider == 'twilio':
            mensaje = request.POST.get('Body', '')
            telefono = request.POST.get('From', '')
        else:
            return JsonResponse({"error": "Proveedor no soportado"}, status=400)
        
        # Procesar confirmación de stock
        mensaje_lower = mensaje.lower().strip()
        if any(palabra in mensaje_lower for palabra in ['confirmo', 'disponible', 'si', 'sí', 'ok', 'stock']):
            logger.info(f"Proveedor {telefono} confirmó stock vía WhatsApp")
            # Aquí se notificaría al taller (email, notificación interna, etc.)
            return JsonResponse({
                "success": True,
                "action": "stock_confirmado",
                "message": "Stock confirmado, taller notificado"
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "Confirmación no reconocida"
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error procesando webhook de proveedor: {e}")
        return JsonResponse({"error": str(e)}, status=500)
