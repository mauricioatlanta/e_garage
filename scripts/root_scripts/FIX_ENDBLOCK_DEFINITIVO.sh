#!/bin/bash
# Script DEFINITIVO para eliminar TODOS los bloques problemáticos
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_definitivo_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Eliminando TODOS los bloques problemáticos..."

python3 << 'PYEOF'
import re

file_path = "templates/taller/us/en/dashboard/centro_operaciones_espacial.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si tiene {% extends %}
has_extends = '{% extends' in content

# Contar bloques antes
block_count = len(re.findall(r'{%\s*block\s+', content))
endblock_count = len(re.findall(r'{%\s*endblock', content))

print(f"📊 Estado inicial:")
print(f"   ¿Tiene {% extends %}? {has_extends}")
print(f"   Bloques encontrados: {block_count}")
print(f"   Endblocks encontrados: {endblock_count}")

# Si no tiene extends, eliminar TODOS los bloques
if not has_extends:
    print("\n⚠️  No tiene {% extends %}, eliminando TODOS los bloques...")
    
    # Eliminar todas las líneas con {% block %} o {% endblock %}
    lines = content.splitlines(keepends=True)
    new_lines = []
    removed = 0
    
    for i, line in enumerate(lines, 1):
        if '{% block' in line or '{% endblock' in line:
            print(f"   Eliminando línea {i}: {line.strip()[:60]}")
            removed += 1
            continue
        new_lines.append(line)
    
    content = ''.join(new_lines)
    print(f"✅ Eliminadas {removed} líneas con bloques")
else:
    print("\n⚠️  Tiene {% extends %}, verificando balance de bloques...")
    
    # Si tiene extends pero los bloques están desbalanceados, eliminarlos todos
    if block_count != endblock_count:
        print(f"   Bloques desbalanceados ({block_count} blocks vs {endblock_count} endblocks)")
        print("   Eliminando TODOS los bloques para evitar errores...")
        
        lines = content.splitlines(keepends=True)
        new_lines = []
        removed = 0
        
        for i, line in enumerate(lines, 1):
            if '{% block' in line or '{% endblock' in line:
                print(f"   Eliminando línea {i}: {line.strip()[:60]}")
                removed += 1
                continue
            new_lines.append(line)
        
        content = ''.join(new_lines)
        print(f"✅ Eliminadas {removed} líneas con bloques desbalanceados")

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Verificar resultado
final_block_count = len(re.findall(r'{%\s*block\s+', content))
final_endblock_count = len(re.findall(r'{%\s*endblock', content))

print(f"\n📊 Estado final:")
print(f"   Bloques restantes: {final_block_count}")
print(f"   Endblocks restantes: {final_endblock_count}")

if final_block_count == 0 and final_endblock_count == 0:
    print("✅ Archivo corregido: sin bloques problemáticos")
else:
    print("⚠️  Aún quedan bloques en el archivo")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

