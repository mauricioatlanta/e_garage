#!/bin/bash
# Script para arreglar el servicio Gunicorn en /srv/egarage
# Ejecutar en el servidor: sudo bash fix_gunicorn_servicio.sh

set -e

APP_DIR="/srv/egarage"
SERVICE_NAME="egarage-gunicorn.service"
PORT="8001"

echo "=========================================="
echo "🔧 ARREGLANDO SERVICIO GUNICORN"
echo "=========================================="
echo ""

# Verificar que el directorio existe
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Error: No se encontró $APP_DIR"
    exit 1
fi

echo "✅ Directorio encontrado: $APP_DIR"
echo ""

# Verificar que manage.py existe
if [ ! -f "$APP_DIR/manage.py" ]; then
    echo "❌ Error: No se encontró manage.py en $APP_DIR"
    exit 1
fi

echo "✅ manage.py encontrado"
echo ""

# Verificar virtualenv
if [ ! -f "$APP_DIR/venv/bin/gunicorn" ]; then
    echo "⚠️  Virtualenv no encontrado o Gunicorn no instalado"
    echo "   Verificando si existe venv..."
    if [ -d "$APP_DIR/venv" ]; then
        echo "   ✅ venv existe, instalando Gunicorn..."
        source "$APP_DIR/venv/bin/activate"
        pip install gunicorn
    else
        echo "   ❌ venv no existe. Creando..."
        cd "$APP_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            pip install gunicorn django
        fi
    fi
else
    echo "✅ Gunicorn encontrado en venv"
fi

echo ""

# Detener el servicio si está corriendo
echo "🛑 Deteniendo servicio actual..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || true
systemctl stop gunicorn.service 2>/dev/null || true

echo ""

# Ver configuración actual del servicio
echo "📋 Configuración actual del servicio:"
if systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
    systemctl cat "$SERVICE_NAME"
    echo ""
    read -p "¿Deseas actualizar la configuración del servicio? (s/N): " -n 1 -r
    echo ""
    UPDATE_SERVICE=$REPLY
else
    echo "   Servicio no existe, se creará uno nuevo"
    UPDATE_SERVICE="s"
fi

if [[ $UPDATE_SERVICE =~ ^[Ss]$ ]]; then
    # Crear archivo de servicio
    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
    
    echo "📝 Creando/actualizando servicio systemd..."
    
    # Detectar usuario del directorio
    APP_USER=$(stat -c '%U' "$APP_DIR")
    APP_GROUP=$(stat -c '%G' "$APP_DIR")
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=eGarage Gunicorn
After=network.target postgresql.service

[Service]
Type=notify
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=gestion_taller.settings"
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:$PORT \\
    --timeout 120 \\
    --keep-alive 5 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --access-logfile $APP_DIR/logs/gunicorn-access.log \\
    --error-logfile $APP_DIR/logs/gunicorn-error.log \\
    gestion_taller.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Crear directorio de logs si no existe
    mkdir -p "$APP_DIR/logs"
    chown "$APP_USER:$APP_GROUP" "$APP_DIR/logs"
    
    echo "✅ Servicio creado en $SERVICE_FILE"
    echo ""
    
    # Recargar systemd
    echo "🔄 Recargando systemd..."
    systemctl daemon-reload
    
    # Habilitar servicio
    echo "✅ Habilitando servicio..."
    systemctl enable "$SERVICE_NAME"
    
    # Iniciar servicio
    echo "🚀 Iniciando servicio..."
    systemctl start "$SERVICE_NAME"
    
    # Esperar un momento
    sleep 3
    
    # Verificar estado
    echo ""
    echo "📊 Estado del servicio:"
    systemctl status "$SERVICE_NAME" --no-pager -l || true
    
    echo ""
    echo "🔍 Verificando que está escuchando en puerto $PORT..."
    if ss -tuln | grep -q ":$PORT "; then
        echo "✅ Gunicorn está escuchando en puerto $PORT"
    else
        echo "❌ Gunicorn NO está escuchando en puerto $PORT"
        echo ""
        echo "Revisa los logs:"
        echo "  sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
    fi
fi

echo ""
echo "=========================================="
echo "✅ PROCESO COMPLETADO"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo "1. Verificar estado: sudo systemctl status $SERVICE_NAME"
echo "2. Ver logs: sudo journalctl -u $SERVICE_NAME -f"
echo "3. Probar conexión: curl http://127.0.0.1:$PORT/"
echo "4. Recargar Nginx: sudo systemctl reload nginx"
