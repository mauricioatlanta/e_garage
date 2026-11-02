#!/bin/bash
# ======================================================
# Script 1: BACKUP COMPLETO (RUTA CORREGIDA)
# Para: atlantareciclajes @ DigitalOcean
# Ruta: /home/atlantareciclajes/apps/egarage/current
# ======================================================

set -e  # Detener si hay error

echo "======================================================"
echo "🔒 SCRIPT 1: BACKUP COMPLETO"
echo "======================================================"
echo ""

# Variables - RUTA CORREGIDA
PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/atlantareciclajes/backups_${BACKUP_DATE}"

# Verificar que existe el proyecto
if [ ! -d "${PROJECT_PATH}" ]; then
    echo "❌ ERROR: No se encontró ${PROJECT_PATH}"
    echo ""
    echo "🔍 Ejecuta primero: ./0_detectar_ruta.sh"
    exit 1
fi

echo "✅ Proyecto encontrado en: ${PROJECT_PATH}"
echo "📁 Creando carpeta de backup: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Backup de base de datos
echo ""
echo "💾 1/5: Haciendo backup de base de datos..."
if [ -f "${PROJECT_PATH}/db.sqlite3" ]; then
    cp "${PROJECT_PATH}/db.sqlite3" "${BACKUP_DIR}/db.sqlite3"
    SIZE=$(ls -lh "${BACKUP_DIR}/db.sqlite3" | awk '{print $5}')
    echo "   ✅ db.sqlite3 respaldada (${SIZE})"
else
    echo "   ⚠️  No se encontró db.sqlite3 (¿usas MySQL?)"
fi

# Backup de media
echo ""
echo "📷 2/5: Haciendo backup de archivos media..."
if [ -d "${PROJECT_PATH}/media" ]; then
    cp -r "${PROJECT_PATH}/media" "${BACKUP_DIR}/"
    COUNT=$(find "${BACKUP_DIR}/media" -type f | wc -l)
    echo "   ✅ Carpeta media/ respaldada (${COUNT} archivos)"
else
    echo "   ℹ️  No hay carpeta media/ (normal si es nuevo)"
fi

# Backup de settings
echo ""
echo "⚙️  3/5: Haciendo backup de settings.py..."
if [ -f "${PROJECT_PATH}/gestion_taller/settings.py" ]; then
    cp "${PROJECT_PATH}/gestion_taller/settings.py" "${BACKUP_DIR}/settings.py"
    echo "   ✅ settings.py respaldado"
else
    echo "   ❌ No se encontró settings.py"
fi

# Backup de URLs
echo ""
echo "🔗 4/5: Haciendo backup de urls.py..."
if [ -f "${PROJECT_PATH}/gestion_taller/urls.py" ]; then
    cp "${PROJECT_PATH}/gestion_taller/urls.py" "${BACKUP_DIR}/urls.py"
    echo "   ✅ urls.py respaldado"
else
    echo "   ❌ No se encontró urls.py"
fi

# Contar usuarios ANTES
echo ""
echo "👥 5/5: Contando usuarios actuales..."
cd "${PROJECT_PATH}"
python manage.py shell << 'EOF' > "${BACKUP_DIR}/usuarios_count.txt" 2>&1
from django.contrib.auth.models import User
try:
    from taller.models.empresa import Empresa
    print(f"USUARIOS_ANTES={User.objects.count()}")
    print(f"EMPRESAS_ANTES={Empresa.objects.count()}")
except Exception as e:
    print(f"USUARIOS_ANTES={User.objects.count()}")
    print(f"ERROR_EMPRESAS={str(e)}")
EOF

if [ -f "${BACKUP_DIR}/usuarios_count.txt" ]; then
    cat "${BACKUP_DIR}/usuarios_count.txt"
    echo "   ✅ Conteo guardado"
fi

# Crear archivo tar.gz completo
echo ""
echo "📦 Creando archivo comprimido completo..."
cd /home/atlantareciclajes/
tar -czf "backup_completo_${BACKUP_DATE}.tar.gz" "backups_${BACKUP_DATE}/" 2>/dev/null
SIZE=$(ls -lh "backup_completo_${BACKUP_DATE}.tar.gz" 2>/dev/null | awk '{print $5}')

echo ""
echo "======================================================"
echo "✅ BACKUP COMPLETADO"
echo "======================================================"
echo ""
echo "📍 Ubicación del backup:"
echo "   ${BACKUP_DIR}/"
echo "   /home/atlantareciclajes/backup_completo_${BACKUP_DATE}.tar.gz (${SIZE})"
echo ""
echo "📥 IMPORTANTE: Descarga con FileZilla a tu PC:"
echo "   Archivo: backup_completo_${BACKUP_DATE}.tar.gz"
echo "   Guardar en: E:\\backups_egarage_digitalocean\\"
echo ""
echo "⏭️  Siguiente paso:"
echo "   1. Descargar backup a tu PC"
echo "   2. Subir egarage_update_atlantareciclajes.zip a:"
echo "      /home/atlantareciclajes/egarage_update/"
echo "   3. Ejecutar: ./2_actualizar_FIXED.sh"
echo ""
echo "======================================================"
