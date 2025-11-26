#!/bin/bash
# Script simple: corregir línea 1231 directamente con sed

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo línea 1231 directamente..."

# Backup
cp taller/documentos/views.py taller/documentos/views.py.backup_$(date +%Y%m%d_%H%M%S)

# Usar Python para corregir la indentación de la línea 1231
python3 << 'PYEOF'
file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Línea 1231 (índice 1230)
target_line = 1230

if target_line >= len(lines):
    print(f"❌ Línea 1231 no existe (archivo tiene {len(lines)} líneas)")
    sys.exit(1)

print(f"📍 Línea 1231 actual: {repr(lines[target_line])}")

# Buscar la función para obtener indentación correcta
func_start = None
for i in range(target_line, -1, -1):
    if 'def enviar_documento_whatsapp' in lines[i]:
        func_start = i
        break

if func_start is None:
    print("❌ No se encontró la función")
    sys.exit(1)

func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
correct_indent = func_indent + 4

print(f"   Indentación de función: {func_indent}")
print(f"   Indentación correcta: {correct_indent}")

# Corregir la línea 1231
line = lines[target_line]
stripped = line.lstrip()
current_indent = len(line) - len(stripped)

print(f"   Indentación actual línea 1231: {current_indent}")

if current_indent != correct_indent:
    lines[target_line] = ' ' * correct_indent + stripped
    if not lines[target_line].endswith('\n'):
        lines[target_line] += '\n'
    print(f"   ✅ Corregida a {correct_indent} espacios")
    
    # También corregir líneas siguientes si están relacionadas
    for i in range(target_line + 1, min(target_line + 10, len(lines))):
        next_line = lines[i]
        next_stripped = next_line.lstrip()
        
        if not next_stripped:
            continue
        
        next_indent = len(next_line) - len(next_stripped)
        
        # Si la siguiente línea está mal indentada y es parte del JsonResponse
        if next_indent < func_indent + 4 and ('{' in next_stripped or '}' in next_stripped or '"' in next_stripped):
            # Debería tener correct_indent + 4 (dentro del JsonResponse)
            expected_indent = correct_indent + 4
            if next_indent != expected_indent:
                lines[i] = ' ' * expected_indent + next_stripped
                if not lines[i].endswith('\n'):
                    lines[i] += '\n'
                print(f"   🔧 Línea {i+1}: también corregida")
        
        # Si encontramos el cierre, parar
        if next_stripped == ')' and i > target_line:
            break
    
    # Guardar
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # Verificar
    import ast
    try:
        content = ''.join(lines)
        ast.parse(content)
        print("✅ Sintaxis verificada correctamente")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        print(f"   Línea {e.lineno}: {e.text}")
        sys.exit(1)
else:
    print("ℹ️  La línea ya tiene la indentación correcta")
PYEOF

echo ""
echo "✅✅✅ Corrección aplicada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



