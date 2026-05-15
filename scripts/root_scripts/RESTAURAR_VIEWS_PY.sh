#!/bin/bash
# Script para restaurar taller/documentos/views.py desde Git
# Ejecutar en el servidor: bash RESTAURAR_VIEWS_PY.sh

cd /home/atlantareciclajes/apps/egarage/current || {
    echo "❌ Error: No se pudo cambiar al directorio"
    exit 1
}

FILE="taller/documentos/views.py"

echo "🔄 Restaurando $FILE desde Git..."

# Crear backup
if [ -f "$FILE" ]; then
    BACKUP="${FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$FILE" "$BACKUP"
    echo "📦 Backup creado: $BACKUP"
fi

# Obtener última versión desde Git
echo "📥 Obteniendo última versión desde Git..."
git fetch origin main 2>&1

# Restaurar desde origin/main
echo "🔄 Restaurando desde origin/main..."
git checkout origin/main -- "$FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Archivo restaurado desde origin/main"
    
    # Verificar sintaxis
    echo "🔍 Verificando sintaxis Python..."
    python3 -m py_compile "$FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Sintaxis Python válida"
        
        # Verificar que no tenga marcadores de conflicto
        if grep -q "^<<<<<<<" "$FILE" || grep -q "^=======" "$FILE" || grep -q "^>>>>>>>" "$FILE"; then
            echo "⚠️  Aún hay marcadores de conflicto, eliminándolos..."
            sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' "$FILE"
            python3 -m py_compile "$FILE" 2>&1
            if [ $? -eq 0 ]; then
                echo "✅ Conflictos eliminados y sintaxis válida"
            fi
        else
            echo "✅ Sin marcadores de conflicto"
        fi
        
        # Reiniciar servidor
        touch /var/www/www_egarage_cl_wsgi.py
        echo "✅ Servidor WSGI reiniciado"
        echo ""
        echo "✅ PROCESO COMPLETADO EXITOSAMENTE"
    else
        echo "❌ Error de sintaxis después de restaurar"
        echo "🔄 Restaurando desde backup..."
        if [ -n "$BACKUP" ] && [ -f "$BACKUP" ]; then
            cp "$BACKUP" "$FILE"
            echo "✅ Restaurado desde backup"
        fi
        exit 1
    fi
else
    echo "❌ Error al restaurar desde Git"
    exit 1
fi



