#!/bin/bash
# Script para corregir views.py en el servidor
# Ejecutar: bash fix_servidor.sh

cd /home/atlantareciclajes/apps/egarage/current || {
    echo "❌ Error: No se pudo cambiar al directorio"
    exit 1
}

FILE="taller/documentos/views.py"

echo "🔧 Corrigiendo $FILE..."

# Verificar que el archivo existe
if [ ! -f "$FILE" ]; then
    echo "❌ Archivo no encontrado: $FILE"
    exit 1
fi

# Crear backup
cp "$FILE" "${FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "📦 Backup creado"

# Eliminar marcadores de conflicto
sed -i '/^<<<<<<</d' "$FILE"
sed -i '/^=======$/d' "$FILE"
sed -i '/^>>>>>>>/d' "$FILE"

echo "✅ Marcadores de conflicto eliminados"

# Verificar sintaxis
python3 -m py_compile "$FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Sintaxis Python válida"
else
    echo "❌ Error de sintaxis"
    echo "🔄 Restaurando desde backup..."
    # Restaurar el último backup
    BACKUP=$(ls -t ${FILE}.backup.* 2>/dev/null | head -1)
    if [ -n "$BACKUP" ]; then
        cp "$BACKUP" "$FILE"
        echo "✅ Restaurado desde backup"
    fi
    exit 1
fi

# Reiniciar servidor
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor WSGI reiniciado"

echo ""
echo "✅ Proceso completado exitosamente"

