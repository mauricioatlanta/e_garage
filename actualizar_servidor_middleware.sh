#!/bin/bash
# Script para actualizar el servidor y eliminar AccountMiddleware

echo "🔄 Actualizando código desde Git..."
cd /home/atlantareciclajes/apps/egarage/current || exit 1

# Hacer pull del repositorio
git pull origin main --no-rebase

if [ $? -ne 0 ]; then
    echo "❌ Error al hacer git pull"
    exit 1
fi

echo ""
echo "🔍 Verificando que no queden referencias a AccountMiddleware..."
grep -n "AccountMiddleware" gestion_taller/settings.py gestion_taller/settings/base.py gestion_taller/compacto/settings.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo "⚠️  Aún hay referencias a AccountMiddleware. Eliminándolas..."
    
    # Eliminar cualquier línea que contenga AccountMiddleware
    sed -i '/AccountMiddleware/d' gestion_taller/settings.py
    sed -i '/AccountMiddleware/d' gestion_taller/settings/base.py
    sed -i '/AccountMiddleware/d' gestion_taller/compacto/settings.py
    
    # Eliminar bloques try/except relacionados
    python3 << 'PYEOF'
import re
import os

files = [
    "gestion_taller/settings.py",
    "gestion_taller/settings/base.py",
    "gestion_taller/compacto/settings.py"
]

for file_path in files:
    if not os.path.exists(file_path):
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Eliminar bloques que intentan agregar AccountMiddleware
    pattern = r'# Agregar AccountMiddleware.*?except.*?pass\n'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Eliminar líneas relacionadas
    lines = content.split('\n')
    new_lines = []
    skip = False
    
    for line in lines:
        if 'AccountMiddleware' in line and ('# Agregar' in line or 'verificar' in line.lower() or 'try:' in line):
            skip = True
            continue
        if skip and ('except' in line or 'pass' in line):
            skip = False
            continue
        if not skip:
            new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"✅ {file_path} limpiado")
PYEOF
else
    echo "✅ No se encontraron referencias a AccountMiddleware"
fi

echo ""
echo "🔍 Verificando si AccountMiddleware existe en el servidor..."
# Si el middleware no existe, comentar o eliminar la línea
if ! python3 -c "from allauth.account import middleware; import middleware" 2>/dev/null; then
    echo "  ⚠️  AccountMiddleware no existe, eliminando de MIDDLEWARE..."
    sed -i '/allauth.account.middleware.AccountMiddleware/d' gestion_taller/settings.py
    sed -i '/allauth.account.middleware.AccountMiddleware/d' gestion_taller/settings/base.py
    sed -i '/allauth.account.middleware.AccountMiddleware/d' gestion_taller/compacto/settings.py
    echo "  ✅ Líneas eliminadas"
else
    echo "  ✅ AccountMiddleware existe, se mantiene en MIDDLEWARE"
fi

echo ""
echo "🧹 Limpiando marcadores de conflicto de merge en taller/documentos/views.py..."
FILE="taller/documentos/views.py"
if [ -f "$FILE" ]; then
    # Verificar si hay marcadores de conflicto
    if grep -q "^<<<<<<<" "$FILE" || grep -q "^=======" "$FILE" || grep -q "^>>>>>>>" "$FILE"; then
        echo "  ⚠️  Marcadores de conflicto encontrados"
        
        # Crear backup
        cp "$FILE" "${FILE}.backup"
        echo "  📦 Backup creado"
        
        # Eliminar líneas con marcadores de conflicto
        sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' "$FILE"
        echo "  ✅ Marcadores eliminados"
        
        # Verificar sintaxis
        python3 -m py_compile "$FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ Sintaxis Python válida"
        else
            echo "  ⚠️  Error de sintaxis, restaurando desde Git..."
            git checkout HEAD -- "$FILE" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "  ✅ Archivo restaurado desde Git"
            else
                echo "  ❌ No se pudo restaurar, usando backup..."
                cp "${FILE}.backup" "$FILE"
            fi
        fi
    else
        echo "  ✅ No se encontraron marcadores de conflicto"
    fi
else
    echo "  ⚠️  Archivo no encontrado: $FILE"
fi

echo ""
echo "🔄 Reiniciando servidor WSGI..."
touch /var/www/www_egarage_cl_wsgi.py

echo ""
echo "✅ Proceso completado. El servidor debería estar funcionando ahora."
echo "📋 Verifica los logs si hay algún error."

