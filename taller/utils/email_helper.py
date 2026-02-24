"""
Helper centralizado para envío de emails con reply_to configurado.
Usa EmailMessage con reply_to=[SUPPORT_EMAIL] para todas las notificaciones.
"""
import logging
from typing import List, Optional

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_email_with_reply_to(
    subject: str,
    message: str,
    recipient_list: List[str],
    from_email: Optional[str] = None,
    html_message: Optional[str] = None,
    fail_silently: bool = False,
):
    """
    Envía un email usando EmailMessage con reply_to configurado a SUPPORT_EMAIL.
    
    Args:
        subject: Asunto del email
        message: Contenido en texto plano
        recipient_list: Lista de destinatarios
        from_email: Email remitente (default: DEFAULT_FROM_EMAIL)
        html_message: Contenido HTML opcional
        fail_silently: Si True, no lanza excepciones en caso de error
        
    Returns:
        int: Número de emails enviados exitosamente
    """
    # Failsafe: validar que recipient_list no esté vacío
    if not recipient_list:
        logger.warning("[email_helper] recipient_list está vacío, no se enviará email")
        return 0
    
    # Failsafe: obtener from_email con fallback robusto
    if not from_email:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not from_email:
            # Fallback adicional si DEFAULT_FROM_EMAIL no está definido
            from_email = getattr(settings, "SUPPORT_EMAIL", "support@egarage.cl")
            from_email = f"eGarage <{from_email}>"
    
    # Failsafe: obtener SUPPORT_EMAIL para reply_to con fallback robusto
    support_email = getattr(settings, "SUPPORT_EMAIL", None)
    if not support_email:
        # Extraer email de DEFAULT_FROM_EMAIL si SUPPORT_EMAIL no está definido
        default_from = getattr(settings, "DEFAULT_FROM_EMAIL", "")
        if "<" in default_from and ">" in default_from:
            support_email = default_from.split("<")[1].split(">")[0].strip()
        else:
            support_email = "support@egarage.cl"  # Fallback final
        logger.warning(f"[email_helper] SUPPORT_EMAIL no definido, usando fallback: {support_email}")
    
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            reply_to=[support_email],  # ✅ Reply-To configurado
        )
        
        # Agregar versión HTML si se proporciona
        if html_message:
            email.content_subtype = "html"
            email.body = html_message
        
        result = email.send(fail_silently=fail_silently)
        logger.info(f"Email enviado exitosamente a {recipient_list} con reply_to={support_email}")
        return result
        
    except Exception as e:
        logger.error(f"Error enviando email a {recipient_list}: {e}", exc_info=True)
        if not fail_silently:
            raise
        return 0


def send_template_email(
    template_name: str,
    context: dict,
    subject: str,
    recipient_list: List[str],
    from_email: Optional[str] = None,
    fail_silently: bool = False,
):
    """
    Envía un email renderizando un template HTML con reply_to configurado.
    
    Args:
        template_name: Nombre del template (ej: 'emails/trial_expired.html')
        context: Contexto para el template
        subject: Asunto del email
        recipient_list: Lista de destinatarios
        from_email: Email remitente (default: DEFAULT_FROM_EMAIL)
        fail_silently: Si True, no lanza excepciones en caso de error
        
    Returns:
        int: Número de emails enviados exitosamente
    """
    try:
        # Failsafe: Agregar variables de soporte al contexto con fallbacks robustos
        if "support_email" not in context:
            context["support_email"] = getattr(settings, "SUPPORT_EMAIL", "support@egarage.cl")
        if "support_whatsapp_display" not in context:
            context["support_whatsapp_display"] = getattr(
                settings, "SUPPORT_WHATSAPP_DISPLAY", "+56 9 5357 4683"
            )
        if "support_whatsapp_wa_me" not in context:
            context["support_whatsapp_wa_me"] = getattr(settings, "SUPPORT_WHATSAPP_WA_ME", "56953574683")
        
        # Validar que el template exista antes de renderizar
        try:
            html_message = render_to_string(template_name, context)
        except Exception as template_error:
            logger.error(f"Error renderizando template '{template_name}': {template_error}", exc_info=True)
            if not fail_silently:
                raise
            return 0
        
        # Crear versión texto plano (remover HTML básico)
        import re
        text_message = re.sub(r"<[^>]+>", "", html_message)
        text_message = re.sub(r"\s+", " ", text_message).strip()
        
        return send_email_with_reply_to(
            subject=subject,
            message=text_message,
            recipient_list=recipient_list,
            from_email=from_email,
            html_message=html_message,
            fail_silently=fail_silently,
        )
        
    except Exception as e:
        logger.error(f"Error enviando template email '{template_name}': {e}", exc_info=True)
        if not fail_silently:
            raise
        return 0
