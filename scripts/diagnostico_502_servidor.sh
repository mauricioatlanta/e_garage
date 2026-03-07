#!/bin/bash
# Script de diagnóstico 502 - Ejecutar directamente en el servidor
# Copiar y pegar este contenido en el servidor o ejecutar línea por línea

echo "=========================================="
echo "🔍 DIAGNÓSTICO 502 BAD GATEWAY"
echo "=========================================="
echo ""

# 1. Buscar servicios relacionados
echo "1️⃣  Buscando servicios Gunicorn/Egarage..."
echo "----------------------------------------"
systemctl list-units --all | grep -E "(gunicorn|egarage)" || echo "❌ No se encontraron servicios"
echo ""

# 2. Buscar procesos de Gunicorn
echo "2️⃣  Buscando procesos Gunicorn corriendo..."
echo "----------------------------------------"
ps aux | grep gunicorn | grep -v grep || echo "❌ No hay procesos Gunicorn corriendo"
echo ""

# 3. Buscar sockets
echo "3️⃣  Buscando sockets Unix..."
echo "----------------------------------------"
find /opt /var/www /srv /tmp -name "*.sock" -type s 2>/dev/null | head -10 || echo "❌ No se encontraron sockets"
echo ""

# 4. Verificar puertos TCP
echo "4️⃣  Verificando puertos TCP (8000, 8001, 8002)..."
echo "----------------------------------------"
netstat -tuln 2>/dev/null | grep -E ":(8000|8001|8002) " || ss -tuln 2>/dev/null | grep -E ":(8000|8001|8002) " || echo "❌ No se encontraron puertos en uso"
echo ""

# 5. Verificar configuración de Nginx
echo "5️⃣  Verificando configuración de Nginx..."
echo "----------------------------------------"
echo "Archivos de configuración encontrados:"
ls -la /etc/nginx/sites-enabled/ 2>/dev/null | grep -v "^total" || echo "❌ No se encontraron configuraciones"
echo ""

echo "Buscando proxy_pass en configuraciones:"
grep -r "proxy_pass" /etc/nginx/sites-enabled/ 2>/dev/null || echo "❌ No se encontró proxy_pass"
echo ""

# 6. Verificar logs de Nginx
echo "6️⃣  Últimos errores de Nginx..."
echo "----------------------------------------"
tail -20 /var/log/nginx/error.log 2>/dev/null | grep -i "502\|bad gateway\|connect\|upstream" || echo "No se encontraron errores 502 recientes"
echo ""

# 7. Buscar dónde está el código
echo "7️⃣  Buscando directorio de la aplicación..."
echo "----------------------------------------"
for dir in /opt/egarage /var/www/egarage /srv/egarage /home/*/egarage; do
    if [ -d "$dir" ] && [ -f "$dir/manage.py" ]; then
        echo "✅ Aplicación encontrada en: $dir"
        ls -la "$dir" | head -5
        break
    fi
done
echo ""

# 8. Verificar configuración de Nginx específica
echo "8️⃣  Configuración proxy_pass completa:"
echo "----------------------------------------"
for config in /etc/nginx/sites-enabled/*; do
    if [ -f "$config" ]; then
        echo "Archivo: $config"
        grep -A 10 "location /" "$config" | grep -A 10 "proxy_pass" || true
        echo ""
    fi
done

echo "=========================================="
echo "✅ DIAGNÓSTICO COMPLETADO"
echo "=========================================="
