#!/bin/bash
# Script para agregar la ruta faltante cl/egarage/
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_cl_egarage_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Agregando ruta cl/egarage/..."

python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar si ya existe la ruta
has_route = False
for line in lines:
    if 'cl/egarage/' in line and 'RedirectView' in line:
        has_route = True
        break

if has_route:
    print("✅ La ruta cl/egarage/ ya existe")
else:
    print("⚠️  Agregando ruta cl/egarage/...")
    
    # Buscar la línea con cl/centro-operaciones-espacial/
    new_lines = []
    added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Después de cl/centro-operaciones-espacial/, agregar cl/egarage/
        if 'cl/centro-operaciones-espacial/' in line and 'name="cl_centro_operaciones_redirect"' in lines[i+1] if i+1 < len(lines) else False:
            # Agregar la nueva ruta
            new_lines.append('    path(\n')
            new_lines.append('        "cl/egarage/",\n')
            new_lines.append('        RedirectView.as_view(url="/cl/es/egarage/", permanent=False),\n')
            new_lines.append('        name="cl_egarage_redirect",\n')
            new_lines.append('    ),\n')
            added = True
            print("✅ Ruta agregada después de cl/centro-operaciones-espacial/")
    
    if not added:
        # Buscar un lugar alternativo después de otras rutas de cl/
        for i, line in enumerate(lines):
            new_lines.append(line)
            if 'cl/configuracion/tecnicos/' in line and i+3 < len(lines):
                # Agregar después de esta ruta
                new_lines.append('    path(\n')
                new_lines.append('        "cl/egarage/",\n')
                new_lines.append('        RedirectView.as_view(url="/cl/es/egarage/", permanent=False),\n')
                new_lines.append('        name="cl_egarage_redirect",\n')
                new_lines.append('    ),\n')
                added = True
                print("✅ Ruta agregada después de cl/configuracion/tecnicos/")
                break
    
    if added:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("✅ Archivo actualizado")
    else:
        print("⚠️  No se pudo encontrar el lugar para agregar la ruta")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

