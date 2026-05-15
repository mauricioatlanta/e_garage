#!/bin/bash
# Script para eliminar específicamente las líneas 839 y 841 con bloques
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_line839_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Eliminando líneas 839 y 841 con bloques..."

python3 << 'PYEOF'
file_path = "templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar si tiene {% extends %}
has_extends = any('{% extends' in line for line in lines)

new_lines = []
removed_lines = []

for i, line in enumerate(lines, 1):
    # Si no tiene extends, eliminar TODOS los bloques
    if not has_extends:
        if '{% block' in line or '{% endblock' in line:
            removed_lines.append((i, line.strip()[:60]))
            continue
    
    # Si tiene extends pero estamos en las líneas problemáticas (839, 841)
    # y hay un endblock sin block correspondiente, eliminarlo
    if has_extends and i == 839 and '{% endblock' in line:
        # Verificar si hay un block antes
        block_found = False
        for j in range(i-1, max(0, i-100), -1):
            if '{% block' in lines[j-1]:
                block_found = True
                break
        if not block_found:
            removed_lines.append((i, line.strip()[:60]))
            continue
    
    new_lines.append(line)

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

if removed_lines:
    print(f"✅ Eliminadas {len(removed_lines)} líneas con bloques:")
    for line_num, content in removed_lines:
        print(f"   Línea {line_num}: {content}")
else:
    print("✅ No se encontraron bloques problemáticos")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

