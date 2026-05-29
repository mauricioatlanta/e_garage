#!/bin/bash
# Script para eliminar TODOS los bloques si no hay {% extends %}
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_allblocks_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Eliminando TODOS los bloques si no hay {% extends %}..."

python3 << 'PYEOF'
file_path = "templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar si tiene {% extends %}
has_extends = False
for line in lines:
    if '{% extends' in line:
        has_extends = True
        break

new_lines = []
removed_count = 0

for i, line in enumerate(lines, 1):
    # Si no tiene extends, eliminar TODOS los bloques
    if not has_extends:
        if '{% block' in line or '{% endblock' in line:
            print(f"⚠️  Eliminando línea {i}: {line.strip()[:70]}")
            removed_count += 1
            continue
    
    new_lines.append(line)

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

if removed_count > 0:
    print(f"✅ Eliminadas {removed_count} líneas con bloques")
else:
    print("✅ Archivo no tiene bloques problemáticos")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

