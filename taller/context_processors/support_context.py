"""
Context processor para información de soporte centralizada.
Expone support_email, support_whatsapp_display y support_whatsapp_wa_me
para uso en templates.
"""

from django.conf import settings


def support_context(request):
    """
    Context processor que expone información de soporte.

    Variables disponibles en templates:
    - support_email: Email de soporte (ej: support@egarage.cl)
    - support_whatsapp_display: Número WhatsApp formateado para mostrar (ej: +56 9 5357 4683)
    - support_whatsapp_wa_me: Número WhatsApp sin + ni espacios para wa.me/ (ej: 56953574683)
    """
    return {
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@egarage.cl"),
        "support_whatsapp_display": getattr(
            settings, "SUPPORT_WHATSAPP_DISPLAY", "+56 9 5357 4683"
        ),
        "support_whatsapp_wa_me": getattr(settings, "SUPPORT_WHATSAPP_WA_ME", "56953574683"),
        "support_whatsapp_e164": getattr(settings, "SUPPORT_WHATSAPP_E164", "+56953574683"),
    }
