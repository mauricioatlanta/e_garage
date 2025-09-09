#!/bin/bash
# Script para desplegar eGarage en Render
# Uso: ./deploy_to_render.sh

echo "🚀 Iniciando despliegue de eGarage en Render..."
echo "================================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

# Paso 1: Verificar setup
echo "🔍 Paso 1: Verificando configuración..."
python tools/verify_render_setup.py
if [ $? -ne 0 ]; then
    echo "❌ Error en la verificación. Corrige los problemas antes de continuar."
    exit 1
fi

# Paso 2: Limpiar proyecto
echo ""
echo "🧹 Paso 2: Limpiando proyecto..."
python tools/audit_and_cleanup.py --root . --apply
if [ $? -ne 0 ]; then
    echo "❌ Error en la limpieza. Revisa el script de auditoría."
    exit 1
fi

# Paso 3: Verificar Git
echo ""
echo "📝 Paso 3: Preparando Git..."
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No hay cambios pendientes en Git"
else
    echo "📋 Cambios detectados:"
    git status --short
    
    read -p "¿Deseas hacer commit de estos cambios? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "chore: cleanup and prepare for Render deployment"
        echo "✅ Cambios commiteados"
    else
        echo "⚠️  Saltando commit. Asegúrate de hacer commit manualmente antes del despliegue."
    fi
fi

# Paso 4: Push a GitHub
echo ""
echo "📤 Paso 4: Pusheando a GitHub..."
current_branch=$(git branch --show-current)
echo "Rama actual: $current_branch"

read -p "¿Deseas hacer push a GitHub? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin $current_branch
    if [ $? -eq 0 ]; then
        echo "✅ Push exitoso"
    else
        echo "❌ Error en el push. Verifica tu conexión y permisos."
        exit 1
    fi
else
    echo "⚠️  Saltando push. Asegúrate de hacer push manualmente antes del despliegue."
fi

# Paso 5: Instrucciones finales
echo ""
echo "🎉 ¡Preparación completada!"
echo "================================================"
echo ""
echo "📋 Próximos pasos manuales:"
echo "1. Ve a https://render.com"
echo "2. Crea una cuenta y conecta tu repositorio de GitHub"
echo "3. Selecciona 'New' → 'Blueprint'"
echo "4. Elige tu repositorio e_garage"
echo "5. Render detectará automáticamente render.yaml"
echo "6. Haz clic en 'Apply' para desplegar"
echo ""
echo "🔗 Tu aplicación estará disponible en:"
echo "   https://eggarage-web.onrender.com"
echo ""
echo "📚 Para más detalles, consulta: INSTRUCCIONES_LIMPIEZA_RENDER.md"
echo ""
echo "✨ ¡Despliegue exitoso!"
