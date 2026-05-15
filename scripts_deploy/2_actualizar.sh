#!/bin/bash
# ======================================================
# Script 2: ACTUALIZAR EGARAGE
# Para: atlantareciclajes @ PythonAnywhere
# ======================================================

set -e  # Detener si hay error

echo "======================================================"
echo "🚀 SCRIPT 2: ACTUALIZACIÓN DE EGARAGE"
echo "======================================================"
echo ""

# Variables
PROJECT_PATH="/home/atlantareciclajes/egarage"
UPDATE_PATH="/home/atlantareciclajes/egarage_update"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Verificar que existe el directorio de actualización
if [ ! -d "${UPDATE_PATH}" ]; then
    echo "❌ ERROR: No se encontró ${UPDATE_PATH}"
    echo "   Primero sube los archivos con FileZilla"
    exit 1
fi

echo "✅ Directorio de actualización encontrado"
echo ""

# Verificar que existe el ZIP o la carpeta descomprimida
if [ -f "${UPDATE_PATH}/egarage_update_atlantareciclajes.zip" ]; then
    echo "📦 Descomprimiendo actualización..."
    cd "${UPDATE_PATH}"
    unzip -o egarage_update_atlantareciclajes.zip
    echo "   ✅ Descomprimido"
fi

# Verificar estructura
if [ ! -d "${UPDATE_PATH}/deploy_atlantareciclajes" ]; then
    echo "❌ ERROR: No se encontró carpeta deploy_atlantareciclajes"
    echo "   Verifica la estructura del ZIP"
    exit 1
fi

DEPLOY_PATH="${UPDATE_PATH}/deploy_atlantareciclajes"

echo ""
echo "======================================================"
echo "📋 COPIANDO ARCHIVOS..."
echo "======================================================"
echo ""

# 1. Templates - Email
echo "📧 1/12: Copiando templates de email..."
mkdir -p "${PROJECT_PATH}/templates/email"
cp -r "${DEPLOY_PATH}/templates/email/"* "${PROJECT_PATH}/templates/email/" 2>/dev/null || true
echo "   ✅ Templates de email copiados"

# 2. Templates - Account Email
echo "📧 2/12: Copiando templates de confirmación..."
mkdir -p "${PROJECT_PATH}/templates/account/email"
cp -r "${DEPLOY_PATH}/templates/account/email/"* "${PROJECT_PATH}/templates/account/email/" 2>/dev/null || true
echo "   ✅ Templates de confirmación copiados"

# 3. Templates - Auth
echo "🔐 3/12: Copiando template de signup..."
mkdir -p "${PROJECT_PATH}/templates/auth"
cp "${DEPLOY_PATH}/templates/auth/signup.html" "${PROJECT_PATH}/templates/auth/" 2>/dev/null || true
echo "   ✅ Template signup copiado"

# 4. Templates - Public Landing Chile
echo "🇨🇱 4/12: Copiando landing Chile completa..."
cp "${DEPLOY_PATH}/templates/public/landing_chile_completa.html" "${PROJECT_PATH}/templates/public/" 2>/dev/null || true
echo "   ✅ Landing Chile copiada"

# 5. Templates - USA Landing
echo "🇺🇸 5/12: Copiando landing USA actualizada..."
cp "${DEPLOY_PATH}/templates/onboarding/bienvenida_usa.html" "${PROJECT_PATH}/templates/onboarding/" 2>/dev/null || true
echo "   ✅ Landing USA actualizada"

# 6. Template - Login actualizado
echo "🔑 6/12: Copiando login actualizado..."
cp "${DEPLOY_PATH}/templates/account/login.html" "${PROJECT_PATH}/templates/account/" 2>/dev/null || true
echo "   ✅ Login actualizado"

# 7. Views Extra
echo "📝 7/12: Copiando views actualizadas..."
cp "${DEPLOY_PATH}/taller/views_extra/signup_complete.py" "${PROJECT_PATH}/taller/views_extra/" 2>/dev/null || true
cp "${DEPLOY_PATH}/taller/views_extra/payment_views.py" "${PROJECT_PATH}/taller/views_extra/" 2>/dev/null || true
cp "${DEPLOY_PATH}/taller/views_extra/paypal_webhook.py" "${PROJECT_PATH}/taller/views_extra/" 2>/dev/null || true
cp "${DEPLOY_PATH}/taller/views_extra/admin_payment_views.py" "${PROJECT_PATH}/taller/views_extra/" 2>/dev/null || true
echo "   ✅ Views copiadas"

# 8. Models
echo "📊 8/12: Copiando modelo de pago..."
cp "${DEPLOY_PATH}/taller/models/pago.py" "${PROJECT_PATH}/taller/models/" 2>/dev/null || true
echo "   ✅ Modelo actualizado"

