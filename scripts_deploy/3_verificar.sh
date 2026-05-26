#!/bin/bash
# ======================================================
# Script 3: VERIFICAR ACTUALIZACIÓN
# Para: atlantareciclajes @ DigitalOcean
# ======================================================

echo "======================================================"
echo "✅ SCRIPT 3: VERIFICACIÓN POST-ACTUALIZACIÓN"
echo "======================================================"
echo ""

# Variables
PROJECT_PATH="/home/atlantareciclajes/egarage"

cd "${PROJECT_PATH}"

echo "🔍 Verificando instalación..."
echo ""

# 1. Verificar archivos críticos
echo "📁 1/5: Verificando archivos críticos..."
ARCHIVOS_CRITICOS=(
    "templates/email/pago_confirmado.html"
    "templates/auth/signup.html"
    "templates/public/landing_chile_completa.html"
    "taller/views_extra/signup_complete.py"
    "taller/views_extra/payment_views.py"
    "taller/signals.py"
    "taller/management/commands/enviar_recordatorios.py"
)

ARCHIVOS_OK=0
ARCHIVOS_FALTANTES=0

for archivo in "${ARCHIVOS_CRITICOS[@]}"; do
    if [ -f "${PROJECT_PATH}/${archivo}" ]; then
        echo "   ✅ ${archivo}"
        ((ARCHIVOS_OK++))
    else
        echo "   ❌ ${archivo} NO ENCONTRADO"
        ((ARCHIVOS_FALTANTES++))
    fi
done

echo ""
echo "   📊 Resultado: ${ARCHIVOS_OK}/${#ARCHIVOS_CRITICOS[@]} archivos correctos"

# 2. Verificar migraciones
echo ""
echo "🗄️  2/5: Verificando migraciones..."
python manage.py showmigrations | grep "\[X\]" > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Migraciones aplicadas"
else
    echo "   ⚠️  Algunas migraciones pendientes"
fi

# 3. Contar usuarios
echo ""
echo "👥 3/5: Contando usuarios..."
python manage.py shell << EOF
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
print(f"   Usuarios: {User.objects.count()}")
print(f"   Empresas: {Empresa.objects.count()}")
EOF

# 4. Verificar configuración
echo ""
echo "⚙️  4/5: Verificando configuración..."
python manage.py check --deploy 2>/dev/null || python manage.py check

# 5. Verificar estáticos
echo ""
echo "🎨 5/5: Verificando archivos estáticos..."
if [ -d "${PROJECT_PATH}/staticfiles" ] || [ -d "${PROJECT_PATH}/static" ]; then
    echo "   ✅ Archivos estáticos recolectados"
else
    echo "   ⚠️  No se encontró carpeta de estáticos"
fi

# Resumen
echo ""
echo "======================================================"
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "======================================================"
echo ""

if [ ${ARCHIVOS_FALTANTES} -eq 0 ]; then
    echo "✅ Archivos: TODOS COPIADOS CORRECTAMENTE"
else
    echo "⚠️  Archivos: ${ARCHIVOS_FALTANTES} archivos faltantes"
fi

echo ""
echo "🌐 Verificaciones Manuales Pendientes:"
echo ""
echo "1. Homepage:"
echo "   https://atlantareciclajes/"
echo "   ¿Carga sin errores?"
echo ""
echo "2. Landing Chile:"
echo "   https://atlantareciclajes/cl/"
echo "   ¿Se ve la nueva landing completa?"
echo ""
echo "3. Login:"
echo "   https://atlantareciclajes/accounts/login/"
echo "   ¿Funciona con usuario existente?"
echo ""
echo "4. Registro:"
echo "   https://atlantareciclajes/accounts/signup/"
echo "   ¿Pide confirmación de email?"
echo ""
echo "======================================================"
echo ""
echo "📋 LOGS DE ERROR:"
echo "   Ver en: https://www/user/atlantareciclajes/"
echo "   Pestaña Web → Error log"
echo ""
echo "======================================================"
