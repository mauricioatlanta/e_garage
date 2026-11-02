#!/bin/bash
# Fix directo: crear el template tag whatsapp_document_link faltante
# Ejecutar en el servidor: sudo -u egarage -H bash -lc 'bash FIX_WHATSAPP_TAG.sh'

set -e

echo "========================================"
echo "🔧 Fix Template Tag: whatsapp_document_link"
echo "========================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d "/srv/egarage/taller/templatetags" ]; then
    echo "❌ No se encontró /srv/egarage/taller/templatetags"
    exit 1
fi

# Backup del archivo existente
WHATSAPP_TAGS_FILE="/srv/egarage/taller/templatetags/whatsapp_tags.py"
if [ -f "$WHATSAPP_TAGS_FILE" ]; then
    cp "$WHATSAPP_TAGS_FILE" "${WHATSAPP_TAGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup creado: ${WHATSAPP_TAGS_FILE}.backup.*"
fi

# Asegurar que __init__.py existe
if [ ! -f "/srv/egarage/taller/templatetags/__init__.py" ]; then
    touch /srv/egarage/taller/templatetags/__init__.py
    echo "✅ __init__.py creado"
fi

# Agregar el tag faltante al archivo existente
cat >> "$WHATSAPP_TAGS_FILE" << 'PYEOF'

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
    from django.conf import settings
    phone = getattr(settings, "WHATSAPP_DEFAULT_PHONE", "") or ""

    # Mensaje
    if not text:
        text = "Hola, te comparto tu documento."

    # Si tenemos document y tiene algún campo usable, lo agregamos
    try:
        if document is not None:
            # intenta varios nombres típicos
            num = getattr(document, "numero", None) or getattr(document, "numero_documento", None) or getattr(document, "folio", None)
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
PYEOF

echo "✅ Template tag whatsapp_document_link agregado"

# Verificar sintaxis Python
echo ""
echo "▶ Verificando sintaxis Python..."
python3 -m py_compile "$WHATSAPP_TAGS_FILE" 2>&1 && echo "✅ Sintaxis correcta" || {
    echo "❌ Error de sintaxis en el archivo"
    exit 1
}

echo ""
echo "========================================"
echo "✅ Paso 1 completado: Template tag creado"
echo "========================================"
echo ""
echo "▶ Siguiente paso: Reiniciar gunicorn"
echo "   sudo systemctl restart egarage-gunicorn"
echo ""
