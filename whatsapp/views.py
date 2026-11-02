"""
Views para eGarage Air - WhatsApp v2 Final
Webhook para recibir mensajes de Meta Cloud API
"""
import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone

# Imports diferidos para evitar problemas de carga circular
# Los imports se harán dentro de las funciones cuando sea necesario

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@csrf_exempt
def webhook(request):
    """
    Webhook para Meta Cloud API.
    
    GET: Verificación del webhook (Meta lo llama al configurar)
    POST: Recepción de mensajes
    """
    if request.method == 'GET':
        return _handle_verification(request)
    elif request.method == 'POST':
        return _handle_message(request)
    else:
        return HttpResponse(status=405)


def _handle_verification(request):
    """
    Manejar verificación del webhook (GET).
    Meta envía un challenge que debemos devolver.
    
    Meta Cloud API envía estos parámetros:
    - hub.mode: 'subscribe'
    - hub.verify_token: El token que configuraste en Meta
    - hub.challenge: Un string aleatorio que debes devolver
    """
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    
    # Intentar obtener el token de settings primero
    verify_token = getattr(settings, 'META_WA_VERIFY_TOKEN', None)
    
    # Normalizar: convertir string vacío a None
    if verify_token == "":
        verify_token = None
    
    # Si no está en settings, intentar leerlo directamente del .env
    if not verify_token:
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Cargar .env desde la raíz del proyecto
        # whatsapp/views.py -> whatsapp/ -> gestion_taller/ -> raíz
        env_path = Path(__file__).resolve().parent.parent.parent / '.env'
        logger.info(f"Token no encontrado en settings. Intentando cargar desde: {env_path}")
        
        if env_path.exists():
            load_dotenv(env_path, override=True)
            verify_token = os.getenv('META_WA_VERIFY_TOKEN', None)
            logger.info(f"Token cargado desde .env: {verify_token is not None}")
        else:
            logger.warning(f"Archivo .env no encontrado en: {env_path}")
            # Intentar cargar desde el directorio actual como último recurso
            load_dotenv(override=True)
            verify_token = os.getenv('META_WA_VERIFY_TOKEN', None)
            logger.info(f"Token cargado desde .env (fallback): {verify_token is not None}")
    
    # Log para debugging
    logger.info(f"Verificación webhook: mode={mode}, token_recibido={token}, token_configurado={verify_token}, challenge={challenge}")
    
    # Verificar que tenemos todos los parámetros necesarios
    if not verify_token:
        logger.error("META_WA_VERIFY_TOKEN no está configurado en settings ni en .env")
        return HttpResponse('Verification failed: Token no configurado. Reinicia el servidor Django.', status=403)
    
    if mode == 'subscribe' and token == verify_token:
        logger.info("Webhook verificado correctamente")
        return HttpResponse(challenge, content_type='text/plain')
    else:
        logger.warning(f"Verificación fallida: mode={mode}, token={token}, verify_token_config={verify_token}")
        # Si no hay parámetros, mostrar mensaje informativo
        if not mode and not token:
            return HttpResponse(
                'Webhook de WhatsApp. Para verificar, Meta debe enviar: hub.mode=subscribe&hub.verify_token=TU_TOKEN&hub.challenge=CHALLENGE',
                content_type='text/plain'
            )
        return HttpResponse('Verification failed', status=403)


