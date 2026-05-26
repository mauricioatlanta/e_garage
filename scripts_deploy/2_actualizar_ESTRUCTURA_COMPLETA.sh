#!/bin/bash
# ======================================================
# Script 2: ACTUALIZAR EGARAGE - ESTRUCTURA COMPLETA
# Para: atlantareciclajes @ DigitalOcean
# Ruta: /home/atlantareciclajes/apps/egarage/current
# Incluye todos los cambios estructurales de templates
# ======================================================

set -e  # Detener si hay error

echo "======================================================"
echo "🚀 SCRIPT 2: ACTUALIZACIÓN COMPLETA DE EGARAGE"
echo "   (Incluye cambios estructurales)"
echo "======================================================"
echo ""

# Variables - RUTA CORREGIDA
PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"
UPDATE_PATH="/home/atlantareciclajes/egarage_update"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Verificar que existe el proyecto
if [ ! -d "${PROJECT_PATH}" ]; then
    echo "❌ ERROR: No se encontró ${PROJECT_PATH}"
    echo "   Ejecuta: ./0_detectar_ruta.sh"
    exit 1
fi

echo "✅ Proyecto encontrado: ${PROJECT_PATH}"

# Verificar que existe el directorio de actualización
if [ ! -d "${UPDATE_PATH}" ]; then
    echo "❌ ERROR: No se encontró ${UPDATE_PATH}"
    echo ""
    echo "📤 Debes subir primero con FileZilla:"
    echo "   1. Crear carpeta: /home/atlantareciclajes/egarage_update/"
    echo "   2. Subir archivo: egarage_update_atlantareciclajes.zip"
    echo "   3. Ejecutar este script de nuevo"
    exit 1
fi

echo "✅ Directorio de actualización encontrado"
echo ""

# Verificar si existe el ZIP
if [ -f "${UPDATE_PATH}/egarage_update_atlantareciclajes.zip" ]; then
    echo "📦 Descomprimiendo actualización..."
    cd "${UPDATE_PATH}"
    unzip -o egarage_update_atlantareciclajes.zip
    echo "   ✅ Descomprimido"
elif [ -d "${UPDATE_PATH}/deploy_atlantareciclajes" ]; then
    echo "✅ Archivos ya descomprimidos"
else
    echo "❌ ERROR: No se encontró el ZIP ni la carpeta descomprimida"
    echo "   Sube: egarage_update_atlantareciclajes.zip"
    exit 1
fi

# Verificar estructura
if [ ! -d "${UPDATE_PATH}/deploy_atlantareciclajes" ]; then
    echo "❌ ERROR: No se encontró deploy_atlantareciclajes/"
    echo "   Verifica la estructura del ZIP"
    exit 1
fi

DEPLOY_PATH="${UPDATE_PATH}/deploy_atlantareciclajes"

echo ""
echo "======================================================"
echo "📋 COPIANDO ARCHIVOS (ESTRUCTURA COMPLETA)..."
echo "======================================================"
echo ""

# ============================================
# TEMPLATES - ESTRUCTURA COMPLETA ACTUALIZADA
# ============================================

echo "📁 COPIANDO TEMPLATES (estructura completa)..."

# Backup de templates actuales (opcional, comentado para no duplicar)
# echo "💾 Haciendo backup de templates actuales..."
# if [ -d "${PROJECT_PATH}/templates" ]; then
#     tar -czf "${PROJECT_PATH}/templates_backup_${BACKUP_DATE}.tar.gz" -C "${PROJECT_PATH}" templates/
#     echo "   ✅ Backup guardado"
# fi

# Copiar estructura completa de templates
TEMPLATES_COPIADOS=0

