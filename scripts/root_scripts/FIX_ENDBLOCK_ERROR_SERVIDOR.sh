#!/bin/bash
# Script para corregir el error de {% endblock %} sin {% block %}
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_endblock_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo error de endblock..."

python3 << 'PYEOF'
import re

file_path = "templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar y eliminar {% endblock %} que no tienen {% block %} correspondiente
# Primero, verificar si el archivo extiende algo
has_extends = False
block_stack = []
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    line_num = i + 1
    
    # Verificar si tiene {% extends %}
    if '{% extends' in line:
        has_extends = True
        new_lines.append(line)
        i += 1
        continue
    
    # Si no tiene extends, no debería tener bloques
    if not has_extends:
        # Si encontramos un {% endblock %} sin extends, lo eliminamos
        if '{% endblock' in line and not has_extends:
            print(f"⚠️  Eliminando {% endblock %} en línea {line_num} (no hay {% extends %})")
            i += 1
            continue
        # Si encontramos un {% block %}, también lo eliminamos si no hay extends
        if '{% block' in line and not has_extends:
            print(f"⚠️  Eliminando {% block %} en línea {line_num} (no hay {% extends %})")
            i += 1
            continue
    
    # Si tiene extends, manejar bloques correctamente
    if has_extends:
        if '{% block' in line:
            block_name = re.search(r'{% block\s+(\w+)', line)
            if block_name:
                block_stack.append(block_name.group(1))
                new_lines.append(line)
            else:
                new_lines.append(line)
        elif '{% endblock' in line:
            if block_stack:
                block_stack.pop()
                new_lines.append(line)
            else:
                print(f"⚠️  Eliminando {% endblock %} sin {% block %} correspondiente en línea {line_num}")
                # No agregar esta línea
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)
    
    i += 1

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Error de endblock corregido")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

