#!/bin/bash
# Script para encontrar la configuración de Nginx para egarage.cl

echo "=========================================="
echo "Buscando configuración de Nginx para egarage.cl"
echo "=========================================="
echo ""

# 1. Buscar en sites-enabled
echo "[1] Buscando en /etc/nginx/sites-enabled/"
if [ -d "/etc/nginx/sites-enabled" ]; then
    ls -la /etc/nginx/sites-enabled/ | grep -i egarage
    echo ""
else
    echo "  ❌ /etc/nginx/sites-enabled/ no existe"
    echo ""
fi

# 2. Buscar en sites-available
echo "[2] Buscando en /etc/nginx/sites-available/"
if [ -d "/etc/nginx/sites-available" ]; then
    ls -la /etc/nginx/sites-available/ | grep -i egarage
    echo ""
else
    echo "  ❌ /etc/nginx/sites-available/ no existe"
    echo ""
fi

# 3. Buscar en conf.d
echo "[3] Buscando en /etc/nginx/conf.d/"
if [ -d "/etc/nginx/conf.d" ]; then
    ls -la /etc/nginx/conf.d/ | grep -i egarage
    echo ""
else
    echo "  ❌ /etc/nginx/conf.d/ no existe"
    echo ""
fi

# 4. Buscar en nginx.conf principal
echo "[4] Buscando referencias a egarage en /etc/nginx/nginx.conf"
if [ -f "/etc/nginx/nginx.conf" ]; then
    grep -i "egarage\|include" /etc/nginx/nginx.conf | head -20
    echo ""
else
    echo "  ❌ /etc/nginx/nginx.conf no existe"
    echo ""
fi

# 5. Buscar en todos los archivos .conf de nginx
echo "[5] Buscando 'egarage' en todos los archivos .conf de Nginx"
find /etc/nginx -name "*.conf" -type f 2>/dev/null | while read file; do
    if grep -qi "egarage\|server_name.*egarage" "$file" 2>/dev/null; then
        echo "  ✅ Encontrado: $file"
        grep -i "egarage\|server_name" "$file" | head -5
        echo ""
    fi
done

# 6. Buscar por puerto 8001 (puerto típico de Gunicorn)
echo "[6] Buscando configuración que use puerto 8001"
find /etc/nginx -name "*.conf" -type f 2>/dev/null | while read file; do
    if grep -q "8001\|127.0.0.1:8001" "$file" 2>/dev/null; then
        echo "  ✅ Archivo con puerto 8001: $file"
        grep -A 5 -B 5 "8001\|127.0.0.1:8001" "$file" | head -15
        echo ""
    fi
done

# 7. Listar todos los archivos de configuración
echo "[7] Todos los archivos de configuración de Nginx:"
find /etc/nginx -name "*.conf" -type f 2>/dev/null | sort
echo ""

echo "=========================================="
echo "Búsqueda completada"
echo "=========================================="
echo ""
echo "💡 Si no encuentras nada, puede que:"
echo "   1. Nginx no esté instalado"
echo "   2. La configuración esté en otro lugar"
echo "   3. El dominio esté configurado con otro nombre"
echo ""
echo "Para verificar si Nginx está corriendo:"
echo "   sudo systemctl status nginx"
echo ""
