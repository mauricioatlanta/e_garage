#!/bin/bash
# Script para restaurar completamente urls.py desde Git
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup final..."
cp "$FILE" "$FILE.backup_final_$(date +%Y%m%d_%H%M%S)"

echo "🔄 Restaurando desde Git..."
git checkout HEAD -- "$FILE"

if [ $? -eq 0 ]; then
    echo "✅ Archivo restaurado desde Git"
    
    # Verificar sintaxis
    echo "🔍 Verificando sintaxis..."
    python3 -c "
import ast
try:
    with open('$FILE', 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print('✅ Sintaxis correcta')
except SyntaxError as e:
    print(f'❌ Error de sintaxis: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  Error: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo "🔄 Reiniciando servidor..."
        touch /var/www/www_egarage_cl_wsgi.py
        echo "✅ Servidor reiniciado"
        echo ""
        echo "💡 El archivo ha sido restaurado. La ruta cl/egarage/ se puede agregar después."
    else
        echo "❌ El archivo restaurado tiene errores de sintaxis"
    fi
else
    echo "❌ Error al restaurar desde Git"
    echo "💡 Intentando restaurar desde backup más reciente..."
    BACKUP=$(ls -t "$FILE".backup_* 2>/dev/null | grep -v "final" | head -1)
    if [ -n "$BACKUP" ]; then
        echo "📋 Restaurando desde: $BACKUP"
        cp "$BACKUP" "$FILE"
        touch /var/www/www_egarage_cl_wsgi.py
        echo "✅ Restaurado desde backup"
    fi
fi

