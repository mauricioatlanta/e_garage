#!/bin/bash
# Script para actualizar el servidor de PythonAnywhere con el fix de scroll móvil
# Ejecutar esto EN EL SERVIDOR después de hacer push

echo "========================================"
echo "🚀 Actualizando eGarage en PythonAnywhere"
echo "========================================"
echo ""

# Ir al directorio de la aplicación
cd ~/apps/egarage/current

echo "📥 Descargando cambios desde GitHub..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Cambios descargados exitosamente"
else
    echo "❌ Error al descargar cambios"
    exit 1
fi

echo ""
echo "🔄 Reiniciando aplicación..."
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

if [ $? -eq 0 ]; then
    echo "✅ Aplicación reiniciada exitosamente"
else
    echo "❌ Error al reiniciar aplicación"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "========================================"
echo ""
echo "🧪 Para verificar que funciona:"
echo "   1. Abre desde un móvil: https://www.egarage.cl/cl/es/clientes/crear/"
echo "   2. Abre consola del navegador"
echo "   3. Busca: '📱 Móvil detectado - activando protección anti-scroll automático'"
echo "   4. Verifica que la página NO salta a la cabecera automáticamente"
echo ""
echo "📋 La vista debe mantenerse estable y el scroll manual debe funcionar perfectamente"
echo ""

