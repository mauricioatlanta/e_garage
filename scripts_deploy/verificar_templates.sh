#!/bin/bash
# ======================================================
# Script: VERIFICAR TEMPLATES EN SERVIDOR
# Verifica qué templates están en el servidor vs los actualizados
# ======================================================

PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"
UPDATE_PATH="/home/atlantareciclajes/egarage_update/deploy_atlantareciclajes"

echo "======================================================"
echo "VERIFICANDO TEMPLATES..."
echo "======================================================"
echo ""

# Verificar templates de signup
echo "1. Templates de signup:"
echo "   En servidor:"
if [ -f "${PROJECT_PATH}/templates/account/signup.html" ]; then
    ls -lh "${PROJECT_PATH}/templates/account/signup.html"
    echo "   ✅ Existe"
else
    echo "   ❌ NO EXISTE"
fi

echo "   En actualización:"
if [ -f "${UPDATE_PATH}/templates/account/signup.html" ]; then
    ls -lh "${UPDATE_PATH}/templates/account/signup.html"
    echo "   ✅ Existe"
else
    echo "   ❌ NO EXISTE"
fi

echo ""
echo "2. Templates de Chile (cl/es):"
echo "   En servidor:"
if [ -d "${PROJECT_PATH}/templates/cl/es" ]; then
    echo "   ✅ Carpeta existe"
    ls -1 "${PROJECT_PATH}/templates/cl/es/" | head -5
else
    echo "   ❌ Carpeta NO EXISTE"
fi

echo "   En actualización:"
if [ -d "${UPDATE_PATH}/templates/cl/es" ]; then
    echo "   ✅ Carpeta existe"
    ls -1 "${UPDATE_PATH}/templates/cl/es/" | head -5
else
    echo "   ❌ Carpeta NO EXISTE"
fi

echo ""
echo "3. Templates de onboarding:"
echo "   En servidor:"
if [ -d "${PROJECT_PATH}/templates/cl/es/onboarding" ]; then
    echo "   ✅ Carpeta existe"
    ls -1 "${PROJECT_PATH}/templates/cl/es/onboarding/" | head -5
else
    echo "   ❌ Carpeta NO EXISTE"
fi

echo "   En actualización:"
if [ -d "${UPDATE_PATH}/templates/cl/es/onboarding" ]; then
    echo "   ✅ Carpeta existe"
    ls -1 "${UPDATE_PATH}/templates/cl/es/onboarding/" | head -5
else
    echo "   ❌ Carpeta NO EXISTE"
fi

echo ""
echo "======================================================"
echo "COMPARANDO FECHAS DE MODIFICACION..."
echo "======================================================"
echo ""

if [ -f "${PROJECT_PATH}/templates/account/signup.html" ] && [ -f "${UPDATE_PATH}/templates/account/signup.html" ]; then
    echo "signup.html:"
    echo "   Servidor: $(stat -c %y "${PROJECT_PATH}/templates/account/signup.html" 2>/dev/null || stat -f "%Sm" "${PROJECT_PATH}/templates/account/signup.html")"
    echo "   Actualización: $(stat -c %y "${UPDATE_PATH}/templates/account/signup.html" 2>/dev/null || stat -f "%Sm" "${UPDATE_PATH}/templates/account/signup.html")"
fi

echo ""
echo "======================================================"











