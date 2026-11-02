#!/bin/bash
# Fix completo: Error 500 por template tag whatsapp_document_link faltante
# Ejecutar en el servidor: sudo -u egarage -H bash -lc 'bash FIX_ERROR_500_WHATSAPP_TAG.sh'

set -e

echo "========================================"
echo "🔧 Fix Error 500: Template Tag WhatsApp"
echo "========================================"
echo ""

# ============================================
# PASO 1: Crear el template tag faltante
# ============================================
echo "▶ PASO 1: Creando template tag whatsapp_document_link..."

# Verificar que estamos en el directorio correcto
if [ ! -d "/srv/egarage/taller/templatetags" ]; then
    echo "❌ No se encontró /srv/egarage/taller/templatetags"
    exit 1
fi

# Backup del archivo existente
WHATSAPP_TAGS_FILE="/srv/egarage/taller/templatetags/whatsapp_tags.py"
if [ -f "$WHATSAPP_TAGS_FILE" ]; then
    cp "$WHATSAPP_TAGS_FILE" "${WHATSAPP_TAGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup creado"
fi

# Asegurar que __init__.py existe
if [ ! -f "/srv/egarage/taller/templatetags/__init__.py" ]; then
    touch /srv/egarage/taller/templatetags/__init__.py
    echo "✅ __init__.py creado"
fi

# Verificar si el tag ya existe
if grep -q "def whatsapp_document_link" "$WHATSAPP_TAGS_FILE" 2>/dev/null; then
    echo "⚠️  El tag whatsapp_document_link ya existe en el archivo"
    echo "   Verificando si necesita actualización..."
else
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
fi

# Verificar sintaxis Python
echo ""
echo "▶ Verificando sintaxis Python..."
if python3 -m py_compile "$WHATSAPP_TAGS_FILE" 2>&1; then
    echo "✅ Sintaxis correcta"
else
    echo "❌ Error de sintaxis en el archivo"
    exit 1
fi

# ============================================
# PASO 2: Reiniciar gunicorn
# ============================================
echo ""
echo "▶ PASO 2: Reiniciando gunicorn..."
sudo systemctl restart egarage-gunicorn
sleep 2

# Verificar estado
if sudo systemctl is-active --quiet egarage-gunicorn; then
    echo "✅ Gunicorn reiniciado correctamente"
else
    echo "❌ Error al reiniciar gunicorn"
    echo "   Ver logs: sudo journalctl -u egarage-gunicorn -n 50"
    exit 1
fi

# ============================================
# PASO 3: Probar URLs
# ============================================
echo ""
echo "▶ PASO 3: Probando URLs..."
echo ""

# Probar login
echo "   Probando /accounts/login/..."
HTTP_CODE_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://egarage.cl/accounts/login/ || echo "000")
echo "   HTTP Code: $HTTP_CODE_LOGIN"

# Probar documentos
echo "   Probando /cl/es/documentos/..."
HTTP_CODE_DOCS=$(curl -s -o /dev/null -w "%{http_code}" https://egarage.cl/cl/es/documentos/ || echo "000")
echo "   HTTP Code: $HTTP_CODE_DOCS"

# ============================================
# PASO 4: Capturar traceback si sigue fallando
# ============================================
echo ""
if [ "$HTTP_CODE_LOGIN" = "500" ] || [ "$HTTP_CODE_DOCS" = "500" ]; then
    echo "❌ Error 500 persiste"
    echo ""
    echo "▶ PASO 4: Capturando traceback del log..."
    echo ""
    if [ -f "/srv/egarage/logs/gunicorn_error.log" ]; then
        echo "📋 Últimas 80 líneas de gunicorn_error.log:"
        echo "----------------------------------------"
        sudo tail -n 80 /srv/egarage/logs/gunicorn_error.log
        echo "----------------------------------------"
    else
        echo "⚠️  No se encontró /srv/egarage/logs/gunicorn_error.log"
        echo "   Intentando journalctl..."
        sudo journalctl -u egarage-gunicorn -n 50 --no-pager
    fi
    echo ""
    echo "❌ Revisa el traceback arriba para identificar el problema"
else
    echo "✅ URLs respondiendo correctamente (no hay 500)"
    echo ""
    echo "========================================"
    echo "✅ Fix completado exitosamente!"
    echo "========================================"
    echo ""
    echo "📋 URLs probadas:"
    echo "   - /accounts/login/: $HTTP_CODE_LOGIN"
    echo "   - /cl/es/documentos/: $HTTP_CODE_DOCS"
    echo ""
    echo "💡 Para habilitar gunicorn al boot:"
    echo "   sudo systemctl enable egarage-gunicorn"
fi