# 9. Forms
echo "📋 9/12: Copiando formularios..."
mkdir -p "${PROJECT_PATH}/taller/forms"
cp "${DEPLOY_PATH}/taller/forms/signup_complete.py" "${PROJECT_PATH}/taller/forms/" 2>/dev/null || true
echo "   ✅ Formularios copiados"

# 10. Signals y Apps
echo "📡 10/12: Copiando signals..."
cp "${DEPLOY_PATH}/taller/signals.py" "${PROJECT_PATH}/taller/" 2>/dev/null || true
cp "${DEPLOY_PATH}/taller/apps.py" "${PROJECT_PATH}/taller/" 2>/dev/null || true
echo "   ✅ Signals copiados"

# 11. Management Commands
echo "⚙️  11/12: Copiando comandos de management..."
mkdir -p "${PROJECT_PATH}/taller/management/commands"
cp "${DEPLOY_PATH}/taller/management/__init__.py" "${PROJECT_PATH}/taller/management/" 2>/dev/null || true
cp "${DEPLOY_PATH}/taller/management/commands/"* "${PROJECT_PATH}/taller/management/commands/" 2>/dev/null || true
echo "   ✅ Comandos copiados"

# 12. URLs
echo "🔗 12/12: Copiando URLs..."
# Hacer backup primero
cp "${PROJECT_PATH}/gestion_taller/urls.py" "${PROJECT_PATH}/gestion_taller/urls.py.backup_${BACKUP_DATE}"
cp "${DEPLOY_PATH}/gestion_taller/urls.py" "${PROJECT_PATH}/gestion_taller/" 2>/dev/null || true
echo "   ✅ URLs actualizadas (backup guardado)"

echo ""
echo "======================================================"
echo "⚠️  IMPORTANTE: ACTUALIZAR SETTINGS.PY MANUALMENTE"
echo "======================================================"
echo ""
echo "Debes editar manualmente estos valores en settings.py:"
echo ""
echo "1. BUSCAR (línea ~74-77):"
echo "   ACCOUNT_EMAIL_VERIFICATION = os.getenv(..., \"none\" if DEBUG else \"mandatory\")"
echo "   ACCOUNT_EMAIL_REQUIRED = False"
echo ""
echo "2. CAMBIAR A:"
echo "   ACCOUNT_EMAIL_VERIFICATION = os.getenv(..., \"mandatory\")"
echo "   ACCOUNT_EMAIL_REQUIRED = True"
echo ""
echo "3. BUSCAR (línea ~78):"
echo "   ACCOUNT_CONFIRM_EMAIL_ON_GET = env_bool(...)"
echo ""
echo "4. CAMBIAR A:"
echo "   ACCOUNT_CONFIRM_EMAIL_ON_GET = True"
echo ""
echo "======================================================"
echo ""
read -p "¿Ya actualizaste settings.py manualmente? (s/n): " respuesta

if [ "$respuesta" != "s" ] && [ "$respuesta" != "S" ]; then
    echo ""
    echo "⚠️  Por favor actualiza settings.py primero"
    echo "   Comando: nano ${PROJECT_PATH}/gestion_taller/settings.py"
    echo ""
    echo "Luego ejecuta de nuevo este script"
    exit 0
fi

echo ""
echo "======================================================"
echo "🗄️  MIGRANDO BASE DE DATOS..."
echo "======================================================"
echo ""

cd "${PROJECT_PATH}"

# Backup de DB antes de migrar
echo "💾 Haciendo backup de DB antes de migrar..."
cp db.sqlite3 "db_antes_migracion_${BACKUP_DATE}.sqlite3"
echo "   ✅ Backup guardado"

# Crear migraciones
echo ""
echo "🔍 Verificando migraciones pendientes..."
python manage.py showmigrations

echo ""
echo "🔨 Creando migraciones..."
python manage.py makemigrations || echo "   ℹ️  No hay cambios en modelos"

echo ""
echo "⚡ Ejecutando migraciones..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo "   ✅ Migraciones completadas"
else
    echo "   ❌ Error en migraciones"
    echo "   Restaura el backup: cp db_antes_migracion_${BACKUP_DATE}.sqlite3 db.sqlite3"
    exit 1
fi

echo ""
echo "======================================================"
echo "🎨 RECOLECTANDO ARCHIVOS ESTÁTICOS..."
echo "======================================================"
echo ""

python manage.py collectstatic --clear --noinput
python manage.py collectstatic --noinput

echo ""
echo "======================================================"
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "======================================================"
echo ""
echo "⏭️  Siguiente paso:"
echo "   1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/"
echo "   2. Pestaña 'Web'"
echo "   3. Clic en 'Reload atlantareciclajes.pythonanywhere.com'"
echo "   4. Esperar 10-15 segundos"
echo "   5. Probar: https://atlantareciclajes.pythonanywhere.com/"
echo ""
echo "======================================================"
