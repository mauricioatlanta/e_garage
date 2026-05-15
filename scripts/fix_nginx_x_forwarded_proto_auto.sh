#!/bin/bash
# Script para verificar y corregir automáticamente X-Forwarded-Proto en Nginx
# Ejecutar en el servidor: sudo bash fix_nginx_x_forwarded_proto_auto.sh

set -e

echo "=========================================="
echo "🔍 Verificando y corrigiendo configuración de Nginx"
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

# 2. Verificar y corregir cada archivo
FIXED=0
for CONFIG_FILE in $CONFIG_FILES; do
    echo "=========================================="
    echo "📄 Analizando: $CONFIG_FILE"
    echo "=========================================="
    echo ""
    
    # Verificar si tiene X-Forwarded-Proto
    if sudo grep -q "X-Forwarded-Proto" "$CONFIG_FILE"; then
        echo "✅ Header X-Forwarded-Proto ya está presente"
        sudo grep "X-Forwarded-Proto" "$CONFIG_FILE" | head -1
    else
        echo "❌ Header X-Forwarded-Proto NO encontrado"
        echo ""
        echo "📝 Mostrando bloque location / { ... } actual:"
        sudo grep -A 20 "location / {" "$CONFIG_FILE" | head -25 || echo "  (no se encontró location /)"
        echo ""
        
        # Crear backup
        BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "💾 Creando backup: $BACKUP_FILE"
        sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
        
        # Intentar agregar el header automáticamente
        echo "🔧 Intentando agregar X-Forwarded-Proto automáticamente..."
        
        # Buscar la línea con proxy_pass en location /
        if sudo grep -q "proxy_pass.*8001" "$CONFIG_FILE"; then
            # Crear un archivo temporal con la corrección
            TEMP_FILE=$(mktemp)
            sudo cp "$CONFIG_FILE" "$TEMP_FILE"
            
            # Agregar X-Forwarded-Proto después de X-Forwarded-For si existe
            if sudo grep -q "X-Forwarded-For" "$TEMP_FILE"; then
                sudo sed -i '/proxy_set_header X-Forwarded-For/a\        proxy_set_header X-Forwarded-Proto $scheme;' "$TEMP_FILE"
            elif sudo grep -q "proxy_set_header Host" "$TEMP_FILE"; then
                # Agregar después de Host si no hay X-Forwarded-For
                sudo sed -i '/proxy_set_header Host/a\        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;' "$TEMP_FILE"
            else
                # Agregar después de proxy_pass
                sudo sed -i '/proxy_pass.*8001/a\        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;' "$TEMP_FILE"
            fi
            
            # Verificar sintaxis antes de aplicar
            if sudo nginx -t -c "$TEMP_FILE" 2>/dev/null; then
                sudo mv "$TEMP_FILE" "$CONFIG_FILE"
                echo "✅ Header X-Forwarded-Proto agregado correctamente"
                FIXED=$((FIXED + 1))
            else
                echo "❌ Error en la sintaxis. Revisando manualmente..."
                sudo rm "$TEMP_FILE"
                echo ""
                echo "⚠️  CORRECCIÓN MANUAL REQUERIDA"
                echo "Edita el archivo: sudo nano $CONFIG_FILE"
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
            fi
        else
            echo "⚠️  No se encontró proxy_pass a 8001. Revisión manual requerida."
        fi
    fi
    echo ""
    
    # Verificar otros headers importantes
    echo "📋 Headers proxy actuales:"
    sudo grep "proxy_set_header" "$CONFIG_FILE" || echo "  (ninguno encontrado)"
    echo ""
done

# 3. Si se hicieron cambios, verificar y recargar
if [ $FIXED -gt 0 ]; then
    echo "=========================================="
    echo "✅ Se corrigieron $FIXED archivo(s)"
    echo "=========================================="
    echo ""
    echo "🔍 Verificando sintaxis de Nginx..."
    if sudo nginx -t; then
        echo "✅ Sintaxis correcta"
        echo ""
        echo "🔄 Recargando Nginx..."
        sudo systemctl reload nginx
        echo "✅ Nginx recargado"
    else
        echo "❌ Error en la sintaxis de Nginx. Revisa los archivos."
        exit 1
    fi
else
    echo "=========================================="
    echo "✅ No se requirieron correcciones"
    echo "=========================================="
fi

echo ""
echo "=========================================="
echo "✅ Verificación completada"
echo "=========================================="
