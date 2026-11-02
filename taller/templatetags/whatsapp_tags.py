from django import template

from taller.utils.whatsapp_helper import clean_phone_number, get_document_whatsapp_url

register = template.Library()


@register.simple_tag
def whatsapp_url(phone=None, text=""):
    """
    Link wa.me estándar.
    phone: número internacional (solo dígitos). Ej: 56912345678
    text: mensaje opcional
    """
    phone = clean_phone_number(phone)
    if not phone:
        return ""
    from urllib.parse import quote

    msg = quote(text or "")
    if msg:
        return f"https://wa.me/{phone}?text={msg}"
    return f"https://wa.me/{phone}"


@register.filter
def only_digits(value):
    """Deja solo dígitos (útil si guardas +56 9 1234 5678)."""
    return "".join(ch for ch in str(value or "") if ch.isdigit())


@register.filter
def has_whatsapp(cliente):
    """Verificar si cliente tiene teléfono para WhatsApp."""
    if not cliente:
        return False
    telefono = getattr(cliente, "telefono", None) or getattr(cliente, "phone", None)
    return bool(telefono)


@register.simple_tag(takes_context=True)
def whatsapp_document_link(context, document=None, text=None):
    """
    Genera un link de WhatsApp para el cliente del documento.

    Soporta estos usos:
    - {% whatsapp_document_link documento as wa_link %}
    - {% whatsapp_document_link documento request as wa_link %}
    - {% whatsapp_document_link documento "mensaje opcional" as wa_link %}
    """
    try:
        request = context.get("request")
        message_override = None

        if hasattr(text, "build_absolute_uri"):
            request = text
        elif text:
            message_override = text

        return get_document_whatsapp_url(
            document,
            request=request,
            message_override=message_override,
        ) or ""
    except Exception:
        return ""
