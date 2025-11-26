#!/bin/bash
# Script para comentar la línea {% load dal_select2 %} en el template

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo template crear_vehiculo.html..."

# Backup
cp templates/taller/us/en/vehiculos/crear_vehiculo.html templates/taller/us/en/vehiculos/crear_vehiculo.html.backup_$(date +%Y%m%d_%H%M%S)

python3 << 'PYEOF'
import re

file_path = "templates/taller/us/en/vehiculos/crear_vehiculo.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar y comentar la línea {% load dal_select2 %}
modified = False
for i, line in enumerate(lines):
    stripped = line.strip()
    # Buscar líneas que contengan {% load dal_select2 %} sin comentar
    if '{% load dal_select2 %}' in stripped and not stripped.startswith('{#'):
        print(f"📍 Línea {i+1} encontrada: {stripped}")
        # Comentar la línea
        indent = len(line) - len(line.lstrip())
        lines[i] = ' ' * indent + '{# {% load dal_select2 %} #}\n'
        modified = True
        print(f"✅ Línea {i+1} comentada")
    # También buscar si está comentada de otra forma y asegurarse de que esté correctamente comentada
    elif 'dal_select2' in stripped and not stripped.startswith('{#'):
        print(f"📍 Línea {i+1} contiene dal_select2: {stripped}")
        indent = len(line) - len(line.lstrip())
        lines[i] = ' ' * indent + '{# {% load dal_select2 %} #}\n'
        modified = True
        print(f"✅ Línea {i+1} comentada")

if not modified:
    print("ℹ️  No se encontró {% load dal_select2 %} sin comentar")
    # Verificar si ya está comentada
    for i, line in enumerate(lines):
        if 'dal_select2' in line:
            print(f"ℹ️  Línea {i+1} ya contiene dal_select2: {line.strip()[:60]}")

# Guardar archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Archivo guardado correctamente")
PYEOF

echo ""
echo "✅✅✅ Template corregido ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



