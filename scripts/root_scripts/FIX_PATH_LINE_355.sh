#!/bin/bash
# Script para corregir el error en línea 355
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_line355_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo error en línea 355..."

python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Mostrar líneas problemáticas
print("📋 Líneas 350-365:")
for i in range(349, min(365, len(lines))):
    marker = ">>>" if i == 354 else "   "
    print(f"{marker} {i+1:3d}: {lines[i].rstrip()}")

# El error "kwargs argument must be a dict, but got function" significa que
# hay un path() con argumentos en orden incorrecto
# Formato correcto: path("url", view, name="name")
# Formato incorrecto: path("url", view, otra_funcion, name="name")

# Buscar el problema en la línea 355
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Si encontramos un path() cerca de la línea 355
    if 'path(' in line and 350 <= i+1 <= 365:
        # Leer el path completo
        path_lines = [line]
        j = i + 1
        paren_count = line.count('(') - line.count(')')
        
        while j < len(lines) and paren_count > 0 and j < i + 10:
            path_lines.append(lines[j])
            paren_count += lines[j].count('(') - lines[j].count(')')
            if '),' in lines[j] and paren_count == 0:
                break
            j += 1
        
        path_content = ''.join(path_lines)
        
        # Verificar si hay un problema: función después de name=
        import re
        # Buscar: name="..." seguido de algo que no sea ), o espacios
        # O buscar: algo antes de name= que no debería estar
        
        # Patrón problemático: path("url", view, otra_cosa, name="name")
        # Buscar si hay algo entre el view y name=
        problematic = re.search(r'(RedirectView\.as_view\([^)]+\)|TemplateView\.as_view\([^)]+\)|include\([^)]+\)|lambda[^,)]+),?\s*([^,)]+)\s*,\s*name=', path_content)
        
        if problematic:
            print(f"⚠️  Problema encontrado en línea {i+1}")
            print(f"   Argumento problemático: {problematic.group(2)}")
            # Eliminar el argumento problemático
            fixed_content = re.sub(
                r'(RedirectView\.as_view\([^)]+\)|TemplateView\.as_view\([^)]+\)|include\([^)]+\)|lambda[^,)]+),?\s*([^,)]+)\s*,\s*(?=name=)',
                r'\1, ',
                path_content
            )
            # Convertir de vuelta a líneas
            fixed_lines = fixed_content.splitlines(keepends=True)
            new_lines.extend(fixed_lines)
            i = j + 1
            continue
        
        new_lines.extend(path_lines)
        i = j + 1
    else:
        new_lines.append(line)
        i += 1

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# Verificar sintaxis
import ast
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print("✅ Sintaxis correcta")
except SyntaxError as e:
    print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
except Exception as e:
    print(f"⚠️  Error al verificar: {e}")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

