#!/bin/bash
# Script para aplicar cambios en export_utils.py sin necesidad de guardar manualmente

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
from pathlib import Path
import re

file_path = 'taller/utils/export_utils.py'

print(f"📝 Aplicando cambios en {file_path}...\n")

if not Path(file_path).exists():
    print(f"❌ Error: {file_path} no existe")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Corregir relaciones de repuestos
if 'self.documento.repuestos.all()' in content:
    content = content.replace(
        'self.documento.repuestos.all()',
        'self.documento.lineas_repuesto.all()'
    )
    changes_made.append("✅ Relación repuestos corregida (repuestos → lineas_repuesto)")

# 2. Corregir relaciones de servicios
if 'self.documento.servicios.all()' in content:
    content = content.replace(
        'self.documento.servicios.all()',
        'self.documento.lineas_servicio.all()'
    )
    changes_made.append("✅ Relación servicios corregida (servicios → lineas_servicio)")

# 3. Corregir relaciones de otros_servicios
if 'self.documento.otros_servicios.all()' in content:
    content = content.replace(
        'self.documento.otros_servicios.all()',
        'self.documento.lineas_otro_servicio.all()'
    )
    changes_made.append("✅ Relación otros_servicios corregida (otros_servicios → lineas_otro_servicio)")

# También corregir en otras partes del archivo si existen
if 'doc.repuestos.all()' in content:
    content = content.replace('doc.repuestos.all()', 'doc.lineas_repuesto.all()')
    changes_made.append("✅ Relación doc.repuestos corregida")

if 'doc.servicios.all()' in content:
    content = content.replace('doc.servicios.all()', 'doc.lineas_servicio.all()')
    changes_made.append("✅ Relación doc.servicios corregida")

if 'doc.otros_servicios.all()' in content:
    content = content.replace('doc.otros_servicios.all()', 'doc.lineas_otro_servicio.all()')
    changes_made.append("✅ Relación doc.otros_servicios corregida")

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

