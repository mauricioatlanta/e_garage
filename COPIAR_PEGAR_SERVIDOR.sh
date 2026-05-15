#!/bin/bash
# Copia TODO este bloque y pégalo directamente en tu servidor Linux (SSH)

set -e

echo "========================================"
echo "🔧 Fix Error 500 Manual - DigitalOcean"
echo "========================================"
echo ""

# Paso 1: Limpiar y Corregir settings_prod.py
echo "▶ Paso 1: Limpiando y corrigiendo settings_prod.py..."

SETTINGS_FILE="/srv/egarage/gestion_taller/settings_prod.py"

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "❌ No se encontró settings_prod.py en: $SETTINGS_FILE"
    exit 1
fi

cp "$SETTINGS_FILE" "${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backup creado"

sed -i 's/\r//' "$SETTINGS_FILE"
echo "✅ Caracteres CRLF eliminados"

sed -i 's|/srv/egarage/app/|/srv/egarage/|g' "$SETTINGS_FILE"
echo "✅ Rutas corregidas (eliminado /app/)"

if grep -q "# --- FIX FINAL MANUAL ---" "$SETTINGS_FILE"; then
    echo "✅ El bloque de fix ya existe, actualizando..."
    sed -i '/# --- FIX FINAL MANUAL ---/,$d' "$SETTINGS_FILE"
fi

cat >> "$SETTINGS_FILE" << 'EOF'

# --- FIX FINAL MANUAL ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/srv/egarage/db.sqlite3",
    }
}
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ["https://egarage.cl", "https://www.egarage.cl"]
EOF

echo "✅ Configuración de emergencia agregada"

# Paso 2: Verificar Servicio Gunicorn
echo ""
echo "▶ Paso 2: Verificando servicio de Gunicorn..."

GUNICORN_SERVICE="/etc/systemd/system/gunicorn.service"

if [ -f "$GUNICORN_SERVICE" ]; then
    echo "✅ Archivo de servicio encontrado"
    echo ""
    echo "📋 Contenido actual:"
    cat "$GUNICORN_SERVICE"
    echo ""
    
    if grep -q "gestion_taller.settings_prod:application" "$GUNICORN_SERVICE"; then
        echo "✅ El servicio ya está configurado correctamente"
    else
        echo "⚠️  El servicio necesita corrección"
        echo "   Edita: sudo nano $GUNICORN_SERVICE"
        echo "   Asegúrate que ExecStart termine con: gestion_taller.settings_prod:application"
    fi
else
    echo "⚠️  No se encontró servicio systemd"
fi

# Paso 3: Reinicio de Limpieza Total
echo ""
echo "▶ Paso 3: Reinicio de Limpieza Total..."

echo "   1. Ajustando permisos..."
sudo chown -R www-data:www-data /srv/egarage
sudo chmod 664 /srv/egarage/db.sqlite3 2>/dev/null || echo "   ⚠️  db.sqlite3 no existe aún"
echo "   ✅ Permisos ajustados"

echo "   2. Recolectando archivos estáticos..."
if [ -f "/srv/egarage/venv/bin/python" ]; then
    /srv/egarage/venv/bin/python /srv/egarage/manage.py collectstatic --noinput
else
    python3 /srv/egarage/manage.py collectstatic --noinput
fi
echo "   ✅ Archivos estáticos recolectados"

echo "   3. Reiniciando servicios..."
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl restart nginx
echo "   ✅ Servicios reiniciados"

echo ""
echo "========================================"
echo "✅ Fix completado!"
echo "========================================"
echo ""
echo "📋 Refresca https://www.egarage.cl"
echo "📋 Si el Error 500 persiste: journalctl -u gunicorn -f"
echo ""