def _handle_message(request):
    """
    Manejar mensajes entrantes (POST).
    Procesa los mensajes según el flujo conversacional.
    """
    # Import diferido para evitar problemas de carga
    from .models import EmpresaWhatsAppConfig, WhatsAppSession
    from .services.meta import MetaWhatsAppClient
    from .services.flow import WhatsAppFlowManager
    
    try:
        body = json.loads(request.body)
        logger.info(f"Mensaje recibido: {json.dumps(body, indent=2)}")
        
        # Meta envía los datos en 'entry'
        if 'entry' not in body:
            logger.warning("Mensaje sin 'entry'")
            return HttpResponse(status=200)  # Responder 200 para evitar reintentos
        
        for entry in body.get('entry', []):
            changes = entry.get('changes', [])
            for change in changes:
                value = change.get('value', {})
                
                # Verificar si hay mensajes
                messages = value.get('messages', [])
                if not messages:
                    # Puede ser un status update, lo ignoramos
                    continue
                
                # Procesar cada mensaje
                for message in messages:
                    _process_incoming_message(value, message)
        
        # Siempre responder 200 para evitar reintentos de Meta
        return HttpResponse(status=200)
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e}")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        return HttpResponse(status=200)  # Responder 200 para evitar reintentos


def _process_incoming_message(value: dict, message: dict):
    """
    Procesar un mensaje entrante individual.
    
    Args:
        value: Valor del cambio (contiene metadata)
        message: Mensaje individual
    """
    from_phone = message.get('from')
    message_id = message.get('id')
    message_type = message.get('type')
    
    if not from_phone:
        logger.warning("Mensaje sin 'from'")
        return
    
    # Normalizar teléfono (remover código de país si viene con +)
    from_phone = from_phone.replace('+', '').replace(' ', '')
    
    # Buscar configuración de empresa por número de teléfono
    # Por ahora, asumimos que el phone_number_id viene en 'value.metadata.phone_number_id'
    # En producción, necesitarás mapear phone_number_id a empresa
    phone_number_id = value.get('metadata', {}).get('phone_number_id')
    
    if not phone_number_id:
        logger.warning("No se encontró phone_number_id en el mensaje")
        return
    
    # Buscar configuración
    try:
        config = EmpresaWhatsAppConfig.objects.get(
            phone_number_id=phone_number_id,
            is_enabled=True
        )
    except EmpresaWhatsAppConfig.DoesNotExist:
        logger.warning(f"Configuración no encontrada para phone_number_id: {phone_number_id}")
        return
    
    # Validar operador autorizado
    if from_phone != config.allowed_operator_phone:
        logger.warning(f"Teléfono no autorizado: {from_phone}")
        # Opcional: enviar mensaje de error
        access_token = getattr(settings, 'META_WA_TOKEN', None)
        if access_token:
            client = MetaWhatsAppClient(config.phone_number_id, access_token)
            client.send_text_message(
                from_phone,
                "❌ No estás autorizado para usar este servicio."
            )
        return
    
    # Obtener o crear sesión
    session, created = WhatsAppSession.objects.get_or_create(
        operator_phone=from_phone,
        defaults={'empresa': config.empresa}
    )
    
    if not created:
        session.empresa = config.empresa  # Actualizar por si cambió
        session.save()
    
    # Inicializar cliente Meta
    access_token = getattr(settings, 'META_WA_TOKEN', None)
    if not access_token:
        logger.error("META_WA_TOKEN no configurado en settings")
        return
    
    meta_client = MetaWhatsAppClient(config.phone_number_id, access_token)
    
    # Inicializar gestor de flujo
    flow_manager = WhatsAppFlowManager(session, meta_client)
    
    # Extraer contenido según tipo
    content = {}
    if message_type == 'text':
        content = {'text': message.get('text', {}).get('body', '')}
    elif message_type == 'image':
        content = {'id': message.get('image', {}).get('id')}
    elif message_type == 'audio':
        content = {'id': message.get('audio', {}).get('id')}
    elif message_type == 'video':
        content = {'id': message.get('video', {}).get('id')}
    elif message_type == 'interactive':
        interactive = message.get('interactive', {})
        if 'button_reply' in interactive:
            content = {'button_reply': interactive['button_reply']}
        elif 'list_reply' in interactive:
            content = {'list_reply': interactive['list_reply']}
    
    # Procesar mensaje
    flow_manager.process_message(from_phone, message_type, content)
