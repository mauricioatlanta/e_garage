#!/bin/bash
# ======================================================
# Script 2: ACTUALIZAR EGARAGE (RUTA CORREGIDA)
# Para: atlantareciclajes @ PythonAnywhere
# Ruta: /home/atlantareciclajes/apps/egarage/current
# ======================================================

set -e  # Detener si hay error

echo "======================================================"
echo "🚀 SCRIPT 2: ACTUALIZACIÓN DE EGARAGE"
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
echo "📋 COPIANDO ARCHIVOS..."
echo "======================================================"
echo ""

# 1. Templates - Email
echo "📧 1/12: Copiando templates de email..."
mkdir -p "${PROJECT_PATH}/templates/email"
if [ -d "${DEPLOY_PATH}/templates/email" ]; then
    cp -r "${DEPLOY_PATH}/templates/email/"* "${PROJECT_PATH}/templates/email/"
    echo "   ✅ Templates de email copiados"
else
    echo "   ⚠️  No se encontró templates/email/ en el paquete"
fi

# 2. Templates - Account Email
echo "📧 2/12: Copiando templates de confirmación..."
mkdir -p "${PROJECT_PATH}/templates/account/email"
if [ -d "${DEPLOY_PATH}/templates/account/email" ]; then
    cp -r "${DEPLOY_PATH}/templates/account/email/"* "${PROJECT_PATH}/templates/account/email/"
    echo "   ✅ Templates de confirmación copiados"
else
    echo "   ⚠️  No se encontró templates/account/email/ en el paquete"
fi

# 3. Templates - Auth
echo "🔐 3/12: Copiando template de signup..."
mkdir -p "${PROJECT_PATH}/templates/auth"
if [ -f "${DEPLOY_PATH}/templates/auth/signup.html" ]; then
    cp "${DEPLOY_PATH}/templates/auth/signup.html" "${PROJECT_PATH}/templates/auth/"
    echo "   ✅ Template signup copiado"
else
    echo "   ⚠️  No se encontró signup.html en el paquete"
fi

# 4. Templates - Public Landing Chile
echo "🇨🇱 4/12: Copiando landing Chile completa..."
if [ -f "${DEPLOY_PATH}/templates/public/landing_chile_completa.html" ]; then
    cp "${DEPLOY_PATH}/templates/public/landing_chile_completa.html" "${PROJECT_PATH}/templates/public/"
    echo "   ✅ Landing Chile copiada"
else
    echo "   ⚠️  No se encontró landing_chile_completa.html"
fi

# 5. Templates - USA Landing
echo "🇺🇸 5/12: Copiando landing USA actualizada..."
if [ -f "${DEPLOY_PATH}/templates/onboarding/bienvenida_usa.html" ]; then
    cp "${DEPLOY_PATH}/templates/onboarding/bienvenida_usa.html" "${PROJECT_PATH}/templates/onboarding/"
    echo "   ✅ Landing USA actualizada"
else
    echo "   ⚠️  No se encontró bienvenida_usa.html"
fi

# 6. Template - Login actualizado
echo "🔑 6/12: Copiando login actualizado..."
if [ -f "${DEPLOY_PATH}/templates/account/login.html" ]; then
    cp "${DEPLOY_PATH}/templates/account/login.html" "${PROJECT_PATH}/templates/account/"
    echo "   ✅ Login actualizado"
else
    echo "   ⚠️  No se encontró login.html"
fi

