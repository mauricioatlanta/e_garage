#!/bin/bash
# Script para arreglar ModuleNotFoundError y collectstatic en el servidor
# Ejecutar como: sudo -u egarage -H bash -lc '/srv/egarage/FIX_SERVIDOR_SIGNUP_STATIC.sh'

set -e  # Salir si hay error

cd /srv/egarage
set -a; source /srv/egarage/.env; set +a
source venv/bin/activate

echo "=========================================="
echo "FIX 1: Crear signup_redirects.py"
echo "=========================================="

# Crear el archivo signup_redirects.py si no existe
SIGNUP_FILE="/srv/egarage/taller/views_extra/signup_redirects.py"
if [ ! -f "$SIGNUP_FILE" ]; then
    echo "Creando $SIGNUP_FILE..."
    mkdir -p "$(dirname "$SIGNUP_FILE")"
    cat > "$SIGNUP_FILE" << 'EOF'
"""
Redirect universal para signup por país.

Este módulo proporciona una función de redirect centralizada que redirige
todas las rutas de signup por país (/xx/es/accounts/signup/) a la ruta
unificada /accounts/signup/ con un parámetro ?from=xx para indicar el país.

Esto simplifica el mantenimiento y evita duplicar templates por país.
"""

from django.shortcuts import redirect


def signup_redirect(request, country_code: str):
    """
    Redirige a /accounts/signup/ con el parámetro from=country_code.

    Args:
        request: El objeto request de Django
        country_code: Código del país (ej: "br", "co", "cl", "us")

    Returns:
        HttpResponseRedirect a /accounts/signup/?from=country_code

    Ejemplo:
        >>> signup_redirect(request, "br")
        # Redirige a: /accounts/signup/?from=br
    """
    # Normalizar código de país a minúsculas
    country_code_lower = country_code.lower()
    
    # Redirigir a la ruta unificada con el parámetro from
    return redirect(f"/accounts/signup/?from={country_code_lower}")
EOF
    echo "✅ Archivo creado"
else
    echo "✅ Archivo ya existe"
fi

# Validar import
echo "Validando import..."
python -c "from taller.views_extra.signup_redirects import signup_redirect; print('✅ Import OK:', signup_redirect)"

echo ""
echo "=========================================="
echo "FIX 2: Verificar STATIC_URL en settings"
echo "=========================================="

# Verificar qué settings está usando
DJANGO_SETTINGS_MODULE=$(python -c "import os; print(os.environ.get('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings'))")
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

STATIC_URL=$(python -c "from django.conf import settings; print('STATIC_URL=', getattr(settings, 'STATIC_URL', None))")
echo "$STATIC_URL"

if [ -z "$STATIC_URL" ] || [[ "$STATIC_URL" == *"None"* ]]; then
    echo "⚠️  STATIC_URL no está definido. Necesitas agregarlo al archivo de settings."
    echo "   Busca el archivo que corresponde a $DJANGO_SETTINGS_MODULE y agrega:"
    echo "   STATIC_URL = '/static/'"
    echo "   STATIC_ROOT = BASE_DIR / 'staticfiles'"
    exit 1
else
    echo "✅ STATIC_URL está definido"
fi

echo ""
echo "=========================================="
echo "FIX 3: Limpiar .pyc fantasma (opcional)"
echo "=========================================="

# Limpiar .pyc fantasma
PYC_FILE="/srv/egarage/taller/views_extra/__pycache__/signup_redirects*.pyc"
if ls $PYC_FILE 1> /dev/null 2>&1; then
    echo "Eliminando .pyc fantasma..."
    rm -f $PYC_FILE
    echo "✅ .pyc eliminado"
else
    echo "✅ No hay .pyc fantasma"
fi

echo ""
echo "=========================================="
echo "FIX 4: Ejecutar deploy"
echo "=========================================="

echo "Ejecutando check..."
python manage.py check

echo "Ejecutando migrate..."
python manage.py migrate --noinput

echo "Ejecutando collectstatic..."
python manage.py collectstatic --noinput

echo ""
echo "=========================================="
echo "✅ TODOS LOS FIXES APLICADOS"
echo "=========================================="
