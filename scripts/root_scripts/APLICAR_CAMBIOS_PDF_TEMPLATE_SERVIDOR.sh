#!/bin/bash
# Script para aplicar cambios en pdf_template.html sin necesidad de guardar manualmente

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
from pathlib import Path
import re

file_path = 'templates/taller/documentos/pdf_template.html'

print(f"📝 Aplicando cambios en {file_path}...\n")

if not Path(file_path).exists():
    print(f"❌ Error: {file_path} no existe")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Corregir nombre_servicio a nombre
if 'servicio.nombre_servicio' in content:
    content = content.replace('servicio.nombre_servicio', 'servicio.nombre')
    changes_made.append("✅ Campo nombre_servicio corregido a nombre")

# 2. Verificar que los totales estén después de Servicios Subcontratados
# Buscar la sección de otros_servicios y verificar que los totales vengan después
idx_otros_end = content.find('{% endif %}', content.find('Servicios Subcontratados'))
idx_totales = content.find('<!-- TOTALES AL PIE -->')

if idx_totales == -1:
    # Los totales no están en el lugar correcto, necesitamos moverlos
    # Buscar donde están actualmente los totales (si existen)
    totales_pattern = r'(<!-- TOTALES AL PIE -->.*?</div>\s*{% endif %}\s*</div>)'
    match = re.search(totales_pattern, content, re.DOTALL)
    
    if match:
        # Los totales están en otro lugar, necesitamos moverlos
        print("⚠️  Los totales necesitan ser reorganizados manualmente")
    else:
        # Verificar si ya están en el lugar correcto (después de otros_servicios)
        if '<!-- TOTALES AL PIE -->' in content and idx_otros_end < idx_totales:
            changes_made.append("✅ Los totales ya están después de Servicios Subcontratados")
        else:
            print("⚠️  Verificar manualmente la posición de los totales")
else:
    if idx_otros_end < idx_totales:
        changes_made.append("✅ Los totales están correctamente posicionados")
    else:
        print("⚠️  Los totales necesitan ser movidos después de Servicios Subcontratados")

# Guardar el archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

if changes_made:
    print("\n".join(changes_made))
    print(f"\n✅ Archivo {file_path} actualizado correctamente")
else:
    print("ℹ️  No se encontraron cambios necesarios (puede que ya estén aplicados)")

PYEOF

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"
echo ""
echo "🎉 ¡Cambios aplicados exitosamente!"

