#!/bin/bash
# Script para verificar configuraciones de Django y Nginx para Cloudflare

echo "=========================================="
echo "🔍 VERIFICACIÓN DE CONFIGURACIÓN PROXY"
echo "=========================================="
echo ""

# 1. Verificar configuraciones de Django
echo "1️⃣ Verificando configuraciones de Django..."
sudo -u egarage -H bash -lc '
cd /srv/egarage
set -a; source /srv/egarage/.env; set +a
/srv/egarage/venv/bin/python - <<PY
from django.conf import settings
print("SECURE_PROXY_SSL_HEADER:", getattr(settings,"SECURE_PROXY_SSL_HEADER", None))
print("SECURE_SSL_REDIRECT:", getattr(settings,"SECURE_SSL_REDIRECT", None))
PY
'

echo ""
echo "2️⃣ Verificando estado de Gunicorn..."
sudo systemctl reset-failed egarage-gunicorn
sudo systemctl restart egarage-gunicorn
if systemctl is-active egarage-gunicorn; then
    echo "✅ Gunicorn está activo y estable"
else
    echo "❌ Gunicorn NO está activo"
    sudo systemctl status egarage-gunicorn
fi

echo ""
echo "3️⃣ Verificando configuración de Nginx..."
echo "Mostrando primeras 240 líneas de /etc/nginx/sites-available/egarage:"
echo "----------------------------------------"
sudo sed -n '1,240p' /etc/nginx/sites-available/egarage

echo ""
echo "4️⃣ Verificando sintaxis de Nginx..."
if sudo nginx -t; then
    echo "✅ Configuración de Nginx es válida"
else
    echo "❌ Hay errores en la configuración de Nginx"
fi

echo ""
echo "=========================================="
echo "✅ Verificación completada"
echo "=========================================="
