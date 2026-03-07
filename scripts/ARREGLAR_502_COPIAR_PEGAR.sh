#!/bin/bash
# ==========================================
# COPIAR Y PEGAR ESTE SCRIPT COMPLETO EN EL SERVIDOR
# Ejecutar: sudo bash -c "$(cat << 'SCRIPT'
# ... (todo el contenido)
# SCRIPT
# )"
# ==========================================

APP_DIR="/srv/egarage"
SERVICE_NAME="egarage-gunicorn.service"
PORT="8001"

echo "=========================================="
echo "🔧 ARREGLANDO SERVICIO GUNICORN"
echo "=========================================="

# 1. Verificar directorio
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Error: No se encontró $APP_DIR"
    exit 1
fi
echo "✅ Directorio: $APP_DIR"

# 2. Detener servicios
echo "🛑 Deteniendo servicios..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl stop gunicorn.service 2>/dev/null || true

# 3. Detectar usuario
APP_USER=$(stat -c '%U' "$APP_DIR")
APP_GROUP=$(stat -c '%G' "$APP_DIR")
echo "✅ Usuario: $APP_USER, Grupo: $APP_GROUP"

# 4. Crear directorio de logs
mkdir -p "$APP_DIR/logs"
chown "$APP_USER:$APP_GROUP" "$APP_DIR/logs"

# 5. Crear servicio systemd
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=eGarage Gunicorn
After=network.target postgresql.service

[Service]
Type=notify
User=APP_USER_PLACEHOLDER
Group=APP_GROUP_PLACEHOLDER
WorkingDirectory=APP_DIR_PLACEHOLDER
Environment="PATH=APP_DIR_PLACEHOLDER/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_taller.settings"
ExecStart=APP_DIR_PLACEHOLDER/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8001 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile APP_DIR_PLACEHOLDER/logs/gunicorn-access.log \
    --error-logfile APP_DIR_PLACEHOLDER/logs/gunicorn-error.log \
    gestion_taller.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reemplazar placeholders
sed -i "s|APP_USER_PLACEHOLDER|$APP_USER|g" "$SERVICE_FILE"
sed -i "s|APP_GROUP_PLACEHOLDER|$APP_GROUP|g" "$SERVICE_FILE"
sed -i "s|APP_DIR_PLACEHOLDER|$APP_DIR|g" "$SERVICE_FILE"

echo "✅ Servicio creado"

# 6. Recargar y habilitar
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# 7. Esperar y verificar
sleep 3
echo ""
echo "📊 Estado:"
systemctl status "$SERVICE_NAME" --no-pager -l | head -20

echo ""
echo "🔍 Verificando puerto $PORT..."
if ss -tuln | grep -q ":$PORT "; then
    echo "✅ Gunicorn está escuchando en puerto $PORT"
    echo ""
    echo "🎉 ¡Listo! Ahora recarga Nginx:"
    echo "   sudo systemctl reload nginx"
else
    echo "❌ Gunicorn NO está escuchando"
    echo ""
    echo "Revisa los logs:"
    echo "   sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
fi
