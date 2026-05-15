#!/bin/bash
# ======================================================
# Script 1: BACKUP COMPLETO
# Para: atlantareciclajes @ PythonAnywhere
# ======================================================

set -e  # Detener si hay error

echo "======================================================"
echo "🔒 SCRIPT 1: BACKUP COMPLETO"
echo "======================================================"
echo ""

# Variables
PROJECT_PATH="/home/atlantareciclajes/egarage"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/atlantareciclajes/backups_${BACKUP_DATE}"

echo "📁 Creando carpeta de backup: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Backup de base de datos
echo ""
echo "💾 1/5: Haciendo backup de base de datos..."
if [ -f "${PROJECT_PATH}/db.sqlite3" ]; then
    cp "${PROJECT_PATH}/db.sqlite3" "${BACKUP_DIR}/db.sqlite3"
    echo "   ✅ db.sqlite3 respaldada"
else
    echo "   ⚠️  No se encontró db.sqlite3"
fi

# Backup de media
echo ""
echo "📷 2/5: Haciendo backup de archivos media..."
if [ -d "${PROJECT_PATH}/media" ]; then
    cp -r "${PROJECT_PATH}/media" "${BACKUP_DIR}/"
    echo "   ✅ Carpeta media/ respaldada"
else
    echo "   ℹ️  No hay carpeta media/"
fi

# Backup de settings
echo ""
echo "⚙️  3/5: Haciendo backup de settings.py..."
if [ -f "${PROJECT_PATH}/gestion_taller/settings.py" ]; then
    cp "${PROJECT_PATH}/gestion_taller/settings.py" "${BACKUP_DIR}/settings.py"
    echo "   ✅ settings.py respaldado"
fi

# Backup de URLs
echo ""
echo "🔗 4/5: Haciendo backup de urls.py..."
if [ -f "${PROJECT_PATH}/gestion_taller/urls.py" ]; then
    cp "${PROJECT_PATH}/gestion_taller/urls.py" "${BACKUP_DIR}/urls.py"
    echo "   ✅ urls.py respaldado"
fi

# Contar usuarios ANTES
echo ""
echo "👥 5/5: Contando usuarios actuales..."
cd "${PROJECT_PATH}"
python manage.py shell << EOF > "${BACKUP_DIR}/usuarios_count.txt" 2>&1
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
print(f"USUARIOS_ANTES={User.objects.count()}")
print(f"EMPRESAS_ANTES={Empresa.objects.count()}")
EOF

if [ -f "${BACKUP_DIR}/usuarios_count.txt" ]; then
    cat "${BACKUP_DIR}/usuarios_count.txt"
    echo "   ✅ Conteo guardado en usuarios_count.txt"
fi

# Crear archivo tar.gz completo
echo ""
echo "📦 Creando archivo comprimido completo..."
cd /home/atlantareciclajes/
tar -czf "backup_completo_${BACKUP_DATE}.tar.gz" "backups_${BACKUP_DATE}/" 2>/dev/null || true

echo ""
echo "======================================================"
echo "✅ BACKUP COMPLETADO"
echo "======================================================"
echo ""
echo "📍 Ubicación del backup:"
echo "   ${BACKUP_DIR}/"
echo "   /home/atlantareciclajes/backup_completo_${BACKUP_DATE}.tar.gz"
echo ""
echo "📥 Descarga este archivo a tu PC con FileZilla:"
echo "   backup_completo_${BACKUP_DATE}.tar.gz"
echo ""
echo "⏭️  Siguiente paso: Subir archivos de actualización"
echo "======================================================"