# 7. Views Extra
echo "📝 7/12: Copiando views actualizadas..."
VIEWS_COPIADAS=0
[ -f "${DEPLOY_PATH}/taller/views_extra/signup_complete.py" ] && cp "${DEPLOY_PATH}/taller/views_extra/signup_complete.py" "${PROJECT_PATH}/taller/views_extra/" && ((VIEWS_COPIADAS++))
[ -f "${DEPLOY_PATH}/taller/views_extra/payment_views.py" ] && cp "${DEPLOY_PATH}/taller/views_extra/payment_views.py" "${PROJECT_PATH}/taller/views_extra/" && ((VIEWS_COPIADAS++))
[ -f "${DEPLOY_PATH}/taller/views_extra/paypal_webhook.py" ] && cp "${DEPLOY_PATH}/taller/views_extra/paypal_webhook.py" "${PROJECT_PATH}/taller/views_extra/" && ((VIEWS_COPIADAS++))
[ -f "${DEPLOY_PATH}/taller/views_extra/admin_payment_views.py" ] && cp "${DEPLOY_PATH}/taller/views_extra/admin_payment_views.py" "${PROJECT_PATH}/taller/views_extra/" && ((VIEWS_COPIADAS++))
echo "   ✅ ${VIEWS_COPIADAS}/4 views copiadas"

# 8. Models
echo "📊 8/12: Copiando modelo de pago..."
if [ -f "${DEPLOY_PATH}/taller/models/pago.py" ]; then
    cp "${DEPLOY_PATH}/taller/models/pago.py" "${PROJECT_PATH}/taller/models/"
    echo "   ✅ Modelo actualizado"
else
    echo "   ⚠️  No se encontró pago.py"
fi

# 9. Forms
echo "📋 9/12: Copiando formularios..."
mkdir -p "${PROJECT_PATH}/taller/forms"
if [ -f "${DEPLOY_PATH}/taller/forms/signup_complete.py" ]; then
    cp "${DEPLOY_PATH}/taller/forms/signup_complete.py" "${PROJECT_PATH}/taller/forms/"
    echo "   ✅ Formularios copiados"
else
    echo "   ⚠️  No se encontró signup_complete.py"
fi

# 10. Signals y Apps
echo "📡 10/12: Copiando signals..."
SIGNALS_OK=0
[ -f "${DEPLOY_PATH}/taller/signals.py" ] && cp "${DEPLOY_PATH}/taller/signals.py" "${PROJECT_PATH}/taller/" && ((SIGNALS_OK++))
[ -f "${DEPLOY_PATH}/taller/apps.py" ] && cp "${DEPLOY_PATH}/taller/apps.py" "${PROJECT_PATH}/taller/" && ((SIGNALS_OK++))
echo "   ✅ ${SIGNALS_OK}/2 archivos copiados"

# 11. Management Commands
echo "⚙️  11/12: Copiando comandos de management..."
mkdir -p "${PROJECT_PATH}/taller/management/commands"
if [ -d "${DEPLOY_PATH}/taller/management" ]; then
    cp -r "${DEPLOY_PATH}/taller/management/"* "${PROJECT_PATH}/taller/management/"
    echo "   ✅ Comandos copiados"
else
    echo "   ⚠️  No se encontró management/"
fi

# 12. URLs
echo "🔗 12/12: Copiando URLs..."
if [ -f "${PROJECT_PATH}/gestion_taller/urls.py" ]; then
    cp "${PROJECT_PATH}/gestion_taller/urls.py" "${PROJECT_PATH}/gestion_taller/urls.py.backup_${BACKUP_DATE}"
    echo "   ✅ Backup de URLs guardado"
fi

if [ -f "${DEPLOY_PATH}/gestion_taller/urls.py" ]; then
    cp "${DEPLOY_PATH}/gestion_taller/urls.py" "${PROJECT_PATH}/gestion_taller/"
    echo "   ✅ URLs actualizadas"
else
    echo "   ⚠️  No se encontró urls.py en el paquete"
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
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "======================================================"
echo ""
echo "⏭️  SIGUIENTE PASO - RELOAD DE LA APP:"
echo ""
echo "   1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/"
echo "   2. Clic en pestaña 'Web'"
echo "   3. Buscar: atlantareciclajes.pythonanywhere.com"
echo "   4. Clic en botón verde grande:"
echo "      'Reload atlantareciclajes.pythonanywhere.com'"
echo "   5. Esperar 15 segundos"
echo "   6. Probar: https://atlantareciclajes.pythonanywhere.com/cl/"
echo ""
echo "Luego ejecuta: ./3_verificar_FIXED.sh"
echo ""
echo "======================================================"

