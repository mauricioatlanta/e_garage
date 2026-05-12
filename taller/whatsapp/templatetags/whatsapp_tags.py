"""
Template tags para WhatsApp
"""
from django import template

from taller.utils.whatsapp_helper import get_document_whatsapp_url

register = template.Library()


@register.simple_tag
def whatsapp_document_link(documento, request=None):
    """
    Genera link de WhatsApp para enviar documento a cliente
    
    Usage:
        {% whatsapp_document_link documento request as wa_link %}
        {% if wa_link %}
            <a href="{{ wa_link }}">Enviar por WhatsApp</a>
        {% endif %}
    """
    return get_document_whatsapp_url(documento, request=request)


@register.filter
def has_whatsapp(cliente):
    """Verificar si cliente tiene teléfono para WhatsApp"""
    if not cliente:
        return False
    telefono = getattr(cliente, "telefono", None) or getattr(cliente, "phone", None)
    return bool(telefono)
