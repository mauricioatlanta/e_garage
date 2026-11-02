#!/bin/bash
# Script para limpiar marcadores de conflicto de merge en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🧹 Limpiando marcadores de conflicto de merge..."

FILE="taller/documentos/views.py"

if [ ! -f "$FILE" ]; then
    echo "❌ Archivo no encontrado: $FILE"
    exit 1
fi

# Verificar si hay marcadores de conflicto
if grep -q "^<<<<<<<" "$FILE" || grep -q "^=======" "$FILE" || grep -q "^>>>>>>>" "$FILE"; then
    echo "⚠️  Marcadores de conflicto encontrados en $FILE"
    
    # Crear backup
    cp "$FILE" "${FILE}.backup"
    echo "  📦 Backup creado: ${FILE}.backup"
    
    # Eliminar líneas con marcadores de conflicto
    sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' "$FILE"
    echo "  ✅ Marcadores eliminados"
    
    # Verificar sintaxis
    python3 -m py_compile "$FILE" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  ✅ Sintaxis Python válida"
    else
        echo "  ⚠️  Error de sintaxis después de limpieza"
        echo "  🔄 Restaurando desde Git..."
        git checkout HEAD -- "$FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ Archivo restaurado desde Git"
        else
            echo "  ❌ No se pudo restaurar desde Git"
            echo "  📦 Restaurando desde backup..."
            cp "${FILE}.backup" "$FILE"
            exit 1
        fi
    fi
else
    echo "✅ No se encontraron marcadores de conflicto"
fi

echo ""
echo "🔄 Reiniciando servidor WSGI..."
touch /var/www/www_egarage_cl_wsgi.py

echo ""
echo "✅ Proceso completado."



