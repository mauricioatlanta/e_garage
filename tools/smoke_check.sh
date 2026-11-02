#!/bin/bash
# Script de checklist de salud para eGarage (Linux/macOS)
# Ejecuta todas las verificaciones necesarias para confirmar que el sistema está sano

echo "🚀 CHECKLIST DE SALUD DE EGARAGE"
echo "============================================================"

set -e  # Exit on any error
exit_code=0

test_command() {
    local command="$1"
    local description="$2"
    echo "🔍 $description"
    if eval "$command"; then
        echo "✅ $description - OK"
        return 0
    else
        echo "❌ $description - ERROR"
        return 1
    fi
}

# 1. Arranque mínimo
echo ""
echo "📋 1. ARRANQUE MÍNIMO"
if ! test_command 'DJANGO_SETTINGS_MODULE="gestion_taller.settings.min" python manage.py check' "Django mínimo"; then
    exit_code=1
fi

# 2. Arranque seguro (sin logging ruidoso)
echo ""
echo "📋 2. ARRANQUE SEGURO"
if ! test_command 'DJANGO_SETTINGS_MODULE="gestion_taller.settings" EGARAGE_SAFE_MODE="1" python manage.py check' "Django modo seguro"; then
    exit_code=1
fi

# 3. Migraciones y estado DB
echo ""
echo "📋 3. MIGRACIONES Y BASE DE DATOS"
if ! test_command 'python manage.py makemigrations --check' "Verificar migraciones pendientes"; then
    exit_code=1
fi
if ! test_command 'python manage.py migrate --check' "Verificar estado de migraciones"; then
    exit_code=1
fi

# 4. Archivos estáticos e i18n
echo ""
echo "📋 4. ARCHIVOS ESTÁTICOS E I18N"
if ! test_command 'python manage.py collectstatic --noinput --dry-run' "Verificar archivos estáticos"; then
    exit_code=1
fi
if ! test_command 'python manage.py compilemessages --dry-run' "Verificar mensajes i18n"; then
    exit_code=1
fi

# 5. Smoke tests personalizados
echo ""
echo "📋 5. SMOKE TESTS PERSONALIZADOS"
if ! test_command 'python tools/eg_diag.py' "Diagnóstico automatizado"; then
    exit_code=1
fi

# 6. Verificar estructura de directorios críticos
echo ""
echo "📋 6. ESTRUCTURA DE DIRECTORIOS"
critical_dirs=("templates_canonical" "locale" "static" "media" "logs")
for dir in "${critical_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ Directorio $dir existe"
    else
        echo "❌ Directorio $dir no existe"
        exit_code=1
    fi
done

# Resumen final
echo ""
echo "============================================================"
if [ $exit_code -eq 0 ]; then
    echo "🎉 ¡SISTEMA COMPLETAMENTE SANO!"
    echo "   Todos los checks pasaron exitosamente."
else
    echo "⚠️  SE ENCONTRARON PROBLEMAS"
    echo "   Revisa los errores anteriores antes de continuar."
fi
echo "============================================================"

exit $exit_code
