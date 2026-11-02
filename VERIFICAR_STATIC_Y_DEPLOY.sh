#!/bin/bash
# Script para verificar STATIC_URL/STATIC_ROOT y ejecutar deploy completo
# Ejecutar en el servidor como: sudo -u egarage -H bash -lc 'cd /srv/egarage && bash VERIFICAR_STATIC_Y_DEPLOY.sh'

set -e  # Salir si hay error

echo "=========================================="
echo "Paso 3: Verificando STATIC_URL y STATIC_ROOT"
echo "=========================================="

# Cargar variables de entorno
set -a
source /srv/egarage/.env
set +a

# Activar entorno virtual
source venv/bin/activate

# Verificar configuración
python -c "
from django.conf import settings
print('✅ STATIC_URL =', settings.STATIC_URL)
print('✅ STATIC_ROOT =', settings.STATIC_ROOT)
print('✅ MEDIA_URL =', settings.MEDIA_URL)
print('✅ MEDIA_ROOT =', settings.MEDIA_ROOT)
if hasattr(settings, 'STORAGES'):
    print('✅ STORAGES configurado:', 'staticfiles' in settings.STORAGES)
else:
    print('⚠️ STORAGES no encontrado (puede ser Django < 5)')
"

echo ""
echo "=========================================="
echo "Paso 4: Ejecutando deploy completo"
echo "=========================================="

echo "1. Ejecutando check..."
python manage.py check

echo ""
echo "2. Ejecutando migrate..."
python manage.py migrate --noinput

echo ""
echo "3. Ejecutando collectstatic..."
python manage.py collectstatic --noinput

echo ""
echo "=========================================="
echo "✅ Deploy completo finalizado"
echo "=========================================="
echo ""
echo "Próximos pasos (como root):"
echo "  sudo systemctl restart egarage-gunicorn"
echo "  sudo systemctl reload nginx"
