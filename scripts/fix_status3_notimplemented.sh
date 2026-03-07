#!/bin/bash
# Script para arreglar error status=3/NOTIMPLEMENTED
# Ejecutar en el servidor: sudo bash fix_status3_notimplemented.sh

set -e

SERVICE_NAME="egarage-gunicorn.service"
APP_DIR="/srv/egarage"
LOG_DIR="$APP_DIR/logs"

echo "=========================================="
echo "🔧 ARREGLANDO ERROR STATUS=3/NOTIMPLEMENTED"
echo "=========================================="
echo ""

# 1. Detener el servicio
echo "🛑 Deteniendo servicio..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
sleep 2

# 2. Crear directorio de logs si no existe
echo "📁 Verificando directorio de logs..."
mkdir -p "$LOG_DIR"
chown -R egarage:www-data "$LOG_DIR"
chmod -R 755 "$LOG_DIR"
echo "✅ Logs configurados"

# 3. Verificar que los archivos de log existan
touch "$LOG_DIR/gunicorn_access.log"
touch "$LOG_DIR/gunicorn_error.log"
chown egarage:www-data "$LOG_DIR"/*.log
chmod 644 "$LOG_DIR"/*.log
echo "✅ Archivos de log creados"

# 4. Arreglar el override.conf
echo "📝 Actualizando configuración del servicio..."
OVERRIDE_FILE="/etc/systemd/system/$SERVICE_NAME.d/override.conf"
mkdir -p "$(dirname "$OVERRIDE_FILE")"

cat > "$OVERRIDE_FILE" << 'EOF'
[Service]
Type=simple
RuntimeDirectory=egarage
RuntimeDirectoryMode=0755
UMask=0007

ExecStartPre=/bin/rm -f /run/egarage/gunicorn.sock

ExecStart=
ExecStart=/srv/egarage/venv/bin/gunicorn gestion_taller.wsgi:application \
  --name egarage \
  --workers 3 \
  --bind 127.0.0.1:8001 \
  --access-logfile /srv/egarage/logs/gunicorn_access.log \
  --error-logfile /srv/egarage/logs/gunicorn_error.log \
  --capture-output \
  --log-level info \
  --timeout 120 \
  --keep-alive 5
EOF

echo "✅ Configuración actualizada"

# 5. Recargar systemd
echo "🔄 Recargando systemd..."
systemctl daemon-reload

# 6. Iniciar servicio
echo "🚀 Iniciando servicio..."
systemctl start "$SERVICE_NAME"

# 7. Esperar un momento
sleep 3

# 8. Verificar estado
echo ""
echo "📊 Estado del servicio:"
systemctl status "$SERVICE_NAME" --no-pager -l | head -30

echo ""
echo "🔍 Verificando puerto 8001..."
if ss -tuln | grep -q ":8001 "; then
    echo "✅ Gunicorn está escuchando en puerto 8001"
else
    echo "❌ Gunicorn NO está escuchando"
    echo ""
    echo "Revisa los logs:"
    echo "  sudo tail -50 $LOG_DIR/gunicorn_error.log"
    echo "  sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
fi

echo ""
echo "=========================================="
echo "✅ PROCESO COMPLETADO"
echo "=========================================="
