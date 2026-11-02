#!/bin/bash
# Script para corregir el bloque robots.txt en nginx
# Ejecutar en el servidor: sudo bash fix_nginx_robots_txt.sh

set -e

CONFIG_FILE="/etc/nginx/sites-available/egarage"
BACKUP_FILE="/etc/nginx/sites-available/egarage.backup.$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "Corrigiendo bloque robots.txt en nginx"
echo "=========================================="
echo ""

# Verificar que el archivo existe
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: No se encontró $CONFIG_FILE"
    exit 1
fi

echo "✅ Archivo encontrado: $CONFIG_FILE"

# Crear backup
echo "📦 Creando backup: $BACKUP_FILE"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ Backup creado"

# Usar el script Python si está disponible (más robusto)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/fix_nginx_robots_txt.py"

if [ -f "$PYTHON_SCRIPT" ] && command -v python3 &> /dev/null; then
    echo "🐍 Usando script Python para el reemplazo..."
    python3 "$PYTHON_SCRIPT"
    PYTHON_EXIT=$?
    
    if [ $PYTHON_EXIT -eq 0 ]; then
        echo "✅ Script Python completado exitosamente"
        # El script Python ya verificó la sintaxis, solo recargar
        echo ""
        echo "=========================================="
        echo "Recargando nginx..."
        echo "=========================================="
        
        if sudo systemctl reload nginx; then
            echo "✅ Nginx recargado exitosamente"
            echo ""
            echo "=========================================="
            echo "Verificando robots.txt..."
            echo "=========================================="
            echo ""
            echo "Ejecuta en el servidor:"
            echo "  curl -i https://egarage.cl/robots.txt | head -n 20"
            echo ""
            echo "Deberías ver HTTP/2 200 y el contenido del archivo."
            echo ""
            echo "=========================================="
            echo "✅ Proceso completado exitosamente"
            echo "=========================================="
            exit 0
        else
            echo "❌ Error al recargar nginx"
            exit 1
        fi
    else
        echo "❌ Error en el script Python"
        exit 1
    fi
else
    echo "⚠️  Script Python no disponible, usando método manual..."
    
    # Verificar si existe el bloque robots.txt actual
    if grep -q "location = /robots.txt" "$CONFIG_FILE"; then
        echo "✅ Bloque robots.txt encontrado, actualizando..."
        
        # Eliminar el bloque existente
        sed -i '/^\s*location\s*=\s*\/robots\.txt\s*{/,/^\s*}\s*$/d' "$CONFIG_FILE"
        
        # Agregar el nuevo bloque después de location /static/
        if grep -q "location /static/" "$CONFIG_FILE"; then
            sed -i '/location \/static\/ {/,/^[[:space:]]*}$/a\
    location = /robots.txt {\
        default_type text/plain;\
        alias /srv/egarage/staticfiles/robots.txt;\
        access_log off;\
        log_not_found off;\
    }
' "$CONFIG_FILE"
        else
            sed -i '/^}$/i\
    location = /robots.txt {\
        default_type text/plain;\
        alias /srv/egarage/staticfiles/robots.txt;\
        access_log off;\
        log_not_found off;\
    }
' "$CONFIG_FILE"
        fi
        
        echo "✅ Bloque robots.txt actualizado"
    else
        echo "⚠️  Bloque robots.txt no encontrado, agregando..."
        
        # Agregar el bloque después de location /static/ si existe
        if grep -q "location /static/" "$CONFIG_FILE"; then
            sed -i '/location \/static\/ {/,/^[[:space:]]*}$/a\
    location = /robots.txt {\
        default_type text/plain;\
        alias /srv/egarage/staticfiles/robots.txt;\
        access_log off;\
        log_not_found off;\
    }
' "$CONFIG_FILE"
        else
            sed -i '/^}$/i\
    location = /robots.txt {\
        default_type text/plain;\
        alias /srv/egarage/staticfiles/robots.txt;\
        access_log off;\
        log_not_found off;\
    }
' "$CONFIG_FILE"
        fi
        
        echo "✅ Bloque robots.txt agregado"
    fi
fi

echo ""
echo "=========================================="
echo "Verificando configuración de nginx..."
echo "=========================================="

# Verificar sintaxis
if sudo nginx -t; then
    echo ""
    echo "✅ Sintaxis de nginx correcta"
    echo ""
    echo "=========================================="
    echo "Recargando nginx..."
    echo "=========================================="
    
    if sudo systemctl reload nginx; then
        echo "✅ Nginx recargado exitosamente"
        echo ""
        echo "=========================================="
        echo "Verificando robots.txt..."
        echo "=========================================="
        echo ""
        echo "Ejecuta en el servidor:"
        echo "  curl -i https://egarage.cl/robots.txt | head -n 20"
        echo ""
        echo "Deberías ver HTTP/2 200 y el contenido del archivo."
    else
        echo "❌ Error al recargar nginx"
        echo "Restaurando backup..."
        cp "$BACKUP_FILE" "$CONFIG_FILE"
        exit 1
    fi
else
    echo "❌ Error en la sintaxis de nginx"
    echo "Restaurando backup..."
    cp "$BACKUP_FILE" "$CONFIG_FILE"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Proceso completado exitosamente"
echo "=========================================="
echo ""
echo "Backup guardado en: $BACKUP_FILE"
