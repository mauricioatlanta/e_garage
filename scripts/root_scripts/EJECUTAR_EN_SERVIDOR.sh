#!/bin/bash
# Script para corregir el error de indentación en views.py
# Ejecutar en el servidor: cd /home/atlantareciclajes/apps/egarage/current && bash EJECUTAR_EN_SERVIDOR.sh

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "📋 Creando backup..."
cp taller/documentos/views.py taller/documentos/views.py.backup_indent_$(date +%Y%m%d_%H%M%S)

echo "🔧 Corrigiendo indentación..."

python3 << 'PYEOF'
import sys

file_path = "taller/documentos/views.py"

# Leer archivo
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la línea con el cierre del f-string
target_idx = None
for i, line in enumerate(lines):
    if '¡Gracias por confiar en nuestros servicios!"""' in line:
        target_idx = i
        break

if target_idx is None:
    print("❌ No se encontró la línea de cierre del f-string")
    sys.exit(1)

print(f"📍 Línea de cierre encontrada en línea {target_idx + 1}")

# Determinar indentación correcta (4 espacios dentro del try block)
base_indent = 4

# Corregir las siguientes 20 líneas (para cubrir el bloque completo)
fixed = False
for i in range(target_idx + 1, min(target_idx + 21, len(lines))):
    line = lines[i]
    stripped = line.lstrip()
    
    # Saltar líneas vacías (mantenerlas como están)
    if not stripped:
        continue
    
    # Reemplazar tabs con espacios primero
    if '\t' in line:
        line = line.replace('\t', '    ')
        lines[i] = line
        fixed = True
    
    # Para líneas de código (no comentarios), deben tener base_indent espacios
    if stripped and not stripped.startswith('#'):
        current_indent = len(line) - len(stripped)
        # Si la indentación es incorrecta (muy diferente de base_indent)
        if abs(current_indent - base_indent) > 1:
            print(f"🔧 Corrigiendo línea {i+1}: indentación {current_indent} -> {base_indent}")
            lines[i] = ' ' * base_indent + stripped
            fixed = True
    elif stripped.startswith('#'):
        # Los comentarios también deben tener indentación correcta
        current_indent = len(line) - len(stripped)
        if current_indent < base_indent:
            print(f"🔧 Corrigiendo línea {i+1} (comentario): indentación {current_indent} -> {base_indent}")
            lines[i] = ' ' * base_indent + stripped
            fixed = True

if fixed:
    # Escribir archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Verificar sintaxis
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, file_path, 'exec')
        print("✅ Archivo corregido y sintaxis válida")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
        sys.exit(1)
else:
    print("⚠️  No se encontraron problemas de indentación")
PYEOF

echo ""
echo "✅ Proceso completado"
