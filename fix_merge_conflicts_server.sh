#!/bin/bash
# Script para limpiar marcadores de conflicto de merge en el servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/current"

cd "$RELEASE_DIR" || exit 1

echo "🧹 Limpiando marcadores de conflicto de merge..."

# Archivo problemático
FILE="taller/documentos/views.py"

if [ ! -f "$FILE" ]; then
    echo "❌ Archivo no encontrado: $FILE"
    exit 1
fi

# Verificar si hay marcadores de conflicto
if grep -q "^<<<<<<<" "$FILE" || grep -q "^=======" "$FILE" || grep -q "^>>>>>>>" "$FILE"; then
    echo "⚠️  Marcadores de conflicto encontrados en $FILE"
    
    # Opción 1: Eliminar líneas con marcadores
    echo "  Limpiando marcadores..."
    sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' "$FILE"
    
    # Verificar sintaxis
    python3 -m py_compile "$FILE" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  ✅ Sintaxis Python válida después de limpieza"
    else
        echo "  ⚠️  Error de sintaxis persistente, restaurando desde Git..."
        # Restaurar desde Git
        git checkout HEAD -- "$FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ Archivo restaurado desde Git"
        else
            echo "  ❌ No se pudo restaurar desde Git"
            exit 1
        fi
    fi
else
    echo "✅ No se encontraron marcadores de conflicto"
fi

# Verificar otros archivos Python comunes
echo ""
echo "🔍 Verificando otros archivos Python..."
for pyfile in gestion_taller/settings.py gestion_taller/settings/base.py gestion_taller/compacto/settings.py; do
    if [ -f "$pyfile" ]; then
        if grep -q "^<<<<<<<" "$pyfile" || grep -q "^=======" "$pyfile" || grep -q "^>>>>>>>" "$pyfile"; then
            echo "  ⚠️  Marcadores encontrados en $pyfile, limpiando..."
            sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' "$pyfile"
        fi
    fi
done

echo ""
echo "🔄 Reiniciando servidor WSGI..."
touch /var/www/www_egarage_cl_wsgi.py

echo ""
echo "✅ Proceso completado."

