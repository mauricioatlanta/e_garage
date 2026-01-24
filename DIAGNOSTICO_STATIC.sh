#!/bin/bash
# Script de diagnóstico para STATIC_URL y configuración
# Ejecutar en el servidor como: sudo -u egarage -H bash -lc 'cd /srv/egarage && bash DIAGNOSTICO_STATIC.sh'

set -e

echo "=========================================="
echo "Diagnóstico de STATIC_URL y configuración"
echo "=========================================="

# Cargar variables de entorno
set -a
source /srv/egarage/.env
set +a

# Activar entorno virtual
source venv/bin/activate

echo ""
echo "1. Verificando settings.py..."
if [ -f "gestion_taller/settings.py" ]; then
    echo "✅ settings.py existe"
    echo ""
    echo "Buscando STATIC_URL en settings.py:"
    grep -n "STATIC_URL" gestion_taller/settings.py || echo "⚠️ STATIC_URL no encontrado en settings.py"
    echo ""
    echo "Buscando STORAGES en settings.py:"
    grep -n "STORAGES" gestion_taller/settings.py || echo "⚠️ STORAGES no encontrado en settings.py"
else
    echo "❌ settings.py no encontrado"
    exit 1
fi

echo ""
echo "2. Verificando configuración de Django..."
python -c "
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')

# Cargar settings
django.setup()

from django.conf import settings

print('✅ Django configurado correctamente')
print('')
print('Configuración de Static/Media:')
print('  STATIC_URL =', repr(settings.STATIC_URL))
print('  STATIC_ROOT =', repr(settings.STATIC_ROOT))
print('  MEDIA_URL =', repr(settings.MEDIA_URL))
print('  MEDIA_ROOT =', repr(settings.MEDIA_ROOT))
print('')
print('Configuración de STORAGES:')
if hasattr(settings, 'STORAGES'):
    print('  ✅ STORAGES existe')
    if 'staticfiles' in settings.STORAGES:
        print('  ✅ staticfiles en STORAGES')
        print('  Backend:', settings.STORAGES['staticfiles'].get('BACKEND', 'N/A'))
    else:
        print('  ❌ staticfiles NO está en STORAGES')
        print('  Claves disponibles:', list(settings.STORAGES.keys()))
else:
    print('  ⚠️ STORAGES no existe (puede ser Django < 5)')
    if hasattr(settings, 'STATICFILES_STORAGE'):
        print('  STATICFILES_STORAGE =', settings.STATICFILES_STORAGE)
print('')
print('DEBUG =', settings.DEBUG)
"

echo ""
echo "=========================================="
echo "Diagnóstico completado"
echo "=========================================="