# Templates principales
[ -d "${DEPLOY_PATH}/templates/account" ] && cp -r "${DEPLOY_PATH}/templates/account" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/auth" ] && cp -r "${DEPLOY_PATH}/templates/auth" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/cl" ] && cp -r "${DEPLOY_PATH}/templates/cl" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/us" ] && cp -r "${DEPLOY_PATH}/templates/us" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/taller" ] && cp -r "${DEPLOY_PATH}/templates/taller" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/email" ] && cp -r "${DEPLOY_PATH}/templates/email" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/emails" ] && cp -r "${DEPLOY_PATH}/templates/emails" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/portal" ] && cp -r "${DEPLOY_PATH}/templates/portal" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/suscripcion" ] && cp -r "${DEPLOY_PATH}/templates/suscripcion" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/onboarding" ] && cp -r "${DEPLOY_PATH}/templates/onboarding" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/registration" ] && cp -r "${DEPLOY_PATH}/templates/registration" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/components" ] && cp -r "${DEPLOY_PATH}/templates/components" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/errors" ] && cp -r "${DEPLOY_PATH}/templates/errors" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/landing" ] && cp -r "${DEPLOY_PATH}/templates/landing" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))

# Templates adicionales
[ -d "${DEPLOY_PATH}/templates/admin_panel" ] && cp -r "${DEPLOY_PATH}/templates/admin_panel" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/analytics" ] && cp -r "${DEPLOY_PATH}/templates/analytics" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/business_intelligence" ] && cp -r "${DEPLOY_PATH}/templates/business_intelligence" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/settings" ] && cp -r "${DEPLOY_PATH}/templates/settings" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/suspension" ] && cp -r "${DEPLOY_PATH}/templates/suspension" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))

# Templates por país
[ -d "${DEPLOY_PATH}/templates/br" ] && cp -r "${DEPLOY_PATH}/templates/br" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/co" ] && cp -r "${DEPLOY_PATH}/templates/co" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/ec" ] && cp -r "${DEPLOY_PATH}/templates/ec" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/mx" ] && cp -r "${DEPLOY_PATH}/templates/mx" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/pe" ] && cp -r "${DEPLOY_PATH}/templates/pe" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -d "${DEPLOY_PATH}/templates/ve" ] && cp -r "${DEPLOY_PATH}/templates/ve" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))

# Templates base
[ -f "${DEPLOY_PATH}/templates/base.html" ] && cp "${DEPLOY_PATH}/templates/base.html" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))
[ -f "${DEPLOY_PATH}/templates/landing_inicio.html" ] && cp "${DEPLOY_PATH}/templates/landing_inicio.html" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++))

echo "   ✅ ${TEMPLATES_COPIADOS} carpetas/archivos de templates copiados"

# ============================================
# CÓDIGO PYTHON - APP TALLER
# ============================================

echo ""
echo "📝 COPIANDO CÓDIGO PYTHON..."

# Views Extra
if [ -d "${DEPLOY_PATH}/taller/views_extra" ]; then
    mkdir -p "${PROJECT_PATH}/taller/views_extra"
    cp -r "${DEPLOY_PATH}/taller/views_extra/"* "${PROJECT_PATH}/taller/views_extra/"
    echo "   ✅ Views extra copiadas"
fi

# Models
if [ -d "${DEPLOY_PATH}/taller/models" ]; then
    mkdir -p "${PROJECT_PATH}/taller/models"
    cp -r "${DEPLOY_PATH}/taller/models/"* "${PROJECT_PATH}/taller/models/"
    echo "   ✅ Models copiados"
fi

# Forms
if [ -d "${DEPLOY_PATH}/taller/forms" ]; then
    mkdir -p "${PROJECT_PATH}/taller/forms"
    cp -r "${DEPLOY_PATH}/taller/forms/"* "${PROJECT_PATH}/taller/forms/"
    echo "   ✅ Forms copiados"
fi

# Middleware
if [ -d "${DEPLOY_PATH}/taller/middleware" ]; then
    mkdir -p "${PROJECT_PATH}/taller/middleware"
    cp -r "${DEPLOY_PATH}/taller/middleware/"* "${PROJECT_PATH}/taller/middleware/"
    echo "   ✅ Middleware copiado"
fi

