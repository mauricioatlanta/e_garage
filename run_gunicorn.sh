#!/bin/bash
# ============================================
# Script: Iniciar Gunicorn con variables de entorno
# Carga el .env antes de iniciar Gunicorn
# ============================================

# Cargar variables de entorno desde .env
# set -a exporta todas las variables automáticamente
set -a
source /srv/egarage/.env
set +a

# Directorio del proyecto
cd /srv/egarage/app || cd /srv/egarage || exit 1

# Activar virtualenv si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Iniciar Gunicorn
exec gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8001 \
    --timeout 30 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    gestion_taller.wsgi:application
