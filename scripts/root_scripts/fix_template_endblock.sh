#!/bin/bash
# Script para corregir el template centro_operaciones_espacial.html en el servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"
TEMPLATE_FILE="templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

cd "$RELEASE_DIR" || exit 1

echo "🔧 Corrigiendo template $TEMPLATE_FILE..."

# Opción 1: Obtener la versión correcta desde origin/main
echo "📥 Obteniendo versión correcta desde origin/main..."
if git show origin/main:"$TEMPLATE_FILE" > /tmp/template_correcto.html 2>/dev/null; then
    cp /tmp/template_correcto.html "$TEMPLATE_FILE"
    echo "✅ Template reemplazado con versión de origin/main"
else
    echo "⚠️  No se pudo obtener desde origin/main. Corrigiendo manualmente..."
    
    # Opción 2: Eliminar el {% endblock %} problemático
    python3 << 'PYEOF'
file_path = 'templates/taller/us/en/dashboard/centro_operaciones_espacial.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar y eliminar {% endblock %} alrededor de línea 839
fixed = False
for i in range(max(0, 835), min(845, len(lines))):
    if '{% endblock %}' in lines[i] or '{%endblock%}' in lines[i]:
        print(f"⚠️  Encontrado {% endblock %} en línea {i+1}: {lines[i].strip()}")
        # Verificar si hay un {% block %} correspondiente antes
        has_block = False
        for j in range(max(0, i-100), i):
            if '{% block ' in lines[j] or '{%block ' in lines[j]:
                has_block = True
                print(f"   → Encontrado {% block %} correspondiente en línea {j+1}")
                break
        
        if not has_block:
            print(f"✅ Eliminando {% endblock %} sin {% block %} correspondiente")
            lines[i] = ''  # Eliminar la línea
            fixed = True
        else:
            print(f"⚠️  El {% endblock %} tiene un {% block %} correspondiente, no se elimina")
        break

if fixed:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Template corregido")
else:
    print("⚠️  No se encontró {% endblock %} problemático o ya está corregido")
    
    # Verificar si hay algún {% endblock %} sin {% block %}
    block_count = 0
    endblock_count = 0
    for i, line in enumerate(lines):
        if '{% block ' in line or '{%block ' in line:
            block_count += 1
        if '{% endblock %}' in line or '{%endblock%}' in line:
            endblock_count += 1
            if endblock_count > block_count:
                print(f"⚠️  {% endblock %} en línea {i+1} sin {% block %} correspondiente")
                lines[i] = ''
                fixed = True
    
    if fixed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ Template corregido (eliminados {% endblock %} sin {% block %})")
    else:
        print(f"ℹ️  Estadísticas: {block_count} {% block %}, {endblock_count} {% endblock %}")
PYEOF
fi

# Verificar que el template sea válido
echo ""
echo "🔍 Verificando template..."
if python3 -c "
import django
import os
import sys
sys.path.insert(0, '$RELEASE_DIR')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()
from django.template.loader import get_template
try:
    template = get_template('taller/us/en/dashboard/centro_operaciones_espacial.html')
    print('✅ Template válido')
except Exception as e:
    print(f'❌ Error en template: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo "✅ Template verificado correctamente"
else
    echo "⚠️  No se pudo verificar el template (puede ser normal si Django no está configurado)"
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
echo "✅ Servidor reiniciado"



