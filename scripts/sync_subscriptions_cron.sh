#!/bin/bash
# Script para ejecutar sync_subscriptions.py como cron job
# 
# Uso en crontab:
# 0 2 * * * /ruta/completa/al/proyecto/scripts/sync_subscriptions_cron.sh >> /var/log/egarage_sync_subscriptions.log 2>&1

# Cambiar al directorio del proyecto
cd "$(dirname "$0")/.." || exit 1

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "env" ]; then
    source env/bin/activate
fi

# Ejecutar el comando
python manage.py sync_subscriptions

# Código de salida
exit $?