# Context Processors
if [ -d "${DEPLOY_PATH}/taller/context_processors" ]; then
    mkdir -p "${PROJECT_PATH}/taller/context_processors"
    cp -r "${DEPLOY_PATH}/taller/context_processors/"* "${PROJECT_PATH}/taller/context_processors/"
    echo "   ✅ Context processors copiados"
fi

# Management Commands
if [ -d "${DEPLOY_PATH}/taller/management" ]; then
    mkdir -p "${PROJECT_PATH}/taller/management/commands"
    cp -r "${DEPLOY_PATH}/taller/management/"* "${PROJECT_PATH}/taller/management/"
    echo "   ✅ Management commands copiados"
fi

# Backends
if [ -d "${DEPLOY_PATH}/taller/backends" ]; then
    mkdir -p "${PROJECT_PATH}/taller/backends"
    cp -r "${DEPLOY_PATH}/taller/backends/"* "${PROJECT_PATH}/taller/backends/"
    echo "   ✅ Backends copiados"
fi

# Archivos individuales
[ -f "${DEPLOY_PATH}/taller/signals.py" ] && cp "${DEPLOY_PATH}/taller/signals.py" "${PROJECT_PATH}/taller/" && echo "   ✅ signals.py copiado"
[ -f "${DEPLOY_PATH}/taller/apps.py" ] && cp "${DEPLOY_PATH}/taller/apps.py" "${PROJECT_PATH}/taller/" && echo "   ✅ apps.py copiado"
[ -f "${DEPLOY_PATH}/taller/urls.py" ] && cp "${DEPLOY_PATH}/taller/urls.py" "${PROJECT_PATH}/taller/" && echo "   ✅ urls.py copiado"
[ -f "${DEPLOY_PATH}/taller/views.py" ] && cp "${DEPLOY_PATH}/taller/views.py" "${PROJECT_PATH}/taller/" && echo "   ✅ views.py copiado"
[ -f "${DEPLOY_PATH}/taller/admin.py" ] && cp "${DEPLOY_PATH}/taller/admin.py" "${PROJECT_PATH}/taller/" && echo "   ✅ admin.py copiado"

# ============================================
# CONFIGURACIÓN DJANGO
# ============================================

echo ""
echo "⚙️  COPIANDO CONFIGURACIÓN..."

# Backup de URLs antes de copiar
if [ -f "${PROJECT_PATH}/gestion_taller/urls.py" ]; then
    cp "${PROJECT_PATH}/gestion_taller/urls.py" "${PROJECT_PATH}/gestion_taller/urls.py.backup_${BACKUP_DATE}"
    echo "   ✅ Backup de URLs guardado"
fi

# Copiar URLs
if [ -f "${DEPLOY_PATH}/gestion_taller/urls.py" ]; then
    cp "${DEPLOY_PATH}/gestion_taller/urls.py" "${PROJECT_PATH}/gestion_taller/"
    echo "   ✅ URLs actualizadas"
fi

# WSGI y ASGI (solo si existen)
[ -f "${DEPLOY_PATH}/gestion_taller/wsgi.py" ] && cp "${DEPLOY_PATH}/gestion_taller/wsgi.py" "${PROJECT_PATH}/gestion_taller/" && echo "   ✅ wsgi.py copiado"
[ -f "${DEPLOY_PATH}/gestion_taller/asgi.py" ] && cp "${DEPLOY_PATH}/gestion_taller/asgi.py" "${PROJECT_PATH}/gestion_taller/" && echo "   ✅ asgi.py copiado"

# ============================================
# OTRAS APPS
# ============================================

echo ""
echo "📦 COPIANDO OTRAS APPS..."

# Core
if [ -d "${DEPLOY_PATH}/core" ]; then
    cp -r "${DEPLOY_PATH}/core" "${PROJECT_PATH}/"
    echo "   ✅ Core copiado"
fi

