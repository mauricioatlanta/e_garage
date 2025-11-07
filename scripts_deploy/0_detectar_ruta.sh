#!/bin/bash
# ======================================================
# Script 0: DETECTAR RUTA DEL PROYECTO
# ======================================================

echo "======================================================"
echo "🔍 DETECTANDO RUTA DEL PROYECTO EGARAGE"
echo "======================================================"
echo ""

# Rutas posibles
RUTAS_POSIBLES=(
    "/home/atlantareciclajes/apps/egarage/current"
    "/home/atlantareciclajes/egarage"
    "/home/atlantareciclajes/mysite"
    "/home/atlantareciclajes/webapp"
)

echo "Buscando manage.py en rutas comunes..."
echo ""

RUTA_ENCONTRADA=""

for ruta in "${RUTAS_POSIBLES[@]}"; do
    if [ -f "${ruta}/manage.py" ]; then
        echo "✅ ENCONTRADO: ${ruta}"
        RUTA_ENCONTRADA="${ruta}"
        break
    else
        echo "❌ No encontrado: ${ruta}"
    fi
done

echo ""

if [ -z "${RUTA_ENCONTRADA}" ]; then
    echo "⚠️  No se encontró manage.py en rutas comunes"
    echo ""
    echo "🔍 Buscando en todo el home..."
    find /home/atlantareciclajes/ -name "manage.py" -type f 2>/dev/null | head -5
    echo ""
    echo "📝 Ejecuta manualmente:"
    echo "   find /home/atlantareciclajes/ -name manage.py"
else
    echo "======================================================"
    echo "✅ RUTA DEL PROYECTO ENCONTRADA:"
    echo "======================================================"
    echo ""
    echo "   ${RUTA_ENCONTRADA}"
    echo ""
    
    # Verificar contenido
    echo "📁 Contenido del proyecto:"
    ls -la "${RUTA_ENCONTRADA}" | head -20
    
    echo ""
    echo "📊 Base de datos:"
    if [ -f "${RUTA_ENCONTRADA}/db.sqlite3" ]; then
        ls -lh "${RUTA_ENCONTRADA}/db.sqlite3"
        echo "   ✅ db.sqlite3 encontrada"
    else
        echo "   ⚠️  No se encontró db.sqlite3"
        echo "   ¿Usas MySQL/PostgreSQL?"
    fi
    
    echo ""
    echo "======================================================"
    echo "📝 GUARDA ESTA RUTA:"
    echo "======================================================"
    echo ""
    echo "   ${RUTA_ENCONTRADA}"
    echo ""
    echo "Usarás esta ruta en los siguientes scripts."
    echo ""
fi

echo "======================================================"

