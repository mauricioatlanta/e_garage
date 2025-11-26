#!/bin/bash
# Script para eliminar directamente AccountMiddleware de MIDDLEWARE en el servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"

cd "$RELEASE_DIR" || exit 1

echo "🔧 Eliminando AccountMiddleware de MIDDLEWARE..."

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
        lines = content.split('\n')
    
    new_lines = []
    modified = False
    in_middleware_list = False
    middleware_found = False
    
    for i, line in enumerate(lines):
        # Detectar inicio de lista MIDDLEWARE
        if 'MIDDLEWARE = [' in line or 'MIDDLEWARE=[' in line:
            in_middleware_list = True
            new_lines.append(line)
            continue
        
        # Detectar fin de lista MIDDLEWARE
        if in_middleware_list and line.strip() == ']':
            # Si encontramos el middleware, no agregarlo
            if not middleware_found:
                new_lines.append(line)
            in_middleware_list = False
            continue
        
        # Si estamos en la lista MIDDLEWARE y encontramos AccountMiddleware
        if in_middleware_list and 'allauth.account.middleware.AccountMiddleware' in line:
            print(f"  ❌ Eliminando línea {i+1}: {line.strip()}")
            modified = True
            middleware_found = True
            # También eliminar líneas de comentario relacionadas si están justo antes
            if i > 0 and ('AccountMiddleware' in lines[i-1] or 'allauth' in lines[i-1].lower()):
                if new_lines and ('AccountMiddleware' in new_lines[-1] or 'allauth' in new_lines[-1].lower()):
                    removed = new_lines.pop()
                    print(f"  ❌ También eliminando línea anterior: {removed.strip()}")
            continue
        
        new_lines.append(line)
    
    # También eliminar bloques try/except que intentan agregar el middleware
    # si el middleware no existe en el servidor
    final_lines = []
    i = 0
    while i < len(new_lines):
        line = new_lines[i]
        
        # Detectar bloque try que agrega AccountMiddleware
        if 'Agregar AccountMiddleware' in line or ('try:' in line and i + 5 < len(new_lines) and 'AccountMiddleware' in '\n'.join(new_lines[i:i+10])):
            # Encontrar el bloque completo try/except
            try_start = i
            try_end = i
            indent_level = len(line) - len(line.lstrip())
            
            # Buscar el except correspondiente
            j = i + 1
            while j < len(new_lines):
                current_line = new_lines[j]
                current_indent = len(current_line) - len(current_line.lstrip())
                
                if 'except' in current_line and current_indent == indent_level:
                    try_end = j
                    # Buscar el pass o el cierre del except
                    k = j + 1
                    while k < len(new_lines) and k < j + 3:
                        if 'pass' in new_lines[k] and len(new_lines[k]) - len(new_lines[k].lstrip()) == indent_level:
                            try_end = k
                            break
                        k += 1
                    break
                j += 1
            
            # Si el bloque intenta agregar AccountMiddleware, eliminarlo
            block_content = '\n'.join(new_lines[try_start:try_end+1])
            if 'AccountMiddleware' in block_content:
                print(f"  ❌ Eliminando bloque try/except (líneas {try_start+1}-{try_end+1})")
                modified = True
                i = try_end + 1
                continue
        
        final_lines.append(line)
        i += 1
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_lines))
        print(f"  ✅ {file_path} corregido")
    else:
        print(f"  ℹ️  {file_path} no necesita corrección")

print("\n✅ Proceso completado")
PYEOF

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
echo "✅ Servidor reiniciado"



