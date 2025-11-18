#!/bin/bash
# Script para resolver conflictos de merge en el servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"
CURRENT_DIR="/home/atlantareciclajes/apps/egarage/current"

cd "$RELEASE_DIR" || exit 1

echo "🔍 Buscando conflictos de merge..."

# Buscar archivos con marcadores de conflicto
CONFLICT_FILES=$(grep -r -l "<<<<<<< Updated upstream\|=======\|>>>>>>> Stashed changes" . 2>/dev/null | grep -v ".git" | head -20)

if [ -z "$CONFLICT_FILES" ]; then
    echo "✅ No se encontraron conflictos de merge"
else
    echo "⚠️  Archivos con conflictos encontrados:"
    echo "$CONFLICT_FILES"
    echo ""
    
    for file in $CONFLICT_FILES; do
        echo "🔧 Resolviendo conflicto en: $file"
        
        # Resolver conflicto aceptando la versión remota (theirs)
        # Primero, verificar si el archivo existe en origin/main
        if git show origin/main:"$file" > /tmp/resolved_file 2>/dev/null; then
            cp /tmp/resolved_file "$file"
            echo "✅ $file resuelto usando versión de origin/main"
        else
            # Si no existe en origin/main, usar la versión local (ours)
            git checkout --ours "$file" 2>/dev/null
            echo "✅ $file resuelto usando versión local"
        fi
        
        # Verificar que no queden marcadores de conflicto
        if grep -q "<<<<<<< Updated upstream\|=======\|>>>>>>> Stashed changes" "$file" 2>/dev/null; then
            echo "⚠️  Aún hay conflictos en $file, limpiando manualmente..."
            # Eliminar líneas de conflicto manualmente
            sed -i '/^<<<<<<< Updated upstream$/d; /^=======$/d; /^>>>>>>> Stashed changes$/d' "$file"
        fi
    done
fi

# Verificar específicamente taller/documentos/views.py
if [ -f "taller/documentos/views.py" ]; then
    echo ""
    echo "🔍 Verificando taller/documentos/views.py..."
    if grep -q "<<<<<<< Updated upstream\|=======\|>>>>>>> Stashed changes" "taller/documentos/views.py" 2>/dev/null; then
        echo "⚠️  Conflicto encontrado en taller/documentos/views.py"
        
        # Intentar obtener versión de origin/main
        if git show origin/main:taller/documentos/views.py > /tmp/views_resolved.py 2>/dev/null; then
            cp /tmp/views_resolved.py "taller/documentos/views.py"
            echo "✅ taller/documentos/views.py resuelto usando versión de origin/main"
        else
            # Limpiar marcadores de conflicto
            sed -i '/^<<<<<<< Updated upstream$/d; /^=======$/d; /^>>>>>>> Stashed changes$/d' "taller/documentos/views.py"
            echo "✅ Marcadores de conflicto eliminados de taller/documentos/views.py"
        fi
    else
        echo "✅ taller/documentos/views.py sin conflictos"
    fi
fi

echo ""
echo "🔍 Verificación final..."
REMAINING_CONFLICTS=$(grep -r -l "<<<<<<< Updated upstream\|=======\|>>>>>>> Stashed changes" . 2>/dev/null | grep -v ".git" | wc -l)

if [ "$REMAINING_CONFLICTS" -eq 0 ]; then
    echo "✅ Todos los conflictos resueltos"
else
    echo "⚠️  Aún quedan $REMAINING_CONFLICTS archivos con conflictos"
    grep -r -l "<<<<<<< Updated upstream\|=======\|>>>>>>> Stashed changes" . 2>/dev/null | grep -v ".git"
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
echo "✅ Servidor reiniciado"