# Ubicacion
if [ -d "${DEPLOY_PATH}/ubicacion" ]; then
    cp -r "${DEPLOY_PATH}/ubicacion" "${PROJECT_PATH}/"
    echo "   ✅ Ubicacion copiado"
fi

# Manage.py
if [ -f "${DEPLOY_PATH}/manage.py" ]; then
    cp "${DEPLOY_PATH}/manage.py" "${PROJECT_PATH}/"
    echo "   ✅ manage.py copiado"
fi

echo ""
echo "======================================================"
echo "⚠️  PASO MANUAL: EDITAR SETTINGS.PY"
echo "======================================================"
echo ""
echo "Ejecuta este comando:"
echo ""
echo "   nano ${PROJECT_PATH}/gestion_taller/settings.py"
echo ""
echo "Busca (Ctrl+W) y cambia estas 3 líneas:"
echo ""
echo "1. BUSCAR: ACCOUNT_EMAIL_VERIFICATION = os.getenv"
echo "   CAMBIAR línea completa a:"
echo "   ACCOUNT_EMAIL_VERIFICATION = os.getenv(\"ACCOUNT_EMAIL_VERIFICATION\", \"mandatory\")"
echo ""
echo "2. BUSCAR: ACCOUNT_EMAIL_REQUIRED = False"
echo "   CAMBIAR a:"
echo "   ACCOUNT_EMAIL_REQUIRED = True"
echo ""
echo "3. BUSCAR: ACCOUNT_CONFIRM_EMAIL_ON_GET = env_bool"
echo "   CAMBIAR línea completa a:"
echo "   ACCOUNT_CONFIRM_EMAIL_ON_GET = True"
echo ""
echo "Guardar: Ctrl+O, Enter"
echo "Salir: Ctrl+X"
echo ""
read -p "Presiona ENTER después de editar settings.py..." pausa

echo ""
echo "======================================================"
echo "🗄️  MIGRANDO BASE DE DATOS..."
echo "======================================================"
echo ""

cd "${PROJECT_PATH}"

# Backup de DB antes de migrar
if [ -f "db.sqlite3" ]; then
    echo "💾 Haciendo backup de DB antes de migrar..."
    cp db.sqlite3 "db_antes_migracion_${BACKUP_DATE}.sqlite3"
    echo "   ✅ Backup guardado"
fi

# Crear migraciones
echo ""
echo "🔨 Creando migraciones si hay cambios en modelos..."
python manage.py makemigrations 2>&1 || echo "   ℹ️  No hay cambios en modelos"

echo ""
echo "⚡ Ejecutando migraciones..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo "   ✅ Migraciones completadas"
else
    echo "   ❌ Error en migraciones"
    exit 1
fi

echo ""
echo "======================================================"
echo "🎨 RECOLECTANDO ARCHIVOS ESTÁTICOS..."
echo "======================================================"
echo ""

python manage.py collectstatic --clear --noinput 2>&1 | tail -5
python manage.py collectstatic --noinput 2>&1 | tail -3

echo ""
echo "======================================================"
echo "✅ ACTUALIZACIÓN COMPLETA FINALIZADA"
echo "======================================================"
echo ""
echo "📊 RESUMEN:"
echo "   • Templates: ${TEMPLATES_COPIADOS} carpetas/archivos"
echo "   • Código Python: Actualizado"
echo "   • Configuración: Actualizada"
echo "   • Migraciones: Aplicadas"
echo "   • Estáticos: Recolectados"
echo ""
echo "⏭️  SIGUIENTE PASO - RELOAD DE LA APP:"
echo ""
echo "   1. Ir a: https://www/user/atlantareciclajes/"
echo "   2. Clic en pestaña 'Web'"
echo "   3. Buscar: atlantareciclajes"
echo "   4. Clic en botón verde grande:"
echo "      'Reload atlantareciclajes'"
echo "   5. Esperar 15 segundos"
echo "   6. Probar: https://atlantareciclajes/cl/"
echo ""
echo "Luego ejecuta: ./3_verificar_FIXED.sh"
echo ""
echo "======================================================"







