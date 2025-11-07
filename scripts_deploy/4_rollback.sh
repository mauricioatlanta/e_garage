#!/bin/bash
# ======================================================
# Script 4: ROLLBACK (Restaurar Backup)
# Para: atlantareciclajes @ PythonAnywhere
# ======================================================

echo "======================================================"
echo "🔄 SCRIPT 4: ROLLBACK - RESTAURAR BACKUP"
echo "======================================================"
echo ""
echo "⚠️  ¡ADVERTENCIA!"
echo "   Este script restaurará el backup y perderá"
echo "   todos los cambios de la actualización."
echo ""

# Listar backups disponibles
echo "📦 Backups disponibles:"
echo ""
ls -lht /home/atlantareciclajes/backups_* 2>/dev/null | head -10

echo ""
read -p "¿Estás seguro de hacer rollback? (escribe SI): " confirmacion

if [ "$confirmacion" != "SI" ]; then
    echo ""
    echo "❌ Rollback cancelado"
    exit 0
fi

echo ""
read -p "Ingresa la fecha del backup (YYYYMMDD_HHMMSS): " BACKUP_DATE

BACKUP_DIR="/home/atlantareciclajes/backups_${BACKUP_DATE}"
PROJECT_PATH="/home/atlantareciclajes/egarage"

# Verificar que existe el backup
if [ ! -d "${BACKUP_DIR}" ]; then
    echo "❌ ERROR: No se encontró el backup: ${BACKUP_DIR}"
    echo ""
    echo "Backups disponibles:"
    ls -d /home/atlantareciclajes/backups_* 2>/dev/null
    exit 1
fi

echo ""
echo "======================================================"
echo "🔄 RESTAURANDO BACKUP..."
echo "======================================================"
echo ""

# Restaurar base de datos
echo "💾 1/4: Restaurando base de datos..."
if [ -f "${BACKUP_DIR}/db.sqlite3" ]; then
    cp "${BACKUP_DIR}/db.sqlite3" "${PROJECT_PATH}/db.sqlite3"
    echo "   ✅ Base de datos restaurada"
else
    echo "   ❌ No se encontró db.sqlite3 en el backup"
fi

# Restaurar media
echo ""
echo "📷 2/4: Restaurando archivos media..."
if [ -d "${BACKUP_DIR}/media" ]; then
    rm -rf "${PROJECT_PATH}/media"
    cp -r "${BACKUP_DIR}/media" "${PROJECT_PATH}/"
    echo "   ✅ Media restaurada"
else
    echo "   ℹ️  No hay media en el backup"
fi

# Restaurar settings
echo ""
echo "⚙️  3/4: Restaurando settings.py..."
if [ -f "${BACKUP_DIR}/settings.py" ]; then
    cp "${BACKUP_DIR}/settings.py" "${PROJECT_PATH}/gestion_taller/settings.py"
    echo "   ✅ Settings restaurado"
fi

# Restaurar URLs
echo ""
echo "🔗 4/4: Restaurando urls.py..."
if [ -f "${BACKUP_DIR}/urls.py" ]; then
    cp "${BACKUP_DIR}/urls.py" "${PROJECT_PATH}/gestion_taller/urls.py"
    echo "   ✅ URLs restaurado"
fi

echo ""
echo "======================================================"
echo "✅ ROLLBACK COMPLETADO"
echo "======================================================"
echo ""
echo "⏭️  Siguiente paso:"
echo "   1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/"
echo "   2. Pestaña 'Web'"
echo "   3. Clic en 'Reload atlantareciclajes.pythonanywhere.com'"
echo "   4. El sitio volverá al estado anterior"
echo ""
echo "======================================================"

