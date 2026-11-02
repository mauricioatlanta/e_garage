#!/bin/bash
# Script para verificar que el template fue creado correctamente

echo "=========================================="
echo "VERIFICACIÓN DEL TEMPLATE CREADO"
echo "=========================================="

TEMPLATE_PATH="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/taller/us/en/settings/futuristic_company_settings.html"

if [ -f "$TEMPLATE_PATH" ]; then
    echo "✅ El archivo existe"
    echo "   Ruta: $TEMPLATE_PATH"
    echo ""
    echo "📊 Información del archivo:"
    ls -lh "$TEMPLATE_PATH"
    echo ""
    echo "📝 Líneas en el archivo:"
    wc -l "$TEMPLATE_PATH"
    echo ""
    echo "🔍 Primeras líneas del archivo:"
    head -n 5 "$TEMPLATE_PATH"
    echo ""
    echo "🔍 Últimas líneas del archivo:"
    tail -n 5 "$TEMPLATE_PATH"
    echo ""
    echo "✅ El template está listo para usar"
    echo ""
    echo "🌐 Prueba acceder a: https://www.egarage.cl/us/en/settings/"
else
    echo "❌ El archivo NO existe en: $TEMPLATE_PATH"
fi

echo "=========================================="

