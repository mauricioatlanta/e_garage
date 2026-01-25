from urllib.parse import quote
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def whatsapp_url(phone=None, text=""):
    """
    Link wa.me estándar.
    phone: número internacional (solo dígitos). Ej: 56912345678
    text: mensaje opcional
    """
    phone = (phone or "").strip()
    if not phone:
        return ""
    msg = quote(text or "")
    if msg:
        return f"https://wa.me/{phone}?text={msg}"
    return f"https://wa.me/{phone}"


@register.filter
def only_digits(value):
    """Deja solo dígitos (útil si guardas +56 9 1234 5678)."""
    return "".join(ch for ch in str(value or "") if ch.isdigit())


@register.simple_tag(takes_context=True)
def whatsapp_document_link(context, document=None, text=None):
    """
    Fallback robusto:
    - Devuelve un link wa.me con un mensaje armado.
    - No lanza excepción aunque falten datos.
    Uso: {% whatsapp_document_link documento "mensaje opcional" %}
    """
    try:
        request = context.get("request")
        host = request.get_host() if request else ""
        scheme = "https"
        if request:
            scheme = "https" if request.is_secure() else "http"
        base_url = f"{scheme}://{host}" if host else ""
    except Exception:
        base_url = ""

    # Número WhatsApp configurable (si existe)
    phone = getattr(settings, "WHATSAPP_DEFAULT_PHONE", "") or ""

    # Mensaje
    if not text:
        text = "Hola, te comparto tu documento."

    # Si tenemos document y tiene algún campo usable, lo agregamos
    try:
        if document is not None:
            # intenta varios nombres típicos
            num = (
                getattr(document, "numero", None)
                or getattr(document, "numero_documento", None)
                or getattr(document, "folio", None)
            )
            if num:
                text += f" N° {num}."
            # link al detalle si existe id/pk
            pk = getattr(document, "pk", None)
            if pk and base_url:
                # ruta genérica: ajusta si tienes una url named
                text += f" {base_url}/"
    except Exception:
        pass

    msg = quote(text)
    if phone:
        return f"https://wa.me/{phone}?text={msg}"
    return f"https://wa.me/?text={msg}"
