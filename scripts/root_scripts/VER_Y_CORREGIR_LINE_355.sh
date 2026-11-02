#!/bin/bash
# Script para ver y corregir específicamente la línea 355
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_ver355_$(date +%Y%m%d_%H%M%S)"

echo "🔍 Mostrando líneas 350-365 del servidor..."
sed -n '350,365p' "$FILE"

echo ""
echo "🔧 Corrigiendo problema..."

python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

# Mostrar el path() completo alrededor de línea 355
print("📋 Path() completo alrededor de línea 355:")
start = max(0, 350 - 5)
end = min(len(lines), 365 + 5)

for i in range(start, end):
    marker = ">>>" if 350 <= i+1 <= 365 else "   "
    print(f"{marker} {i+1:3d}: {lines[i].rstrip()}")

# Buscar el path() que comienza antes de línea 355
# El problema es que path() espera: path("url", view, name="name")
# Pero puede tener: path("url", view, otra_cosa, name="name")

# Buscar todos los path() y verificar su estructura
import re

# Encontrar el path() que incluye la línea 355
path_pattern = r'path\s*\(\s*"[^"]+"\s*,\s*([^,)]+)\s*,\s*([^,)]+)\s*,\s*name\s*='
matches = list(re.finditer(path_pattern, content))

for match in matches:
    # Calcular en qué línea está
    line_num = content[:match.start()].count('\n') + 1
    if 350 <= line_num <= 365:
        print(f"\n⚠️  Problema encontrado en línea {line_num}")
        print(f"   View: {match.group(1)}")
        print(f"   Argumento extra: {match.group(2)}")
        
        # Corregir: eliminar el argumento extra
        fixed_content = re.sub(
            r'(path\s*\(\s*"[^"]+"\s*,\s*[^,)]+)\s*,\s*([^,)]+)\s*,\s*(?=name\s*=)',
            r'\1, ',
            content,
            count=1
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✅ Archivo corregido")
        break
else:
    # Si no se encontró con regex, buscar manualmente
    print("\n🔍 Buscando problema manualmente...")
    
    # Buscar path() que incluye línea 355
    i = 349  # Línea 350 (0-indexed)
    if i < len(lines):
        # Buscar hacia atrás para encontrar el inicio del path()
        path_start = i
        while path_start > 0 and 'path(' not in lines[path_start]:
            path_start -= 1
        
        if path_start >= 0 and 'path(' in lines[path_start]:
            # Leer el path completo
            path_lines = []
            paren_count = 0
            for j in range(path_start, min(path_start + 15, len(lines))):
                path_lines.append(lines[j])
                paren_count += lines[j].count('(') - lines[j].count(')')
                if '),' in lines[j] and paren_count == 0:
                    break
            
            path_str = ''.join(path_lines)
            print(f"Path encontrado (líneas {path_start+1}-{j+1}):")
            print(path_str)
            
            # Contar comas entre argumentos
            # Debería ser: path("url", view, name="name")
            # Si hay más de 2 comas antes de name=, hay un problema
            before_name = path_str.split('name=')[0] if 'name=' in path_str else path_str
            comma_count = before_name.count(',')
            
            if comma_count > 2:
                print(f"⚠️  Demasiadas comas ({comma_count}) antes de name=")
                # Buscar y eliminar argumentos extra
                # Formato esperado: path("url", view, name="name")
                # Si hay: path("url", view, extra, name="name")
                
                # Buscar el patrón y corregirlo
                fixed = re.sub(
                    r'(path\s*\(\s*"[^"]+"\s*,\s*[^,)]+)\s*,\s*([^,)]+)\s*,\s*(?=name\s*=)',
                    r'\1, ',
                    path_str
                )
                
                # Reemplazar en el archivo
                new_lines = lines[:path_start] + fixed.splitlines(keepends=True) + lines[j+1:]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print("✅ Archivo corregido")

# Verificar sintaxis
import ast
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print("\n✅ Sintaxis correcta")
except SyntaxError as e:
    print(f"\n❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
except Exception as e:
    print(f"\n⚠️  Error al verificar: {e}")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

