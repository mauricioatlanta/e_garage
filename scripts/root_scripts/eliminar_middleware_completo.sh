#!/bin/bash
# Script definitivo para eliminar AccountMiddleware del servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"

cd "$RELEASE_DIR" || exit 1

echo "🔧 Eliminando AccountMiddleware completamente..."

# Usar sed para eliminar líneas que contengan AccountMiddleware
for file in gestion_taller/settings.py gestion_taller/settings/base.py gestion_taller/compacto/settings.py; do
    if [ -f "$file" ]; then
        echo "Procesando $file..."
        # Eliminar líneas que contengan AccountMiddleware
        sed -i '/allauth.account.middleware.AccountMiddleware/d' "$file"
        echo "  ✅ Líneas con AccountMiddleware eliminadas"
    fi
done

# Ahora eliminar bloques try/except relacionados usando Python
python3 << 'PYEOF'
import os
import re

files = [
    "gestion_taller/settings.py",
    "gestion_taller/settings/base.py",
    "gestion_taller/compacto/settings.py"
]

for file_path in files:
    if not os.path.exists(file_path):
        continue
    
    print(f"\n📄 Procesando {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Eliminar bloques completos que intentan agregar AccountMiddleware
    # Patrón: desde "# Agregar AccountMiddleware" hasta el "pass" del except
    pattern = r'# Agregar AccountMiddleware.*?except.*?pass\n'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # También eliminar cualquier línea que mencione AccountMiddleware en comentarios relacionados
    lines = content.split('\n')
    new_lines = []
    skip_block = False
    
    for i, line in enumerate(lines):
        # Detectar inicio de bloque relacionado con AccountMiddleware
        if 'AccountMiddleware' in line and ('# Agregar' in line or 'verificar' in line.lower()):
            skip_block = True
            continue
        
        # Si estamos en un bloque, buscar el final (except/pass)
        if skip_block:
            if 'except' in line or ('pass' in line and i > 0 and 'except' in '\n'.join(lines[max(0, i-3):i])):
                skip_block = False
            continue
        
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    if new_content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ {file_path} limpiado")
    else:
        print(f"  ℹ️  {file_path} no necesita limpieza")

print("\n✅ Proceso completado")
PYEOF

# Verificar que no queden referencias
echo ""
echo "🔍 Verificando que no queden referencias..."
grep -n "AccountMiddleware" gestion_taller/settings.py gestion_taller/settings/base.py gestion_taller/compacto/settings.py 2>/dev/null || echo "✅ No se encontraron referencias a AccountMiddleware"

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_digitalocean_com_wsgi.py
echo "✅ Servidor reiniciado"



