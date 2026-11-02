#!/bin/bash
# Script para verificar y actualizar la configuración de Nginx de egarage

echo "=========================================="
echo "Verificando configuración de Nginx - egarage"
echo "=========================================="
echo ""

CONFIG_FILE="/etc/nginx/sites-available/egarage"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: No se encontró $CONFIG_FILE"
    exit 1
fi

echo "✅ Archivo encontrado: $CONFIG_FILE"
echo ""

# Verificar si tiene el header X-Forwarded-Proto
if grep -q "X-Forwarded-Proto" "$CONFIG_FILE"; then
    echo "✅ Header X-Forwarded-Proto encontrado"
else
    echo "❌ Header X-Forwarded-Proto NO encontrado - Necesita agregarse"
fi

# Verificar si tiene bloqueo de archivos ocultos
if grep -q "location ~ /\\\.(?!well-known)" "$CONFIG_FILE"; then
    echo "✅ Bloqueo de archivos ocultos configurado"
else
    echo "⚠️  Bloqueo de archivos ocultos NO encontrado (recomendado agregarlo)"
fi

echo ""
echo "=========================================="
echo "Contenido actual del archivo:"
echo "=========================================="
cat "$CONFIG_FILE"
echo ""
echo "=========================================="
echo "Verificación completada"
echo "=========================================="
