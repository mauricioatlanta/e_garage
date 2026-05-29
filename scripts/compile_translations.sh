#!/bin/bash
# Script para compilar archivos de traducción (.po) en producción
# Este script debe ejecutarse después de cada actualización de traducciones
# para asegurar que los archivos .mo estén actualizados y no haya impacto en rendimiento

set -e  # Salir si hay algún error

echo "🌐 Compilando archivos de traducción..."

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Compilar todos los archivos .po a .mo
python manage.py compilemessages

# Verificar que los archivos .mo se hayan generado correctamente
echo "✅ Verificando archivos compilados..."

LOCALE_DIRS=("locale" "taller/locale" "ubicacion/locale")

for locale_dir in "${LOCALE_DIRS[@]}"; do
    if [ -d "$locale_dir" ]; then
        echo "📁 Verificando $locale_dir..."
        find "$locale_dir" -name "*.mo" -type f | while read mo_file; do
            if [ -f "$mo_file" ]; then
                echo "  ✓ $(basename $mo_file) compilado correctamente"
            fi
        done
    fi
done

echo "✅ Compilación de traducciones completada exitosamente"
echo "📝 Los archivos .mo están listos para producción"


