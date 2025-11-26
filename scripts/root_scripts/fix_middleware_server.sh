#!/bin/bash
# Script para eliminar AccountMiddleware del servidor si no existe

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"

cd "$RELEASE_DIR" || exit 1

echo "🔍 Verificando si AccountMiddleware existe..."

# Verificar si el middleware existe en el entorno del servidor
python3 << 'PYEOF'
import sys
import os

# Intentar encontrar el path de allauth
try:
    import allauth
    allauth_path = os.path.dirname(allauth.__file__)
    middleware_file = os.path.join(allauth_path, "account", "middleware.py")
    
    if os.path.exists(middleware_file):
        with open(middleware_file, "r", encoding="utf-8") as f:
            content = f.read()
            if "class AccountMiddleware" in content:
                print("✅ AccountMiddleware existe en el servidor")
                sys.exit(0)
            else:
                print("⚠️  Archivo existe pero no contiene AccountMiddleware")
                sys.exit(1)
    else:
        print("❌ AccountMiddleware NO existe en el servidor")
        sys.exit(1)
except ImportError:
    print("❌ No se puede importar allauth")
    sys.exit(1)
PYEOF

MIDDLEWARE_EXISTS=$?

if [ $MIDDLEWARE_EXISTS -ne 0 ]; then
    echo "🔧 Eliminando AccountMiddleware de los archivos de settings..."
    
    # Archivos a verificar
    FILES=(
        "gestion_taller/settings.py"
        "gestion_taller/settings/base.py"
        "gestion_taller/compacto/settings.py"
    )
    
    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "Verificando $file..."
            
            # Verificar si el archivo tiene el middleware agregado directamente (sin verificación)
            if grep -q '"allauth.account.middleware.AccountMiddleware"' "$file"; then
                # Verificar si está dentro de un bloque try/except
                python3 << PYEOF
import re

file_path = "$file"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar líneas que agreguen el middleware directamente sin verificación
new_lines = []
in_try_block = False
try_start = -1

for i, line in enumerate(lines):
    # Detectar inicio de bloque try para AccountMiddleware
    if 'Agregar AccountMiddleware' in line or 'verificar que contiene AccountMiddleware' in line:
        in_try_block = True
        try_start = i
        new_lines.append(line)
    elif in_try_block:
        if 'except' in line or ('pass' in line and i > try_start + 3):
            in_try_block = False
            new_lines.append(line)
        else:
            new_lines.append(line)
    # Si encontramos el middleware agregado directamente (sin try/except), eliminarlo
    elif '"allauth.account.middleware.AccountMiddleware"' in line:
        # Verificar si las líneas anteriores tienen try/except
        has_try = False
        for j in range(max(0, i-10), i):
            if 'try:' in lines[j] or 'Agregar AccountMiddleware' in lines[j]:
                has_try = True
                break
        
        if not has_try:
            print(f"Eliminando línea {i+1} de $file: {line.strip()}")
            continue
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✅ $file procesado")
PYEOF
            fi
        fi
    done
    
    echo "✅ Archivos corregidos"
else
    echo "✅ AccountMiddleware existe, no se necesita corrección"
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
echo "✅ Servidor reiniciado"



