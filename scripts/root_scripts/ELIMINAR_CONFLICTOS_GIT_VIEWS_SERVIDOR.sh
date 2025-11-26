#!/bin/bash
# Script para eliminar marcadores de conflicto de Git en views.py

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Eliminando marcadores de conflicto de Git..."

# Backup
cp taller/documentos/views.py taller/documentos/views.py.backup_$(date +%Y%m%d_%H%M%S)

python3 << 'PYEOF'
import sys
import ast

file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar y eliminar marcadores de conflicto
conflict_markers = ['<<<<<<<', '=======', '>>>>>>>']
has_conflicts = False
conflict_lines = []

for i, line in enumerate(lines):
    stripped = line.strip()
    for marker in conflict_markers:
        if marker in stripped:
            has_conflicts = True
            conflict_lines.append((i+1, stripped))
            print(f"📍 Marcador de conflicto encontrado en línea {i+1}: {stripped[:60]}")

if not has_conflicts:
    print("✅ No se encontraron marcadores de conflicto")
    # Verificar sintaxis de todas formas
    try:
        content = ''.join(lines)
        ast.parse(content)
        print("✅ Sintaxis verificada correctamente")
        sys.exit(0)
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        print(f"   Línea {e.lineno}: {e.text}")
        sys.exit(1)

print(f"\n🔧 Eliminando {len(conflict_lines)} marcador(es) de conflicto...")

# Eliminar bloques de conflicto
# Formato típico:
# <<<<<<< Updated upstream
# ... código ...
# =======
# ... código alternativo ...
# >>>>>>> Stashed changes

new_lines = []
i = 0
removed_blocks = 0

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Si encontramos inicio de conflicto (<<<<<<<)
    if stripped.startswith('<<<<<<<'):
        print(f"   🗑️  Eliminando bloque de conflicto desde línea {i+1}")
        start_line = i + 1
        
        # Saltar hasta encontrar =======
        while i < len(lines) and '=======' not in lines[i]:
            i += 1
        
        # Si encontramos =======, saltarlo también
        if i < len(lines) and '=======' in lines[i]:
            i += 1
        
        # Saltar hasta encontrar >>>>>>>
        while i < len(lines) and not lines[i].strip().startswith('>>>>>>>'):
            i += 1
        
        # Saltar la línea con >>>>>>>
        if i < len(lines):
            i += 1
        
        removed_blocks += 1
        print(f"      Bloque eliminado (líneas {start_line} a {i})")
        continue
    
    # Si encontramos ======= o >>>>>>> sueltos (sin <<<<<<< antes), también eliminarlos
    if stripped.startswith('=======') or stripped.startswith('>>>>>>>'):
        print(f"   🗑️  Eliminando marcador suelto en línea {i+1}: {stripped[:40]}")
        i += 1
        continue
    
    new_lines.append(line)
    i += 1

print(f"✅ {removed_blocks} bloque(s) de conflicto eliminado(s)")

# Verificar sintaxis
try:
    content = ''.join(new_lines)
    ast.parse(content)
    print("✅ Sintaxis verificada correctamente después de eliminar conflictos")
except SyntaxError as e:
    print(f"❌ Error de sintaxis después de eliminar conflictos: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Mostrar contexto del error
    error_lines = content.split('\n')
    if e.lineno <= len(error_lines):
        start = max(0, e.lineno - 10)
        end = min(len(error_lines), e.lineno + 10)
        print(f"\n   Contexto alrededor de línea {e.lineno}:")
        for i in range(start, end):
            marker = ">>>" if i == e.lineno - 1 else "   "
            print(f"{marker} {i+1:4d}: {error_lines[i][:80]}")
    
    sys.exit(1)

# Guardar archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Archivo guardado correctamente")
PYEOF

echo ""
echo "✅✅✅ Conflictos eliminados ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
