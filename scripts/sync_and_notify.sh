#!/bin/bash
# Script para ejecutar sync_subscriptions y notificar_vencimientos en secuencia
# 
# Uso en crontab:
# 0 2 * * * /ruta/completa/al/proyecto/scripts/sync_and_notify.sh >> /var/log/egarage_subscriptions.log 2>&1

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

# Fecha y hora de ejecución
echo "=========================================="
echo "Ejecución: $(date)"
echo "=========================================="

# Paso 1: Sincronizar estado de suscripciones
echo "[PASO 1] Sincronizando estado de suscripciones..."
python manage.py sync_subscriptions

SYNC_EXIT_CODE=$?
if [ $SYNC_EXIT_CODE -ne 0 ]; then
    echo "[ERROR] Falló la sincronización. Código de salida: $SYNC_EXIT_CODE"
    exit $SYNC_EXIT_CODE
fi

# Paso 2: Enviar notificaciones
echo ""
echo "[PASO 2] Enviando notificaciones de vencimiento..."
python manage.py notificar_vencimientos

NOTIFY_EXIT_CODE=$?
if [ $NOTIFY_EXIT_CODE -ne 0 ]; then
    echo "[ERROR] Falló el envío de notificaciones. Código de salida: $NOTIFY_EXIT_CODE"
    exit $NOTIFY_EXIT_CODE
fi

echo ""
echo "=========================================="
echo "[OK] Proceso completado exitosamente"
echo "=========================================="

exit 0
