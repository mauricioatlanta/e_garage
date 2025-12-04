#!/bin/bash
# ======================================================
# Script: COPIAR TODOS LOS TEMPLATES
# Copia todos los templates desde deploy_atlantareciclajes
# ======================================================

set -e

PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"
UPDATE_PATH="/home/atlantareciclajes/egarage_update/deploy_atlantareciclajes"
DEPLOY_PATH="${UPDATE_PATH}"

echo "======================================================"
echo "COPIANDO TODOS LOS TEMPLATES..."
echo "======================================================"
echo ""

# Verificar que existe deploy_atlantareciclajes
if [ ! -d "${DEPLOY_PATH}" ]; then
    echo "❌ ERROR: No se encontró ${DEPLOY_PATH}"
    echo "   Verifica que los archivos estén descomprimidos"
    exit 1
fi

# Verificar que existe el proyecto
if [ ! -d "${PROJECT_PATH}" ]; then
    echo "❌ ERROR: No se encontró ${PROJECT_PATH}"
    exit 1
fi

echo "✅ Origen: ${DEPLOY_PATH}/templates"
echo "✅ Destino: ${PROJECT_PATH}/templates"
echo ""

# Copiar TODA la carpeta de templates
if [ -d "${DEPLOY_PATH}/templates" ]; then
    echo "📁 Copiando estructura completa de templates..."
    
    # Copiar todas las carpetas de templates
    TEMPLATES_COPIADOS=0
    
    # Templates principales
    [ -d "${DEPLOY_PATH}/templates/account" ] && cp -r "${DEPLOY_PATH}/templates/account" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ account/"
    [ -d "${DEPLOY_PATH}/templates/auth" ] && cp -r "${DEPLOY_PATH}/templates/auth" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ auth/"
    [ -d "${DEPLOY_PATH}/templates/cl" ] && cp -r "${DEPLOY_PATH}/templates/cl" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ cl/"
    [ -d "${DEPLOY_PATH}/templates/us" ] && cp -r "${DEPLOY_PATH}/templates/us" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ us/"
    [ -d "${DEPLOY_PATH}/templates/mx" ] && cp -r "${DEPLOY_PATH}/templates/mx" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ mx/"
    [ -d "${DEPLOY_PATH}/templates/co" ] && cp -r "${DEPLOY_PATH}/templates/co" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ co/"
    [ -d "${DEPLOY_PATH}/templates/pe" ] && cp -r "${DEPLOY_PATH}/templates/pe" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ pe/"
    [ -d "${DEPLOY_PATH}/templates/ec" ] && cp -r "${DEPLOY_PATH}/templates/ec" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ ec/"
    [ -d "${DEPLOY_PATH}/templates/ve" ] && cp -r "${DEPLOY_PATH}/templates/ve" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ ve/"
    [ -d "${DEPLOY_PATH}/templates/br" ] && cp -r "${DEPLOY_PATH}/templates/br" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ br/"
    
    [ -d "${DEPLOY_PATH}/templates/taller" ] && cp -r "${DEPLOY_PATH}/templates/taller" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ taller/"
    [ -d "${DEPLOY_PATH}/templates/email" ] && cp -r "${DEPLOY_PATH}/templates/email" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ email/"
    [ -d "${DEPLOY_PATH}/templates/emails" ] && cp -r "${DEPLOY_PATH}/templates/emails" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ emails/"
    [ -d "${DEPLOY_PATH}/templates/onboarding" ] && cp -r "${DEPLOY_PATH}/templates/onboarding" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ onboarding/"
    [ -d "${DEPLOY_PATH}/templates/portal" ] && cp -r "${DEPLOY_PATH}/templates/portal" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ portal/"
    [ -d "${DEPLOY_PATH}/templates/suscripcion" ] && cp -r "${DEPLOY_PATH}/templates/suscripcion" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ suscripcion/"
    [ -d "${DEPLOY_PATH}/templates/registration" ] && cp -r "${DEPLOY_PATH}/templates/registration" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ registration/"
    [ -d "${DEPLOY_PATH}/templates/components" ] && cp -r "${DEPLOY_PATH}/templates/components" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ components/"
    [ -d "${DEPLOY_PATH}/templates/errors" ] && cp -r "${DEPLOY_PATH}/templates/errors" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ errors/"
    [ -d "${DEPLOY_PATH}/templates/landing" ] && cp -r "${DEPLOY_PATH}/templates/landing" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ landing/"
    
    # Templates adicionales
    [ -d "${DEPLOY_PATH}/templates/admin_panel" ] && cp -r "${DEPLOY_PATH}/templates/admin_panel" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ admin_panel/"
    [ -d "${DEPLOY_PATH}/templates/analytics" ] && cp -r "${DEPLOY_PATH}/templates/analytics" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ analytics/"
    [ -d "${DEPLOY_PATH}/templates/business_intelligence" ] && cp -r "${DEPLOY_PATH}/templates/business_intelligence" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ business_intelligence/"
    [ -d "${DEPLOY_PATH}/templates/settings" ] && cp -r "${DEPLOY_PATH}/templates/settings" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ settings/"
    [ -d "${DEPLOY_PATH}/templates/suspension" ] && cp -r "${DEPLOY_PATH}/templates/suspension" "${PROJECT_PATH}/templates/" && ((TEMPLATES_COPIADOS++)) && echo "   ✅ suspension/"
    
    # Templates base
    [ -f "${DEPLOY_PATH}/templates/base.html" ] && cp "${DEPLOY_PATH}/templates/base.html" "${PROJECT_PATH}/templates/" && echo "   ✅ base.html"
    [ -f "${DEPLOY_PATH}/templates/landing_inicio.html" ] && cp "${DEPLOY_PATH}/templates/landing_inicio.html" "${PROJECT_PATH}/templates/" && echo "   ✅ landing_inicio.html"
    
    echo ""
    echo "======================================================"
    echo "✅ TEMPLATES COPIADOS: ${TEMPLATES_COPIADOS} carpetas"
    echo "======================================================"
    echo ""
    echo "⏭️  SIGUIENTE PASO:"
    echo "   1. Reload en Web panel de PythonAnywhere"
    echo "   2. Limpiar caché del navegador (Ctrl+Shift+R)"
    echo ""
else
    echo "❌ ERROR: No se encontró ${DEPLOY_PATH}/templates"
    exit 1
fi


