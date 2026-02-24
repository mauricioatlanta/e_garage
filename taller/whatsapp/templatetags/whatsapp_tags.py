"""
Template tags para WhatsApp
"""
from django import template
from django.urls import reverse

from taller.whatsapp.helpers import build_wa_link, build_document_wa_message, normalize_phone

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
    if not documento or not documento.cliente:
        return None
    
    cliente = documento.cliente
    telefono = getattr(cliente, "telefono", None) or getattr(cliente, "phone", None)
    
    if not telefono:
        return None
    
    # Obtener país de la empresa para normalizar teléfono
    empresa = documento.empresa
    country_code = "56"  # Default Chile
    if hasattr(empresa, "pais"):
        country_map = {
            "CL": "56",
            "US": "1",
            "MX": "52",
            "BR": "55",
            "PE": "51",
            "CO": "57",
            "VE": "58",
            "EC": "593",
            "AR": "54",
            "UY": "598",
        }
        country_code = country_map.get(empresa.pais.upper(), "56")
    
    # Obtener información del documento
    tipo_doc = documento.get_tipo_display() or documento.tipo_documento or "Documento"
    numero_doc = documento.numero_documento or documento.numero or str(documento.id)
    total = float(documento.total) if documento.total else 0.0
    empresa_nombre = empresa.nombre_taller
    
    # Información del vehículo
    vehiculo_info = None
    if hasattr(documento, "vehiculo") and documento.vehiculo:
        vehiculo = documento.vehiculo
        marca = getattr(vehiculo, "marca", None)
        modelo = getattr(vehiculo, "modelo", None)
        patente = getattr(vehiculo, "patente", "")
        
        if marca and modelo:
            vehiculo_info = f"{marca} {modelo} ({patente})"
        elif marca:
            vehiculo_info = f"{marca} ({patente})"
        else:
            vehiculo_info = patente or "N/A"
    
    # URL del documento
    # 🔒 FASE 1: Priorizar PDF solo si es accesible sin login; si no, usar URL interna con mensaje
    url_documento = None
    pdf_requires_login = True  # Por defecto, PDF requiere login
    url_documento_requires_login = True
    
    if request:
        try:
            # 1. Prioridad: URL pública con token (seguimiento_publico) - NO requiere login ✅
            if hasattr(documento, "seguimiento_publico") and documento.seguimiento_publico:
                try:
                    url_documento = request.build_absolute_uri(
                        reverse("documentos:seguimiento_publico", kwargs={"token": documento.seguimiento_publico.token})
                    )
                    url_documento_requires_login = False
                except Exception:
                    pass
            
            # 2. Fallback: URL pública con UUID (si tiene UUID y es presupuesto) - NO requiere login ✅
            if not url_documento and hasattr(documento, "uuid") and documento.uuid and documento.tipo_documento == "PRES":
                try:
                    url_documento = request.build_absolute_uri(
                        reverse("publico:ver_presupuesto", kwargs={"uuid": documento.uuid})
                    )
                    url_documento_requires_login = False
                except Exception:
                    pass
            
            # 3. Intentar PDF público (si existe endpoint público)
            if not url_documento:
                try:
                    # Intentar endpoint público de PDF (fase 2 - preparado pero no implementado)
                    url_documento = request.build_absolute_uri(
                        reverse("documentos:descargar_pdf_public", kwargs={"pk": documento.id})
                    )
                    pdf_requires_login = False
                    url_documento_requires_login = False
                except Exception:
                    # Si no existe endpoint público, intentar PDF normal (requiere login)
                    try:
                        url_documento = request.build_absolute_uri(
                            reverse("documentos:descargar_pdf", kwargs={"pk": documento.id})
                        )
                        pdf_requires_login = True  # PDF normal requiere @login_required
                        url_documento_requires_login = True
                    except Exception:
                        pass
            
            # 4. Último recurso: URL interna (requiere login)
            if not url_documento:
                try:
                    url_documento = request.build_absolute_uri(
                        reverse("documentos:ver_documento", kwargs={"pk": documento.id})
                    )
                    url_documento_requires_login = True
                except Exception:
                    pass
        except Exception:
            pass
    
    # Determinar idioma
    language = "es"
    if hasattr(empresa, "pais") and empresa.pais == "US":
        language = "en"
    
    # Construir mensaje (agregar aviso si requiere login)
    mensaje_adicional = ""
    if url_documento and url_documento_requires_login:
        if language == "en":
            mensaje_adicional = "\n\n⚠️ Note: This link requires login. If it doesn't open, please request the PDF directly."
        else:
            mensaje_adicional = "\n\n⚠️ Nota: Este enlace requiere acceso. Si no abre, solicite el PDF directamente."
    
    # Construir mensaje
    mensaje = build_document_wa_message(
        documento=documento,
        cliente_nombre=cliente.nombre or "Cliente",
        tipo_doc=tipo_doc,
        numero_doc=numero_doc,
        total=total,
        empresa_nombre=empresa_nombre,
        url_documento=url_documento,
        vehiculo_info=vehiculo_info,
        language=language,
    )
    
    # Agregar mensaje adicional si requiere login
    if mensaje_adicional:
        mensaje += mensaje_adicional
    
    # 🔒 VALIDACIÓN: Verificar longitud mínima del teléfono según país
    from taller.whatsapp.helpers import validate_phone_length, normalize_phone
    
    # Normalizar teléfono para validación
    normalized_phone = normalize_phone(telefono, country_code)
    
    # Obtener código de país de 2 letras para validación
    country_code_2letter = empresa.pais.upper() if hasattr(empresa, "pais") else "CL"
    
    # Validar longitud mínima
    if not validate_phone_length(normalized_phone, country_code_2letter):
        # Teléfono no cumple longitud mínima, retornar None (botón se deshabilitará)
        return None
    
    # Construir link
    return build_wa_link(telefono, mensaje, country_code)


@register.filter
def has_whatsapp(cliente):
    """Verificar si cliente tiene teléfono para WhatsApp"""
    if not cliente:
        return False
    telefono = getattr(cliente, "telefono", None) or getattr(cliente, "phone", None)
    return bool(telefono)
