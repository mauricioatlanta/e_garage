#!/bin/bash
# Script para verificar y corregir la configuración de X-Forwarded-Proto en Nginx
# Ejecutar en el servidor: sudo bash fix_nginx_x_forwarded_proto.sh

set -e

echo "=========================================="
echo "🔍 Verificando configuración de Nginx"
echo "=========================================="
echo ""

# 1. Buscar archivo de configuración que use puerto 8001
echo "[1] Buscando configuración que use proxy_pass a 127.0.0.1:8001..."
echo ""

CONFIG_FILES=$(sudo grep -r "proxy_pass.*8001" /etc/nginx/sites-enabled /etc/nginx/sites-available 2>/dev/null | cut -d: -f1 | sort -u)

if [ -z "$CONFIG_FILES" ]; then
    echo "❌ No se encontró configuración con proxy_pass a puerto 8001"
    echo ""
    echo "Buscando en todos los archivos de Nginx..."
    CONFIG_FILES=$(sudo find /etc/nginx -name "*.conf" -type f 2>/dev/null | grep -i egarage || echo "")
    
    if [ -z "$CONFIG_FILES" ]; then
        echo "❌ No se encontró configuración para egarage"
        echo ""
        echo "Archivos en /etc/nginx/sites-enabled/:"
        sudo ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "  (no existe)"
        echo ""
        echo "Archivos en /etc/nginx/sites-available/:"
        sudo ls -la /etc/nginx/sites-available/ 2>/dev/null || echo "  (no existe)"
        exit 1
    fi
fi

echo "✅ Archivos de configuración encontrados:"
echo "$CONFIG_FILES" | while read file; do
    echo "   - $file"
done
echo ""

# 2. Verificar cada archivo
for CONFIG_FILE in $CONFIG_FILES; do
    echo "=========================================="
    echo "📄 Analizando: $CONFIG_FILE"
    echo "=========================================="
    echo ""
    
    # Verificar si tiene X-Forwarded-Proto
    if sudo grep -q "X-Forwarded-Proto" "$CONFIG_FILE"; then
        echo "✅ Header X-Forwarded-Proto encontrado"
        sudo grep "X-Forwarded-Proto" "$CONFIG_FILE" | head -1
    else
        echo "❌ Header X-Forwarded-Proto NO encontrado"
        echo ""
        echo "📝 Mostrando bloque location / { ... } actual:"
        sudo grep -A 20 "location / {" "$CONFIG_FILE" | head -25 || echo "  (no se encontró location /)"
        echo ""
        echo "⚠️  NECESITA AGREGARSE el header X-Forwarded-Proto"
    fi
    echo ""
    
    # Verificar otros headers importantes
    echo "📋 Headers proxy actuales:"
    sudo grep "proxy_set_header" "$CONFIG_FILE" || echo "  (ninguno encontrado)"
    echo ""
done

# 3. Mostrar logs de error de Nginx
echo "=========================================="
echo "📋 Últimas 80 líneas de error.log de Nginx"
echo "=========================================="
echo ""
sudo tail -n 80 /var/log/nginx/error.log 2>/dev/null || echo "  (no se pudo leer el log)"
echo ""

# 4. Instrucciones para corregir
echo "=========================================="
echo "🔧 INSTRUCCIONES PARA CORREGIR"
echo "=========================================="
echo ""
echo "Si falta el header X-Forwarded-Proto, edita el archivo:"
echo ""
for CONFIG_FILE in $CONFIG_FILES; do
    echo "   sudo nano $CONFIG_FILE"
done
echo ""
echo "En el bloque 'location / { ... }' que tiene 'proxy_pass http://127.0.0.1:8001;'"
echo "asegúrate de tener estas líneas:"
echo ""
echo "   location / {"
echo "       proxy_pass http://127.0.0.1:8001;"
echo "       proxy_set_header Host \$host;"
echo "       proxy_set_header X-Real-IP \$remote_addr;"
echo "       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
echo "       proxy_set_header X-Forwarded-Proto \$scheme;  # 🔥 CRÍTICO"
echo "   }"
echo ""
echo "Luego verifica y recarga Nginx:"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "=========================================="
echo "✅ Verificación completada"
echo "=========================================="
