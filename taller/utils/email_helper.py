"""
Helper centralizado para envío de emails con reply_to configurado.
Usa EmailMessage con reply_to=[SUPPORT_EMAIL] para todas las notificaciones.
"""

import logging
from email.utils import formataddr, parseaddr
from typing import List, Optional

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _extract_email_address(raw_email: Optional[str]) -> str:
    _, email_address = parseaddr((raw_email or "").strip())
    return (email_address or (raw_email or "")).strip()


def _is_legacy_atlanta_address(email_address: str) -> bool:
    return email_address.lower().endswith("@atlantareciclajes.cl")


def get_branded_from_email(
    from_email: Optional[str] = None, brand_name: Optional[str] = None
) -> str:
    """
    Devuelve un remitente con display name consistente.

    Ejemplos:
    - "support@egarage.cl" -> "eGarage <support@egarage.cl>"
    - "Soporte eGarage <support@egarage.cl>" -> se preserva tal cual
    """
    raw_from = (
        from_email
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "SUPPORT_EMAIL", None)
        or "support@egarage.cl"
    ).strip()

    display_name, email_address = parseaddr(raw_from)
    email_address = (email_address or raw_from).strip() or "support@egarage.cl"

    if display_name:
        return formataddr((display_name, email_address))

    resolved_brand_name = (
        brand_name
        or getattr(settings, "SITE_NAME", None)
        or getattr(settings, "DEFAULT_BRAND_NAME", None)
        or "eGarage"
    )
    return formataddr((resolved_brand_name, email_address))


def get_support_reply_to() -> str:
    """
    Devuelve la casilla de soporte usable como Reply-To.
    """
    support_email = _extract_email_address(getattr(settings, "SUPPORT_EMAIL", None))
    default_from_email = _extract_email_address(getattr(settings, "DEFAULT_FROM_EMAIL", None))

    if support_email and not _is_legacy_atlanta_address(support_email):
        return support_email

    if default_from_email:
        return default_from_email

    if support_email:
        return support_email

    return "support@egarage.cl"


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

    resolved_from_email = get_branded_from_email(from_email)
    support_email = get_support_reply_to()

    try:
        if html_message:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=resolved_from_email,
                to=recipient_list,
                reply_to=[support_email],
            )
            email.attach_alternative(html_message, "text/html")
        else:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=resolved_from_email,
                to=recipient_list,
                reply_to=[support_email],
            )

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
            context["support_email"] = get_support_reply_to()
        if "support_whatsapp_display" not in context:
            context["support_whatsapp_display"] = getattr(
                settings, "SUPPORT_WHATSAPP_DISPLAY", "+56 9 5357 4683"
            )
        if "support_whatsapp_wa_me" not in context:
            context["support_whatsapp_wa_me"] = getattr(
                settings, "SUPPORT_WHATSAPP_WA_ME", "56953574683"
            )

        # Validar que el template exista antes de renderizar
        try:
            html_message = render_to_string(template_name, context)
        except Exception as template_error:
            logger.error(
                f"Error renderizando template '{template_name}': {template_error}", exc_info=True
            )
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
