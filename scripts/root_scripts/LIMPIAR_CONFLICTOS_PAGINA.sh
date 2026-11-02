#!/bin/bash
# Script para limpiar conflictos de merge en templates y archivos estáticos
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🔍 Buscando conflictos en templates y archivos estáticos..."

# Buscar archivos con marcadores de conflicto
CONFLICT_FILES=$(find . -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) \
    -exec grep -l "^<<<<<<<\|^=======\|^>>>>>>>" {} \; 2>/dev/null | grep -v ".git" | head -30)

if [ -z "$CONFLICT_FILES" ]; then
    echo "✅ No se encontraron conflictos en templates/estáticos"
else
    echo "⚠️  Archivos con conflictos encontrados:"
    echo "$CONFLICT_FILES"
    echo ""
    
    # Crear backup
    BACKUP_DIR="backup_conflictos_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    for file in $CONFLICT_FILES; do
        echo "🔧 Limpiando conflicto en: $file"
        
        # Crear backup
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$file" "$BACKUP_DIR/$file"
        
        # Eliminar marcadores de conflicto
        sed -i '/^<<<<<<< Updated upstream$/d; /^=======$/d; /^>>>>>>> Stashed changes$/d' "$file"
        sed -i '/^<<<<<<< HEAD$/d; /^=======$/d; /^>>>>>>> .*$/d' "$file"
        sed -i '/^<<<<<<<$/d; /^=======$/d; /^>>>>>>>$/d' "$file"
        
        # Verificar que se eliminaron
        if grep -q "^<<<<<<<\|^=======\|^>>>>>>>" "$file" 2>/dev/null; then
            echo "⚠️  Aún hay conflictos en $file, limpiando más agresivamente..."
            # Eliminar líneas que contengan estos marcadores en cualquier parte
            sed -i '/<<<<<<</d; /=======/d; />>>>>>>/d' "$file"
        fi
        
        echo "✅ $file limpiado"
    done
    
    echo ""
    echo "📋 Backups guardados en: $BACKUP_DIR"
fi

# Verificar específicamente templates/public/selector_pais.html
if [ -f "templates/public/selector_pais.html" ]; then
    echo ""
    echo "🔍 Verificando templates/public/selector_pais.html..."
    if grep -q "^<<<<<<<\|^=======\|^>>>>>>>" "templates/public/selector_pais.html" 2>/dev/null; then
        echo "⚠️  Conflicto encontrado en selector_pais.html"
        cp "templates/public/selector_pais.html" "templates/public/selector_pais.html.backup"
        sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' "templates/public/selector_pais.html"
        sed -i '/<<<<<<</d; /=======/d; />>>>>>>/d' "templates/public/selector_pais.html"
        echo "✅ selector_pais.html limpiado"
    else
        echo "✅ selector_pais.html sin conflictos"
    fi
fi

# Verificar archivos CSS
echo ""
echo "🔍 Verificando archivos CSS..."
CSS_CONFLICTS=$(find static -name "*.css" -exec grep -l "^<<<<<<<\|^=======\|^>>>>>>>" {} \; 2>/dev/null | head -10)

if [ -z "$CSS_CONFLICTS" ]; then
    echo "✅ No se encontraron conflictos en CSS"
else
    echo "⚠️  Archivos CSS con conflictos:"
    echo "$CSS_CONFLICTS"
    for css_file in $CSS_CONFLICTS; do
        echo "🔧 Limpiando: $css_file"
        cp "$css_file" "$css_file.backup"
        sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' "$css_file"
        sed -i '/<<<<<<</d; /=======/d; />>>>>>>/d' "$css_file"
        echo "✅ $css_file limpiado"
    done
fi

echo ""
echo "🔍 Verificación final..."
REMAINING=$(find . -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) \
    -exec grep -l "^<<<<<<<\|^=======\|^>>>>>>>" {} \; 2>/dev/null | grep -v ".git" | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "✅ Todos los conflictos en templates/estáticos resueltos"
else
    echo "⚠️  Aún quedan $REMAINING archivos con conflictos:"
    find . -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) \
        -exec grep -l "^<<<<<<<\|^=======\|^>>>>>>>" {} \; 2>/dev/null | grep -v ".git"
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

