#!/bin/bash
# ======================================================
# SOLUCIÓN RÁPIDA: Reorganizar archivos descomprimidos
# Ejecutar en el servidor cuando el ZIP no tiene la carpeta deploy_atlantareciclajes
# ======================================================

UPDATE_PATH="/home/atlantareciclajes/egarage_update"

echo "======================================================"
echo "REORGANIZANDO ARCHIVOS DESCOMPRIMIDOS..."
echo "======================================================"
echo ""

cd "${UPDATE_PATH}"

# Verificar si ya existe la carpeta deploy_atlantareciclajes
if [ -d "deploy_atlantareciclajes" ]; then
    echo "✅ La carpeta deploy_atlantareciclajes ya existe"
    echo "   No es necesario reorganizar"
    exit 0
fi

# Crear la carpeta deploy_atlantareciclajes
echo "📁 Creando carpeta deploy_atlantareciclajes..."
mkdir -p deploy_atlantareciclajes

# Mover archivos y carpetas que deberían estar dentro
echo "📦 Moviendo archivos..."

# Mover templates si existe
[ -d "templates" ] && mv templates deploy_atlantareciclajes/ && echo "   ✅ templates/ movido"

# Mover taller si existe
[ -d "taller" ] && mv taller deploy_atlantareciclajes/ && echo "   ✅ taller/ movido"

# Mover gestion_taller si existe
[ -d "gestion_taller" ] && mv gestion_taller deploy_atlantareciclajes/ && echo "   ✅ gestion_taller/ movido"

# Mover core si existe
[ -d "core" ] && mv core deploy_atlantareciclajes/ && echo "   ✅ core/ movido"

# Mover ubicacion si existe
[ -d "ubicacion" ] && mv ubicacion deploy_atlantareciclajes/ && echo "   ✅ ubicacion/ movido"

# Mover manage.py si existe
[ -f "manage.py" ] && mv manage.py deploy_atlantareciclajes/ && echo "   ✅ manage.py movido"

# Mover otros archivos comunes
[ -f "INFO_ACTUALIZACION.txt" ] && mv INFO_ACTUALIZACION.txt deploy_atlantareciclajes/ && echo "   ✅ INFO_ACTUALIZACION.txt movido"

echo ""
echo "======================================================"
echo "✅ REORGANIZACIÓN COMPLETADA"
echo "======================================================"
echo ""
echo "Ahora puedes ejecutar:"
echo "   ./2_actualizar_FIXED.sh"
echo ""











