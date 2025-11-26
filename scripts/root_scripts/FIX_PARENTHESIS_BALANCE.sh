#!/bin/bash
# Script para corregir el balance de paréntesis
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_balance_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo balance de paréntesis..."

python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar balance de paréntesis
print("🔍 Verificando balance de paréntesis...")

# Mostrar líneas problemáticas
print("\n📋 Líneas 820-845:")
for i in range(819, min(845, len(lines))):
    marker = ">>>" if i == 820 or i == 842 else "   "
    print(f"{marker} {i+1:3d}: {lines[i].rstrip()}")

# Contar paréntesis y corchetes
paren_count = 0
bracket_count = 0
issues = []

for i, line in enumerate(lines, 1):
    paren_count += line.count('(') - line.count(')')
    bracket_count += line.count('[') - line.count(']')
    
    if paren_count < 0:
        issues.append(f"Línea {i}: Paréntesis de cierre sin apertura")
    if bracket_count < 0:
        issues.append(f"Línea {i}: Corchete de cierre sin apertura")

if issues:
    print("\n⚠️  Problemas encontrados:")
    for issue in issues:
        print(f"   {issue}")

# Buscar el problema específico alrededor de la línea 821
print("\n🔧 Buscando problema específico...")

# Leer el archivo completo para ver el contexto
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar urlpatterns = [
urlpatterns_start = content.find('urlpatterns = [')
if urlpatterns_start > 0:
    # Contar paréntesis y corchetes desde el inicio de urlpatterns
    paren_count = 0
    bracket_count = 0
    
    for i, char in enumerate(content[urlpatterns_start:], start=urlpatterns_start):
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
        elif char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
        
        # Si encontramos el ] final y hay un desbalance
        if char == ']' and bracket_count == 0 and paren_count != 0:
            # Calcular la línea
            line_num = content[:i].count('\n') + 1
            print(f"⚠️  Desbalance encontrado: {paren_count} paréntesis sin cerrar en línea ~{line_num}")
            
            # Buscar el último path() antes del ]
            # Buscar hacia atrás desde la línea 843
            lines_before = content[:i].splitlines()
            if len(lines_before) >= 843:
                # Verificar las últimas líneas antes del ]
                for j in range(len(lines_before)-5, len(lines_before)):
                    if j >= 0 and 'path(' in lines_before[j]:
                        print(f"   Último path() encontrado alrededor de línea {j+1}")

# Corregir: buscar y eliminar paréntesis o corchetes extra
new_lines = []
paren_stack = []
bracket_stack = []

for i, line in enumerate(lines, 1):
    # Si estamos cerca de la línea problemática
    if 820 <= i <= 845:
        # Contar paréntesis y corchetes en esta línea
        line_parens = line.count('(') - line.count(')')
        line_brackets = line.count('[') - line.count(']')
        
        # Si hay un ] sin [ correspondiente antes
        if line_brackets < 0 and len(bracket_stack) == 0:
            print(f"⚠️  Corchete ] sin [ en línea {i}, eliminando...")
            # Eliminar el ]
            line = line.replace(']', '', 1)
            line_brackets += 1
        
        # Si hay un ) sin ( correspondiente antes
        if line_parens < 0 and len(paren_stack) == 0:
            print(f"⚠️  Paréntesis ) sin ( en línea {i}, verificando...")
            # Puede ser parte de un path(), verificar contexto
        
        # Actualizar stacks
        for char in line:
            if char == '(':
                paren_stack.append(i)
            elif char == ')':
                if paren_stack:
                    paren_stack.pop()
            elif char == '[':
                bracket_stack.append(i)
            elif char == ']':
                if bracket_stack:
                    bracket_stack.pop()
    
    new_lines.append(line)

# Verificar si el último ] está balanceado
if bracket_stack:
    print(f"⚠️  Faltan {len(bracket_stack)} corchetes de cierre")
    # Agregar corchetes de cierre al final si es necesario
    last_line = new_lines[-1] if new_lines else ""
    if ']' not in last_line:
        # Buscar la línea con urlpatterns = [
        for i, line in enumerate(new_lines):
            if 'urlpatterns = [' in line:
                # Agregar ] al final del archivo si falta
                if new_lines[-1].strip() and new_lines[-1].strip() != ']':
                    new_lines.append(']\n')
                    print("✅ Agregado ] de cierre al final")
                break

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# Verificar sintaxis final
import ast
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print("✅ Sintaxis correcta")
except SyntaxError as e:
    print(f"❌ Error persistente en línea {e.lineno}: {e.msg}")
    if e.lineno <= len(lines):
        print(f"   Línea {e.lineno}: {repr(lines[e.lineno-1])}")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

