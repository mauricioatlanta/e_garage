#!/bin/bash
# ======================================================
# Script 3: VERIFICAR (RUTA CORREGIDA)
# Para: atlantareciclajes @ DigitalOcean
# Ruta: /home/atlantareciclajes/apps/egarage/current
# ======================================================

echo "======================================================"
echo "✅ SCRIPT 3: VERIFICACIÓN POST-ACTUALIZACIÓN"
echo "======================================================"
echo ""

# Variables - RUTA CORREGIDA
PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"

if [ ! -d "${PROJECT_PATH}" ]; then
    echo "❌ ERROR: No se encontró ${PROJECT_PATH}"
    exit 1
fi

cd "${PROJECT_PATH}"

echo "🔍 Verificando instalación en: ${PROJECT_PATH}"
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
python manage.py showmigrations 2>&1 | grep -q "\[X\]"
if [ $? -eq 0 ]; then
    echo "   ✅ Migraciones aplicadas"
else
    echo "   ⚠️  Verificar migraciones manualmente"
fi

# 3. Contar usuarios
echo ""
echo "👥 3/5: Contando usuarios DESPUÉS de actualización..."
python manage.py shell << 'EOF' 2>&1
from django.contrib.auth.models import User
try:
    from taller.models.empresa import Empresa
    print(f"   Usuarios: {User.objects.count()}")
    print(f"   Empresas: {Empresa.objects.count()}")
except Exception as e:
    print(f"   Usuarios: {User.objects.count()}")
    print(f"   ⚠️ Error contando empresas: {e}")
EOF

# 4. Verificar configuración
echo ""
echo "⚙️  4/5: Verificando configuración Django..."
python manage.py check 2>&1 | tail -5

# 5. Verificar estáticos
echo ""
echo "🎨 5/5: Verificando archivos estáticos..."
if [ -d "${PROJECT_PATH}/staticfiles" ] || [ -d "${PROJECT_PATH}/static" ]; then
    COUNT=$(find "${PROJECT_PATH}/staticfiles" -type f 2>/dev/null | wc -l)
    echo "   ✅ Archivos estáticos recolectados (${COUNT} archivos)"
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
echo "======================================================"
echo "🌐 PRUEBAS MANUALES REQUERIDAS:"
echo "======================================================"
echo ""
echo "Abre estas URLs en tu navegador:"
echo ""
echo "1. Homepage:"
echo "   https://atlantareciclajes/"
echo "   ¿Carga sin errores? □"
echo ""
echo "2. Landing Chile (NUEVA):"
echo "   https://atlantareciclajes/cl/"
echo "   ¿Se ve completa con pricing y testimonios? □"
echo ""
echo "3. Registro:"
echo "   https://atlantareciclajes/accounts/signup/?from=cl"
echo "   ¿Está en español? □"
echo "   ¿País pre-seleccionado: Chile? □"
echo ""
echo "4. Login existente:"
echo "   https://atlantareciclajes/accounts/login/"
echo "   ¿Funciona con usuario existente? □"
echo ""
echo "======================================================"
echo "📋 LOGS DE ERROR:"
echo "======================================================"
echo ""
echo "Ver en: https://www/user/atlantareciclajes/"
echo "Pestaña Web → Error log"
echo ""
echo "O en consola:"
echo "tail -50 /var/log/atlantareciclajes.error.log"
echo ""
echo "======================================================"

if [ ${ARCHIVOS_FALTANTES} -eq 0 ]; then
    echo ""
    echo "✅ ¡ACTUALIZACIÓN EXITOSA!"
    echo ""
else
    echo ""
    echo "⚠️  HAY ARCHIVOS FALTANTES"
    echo "   Revisa el paquete egarage_update_atlantareciclajes.zip"
    echo ""
fi

echo "======================================================"
