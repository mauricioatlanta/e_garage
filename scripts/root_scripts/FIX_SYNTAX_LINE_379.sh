#!/bin/bash
# Script para corregir específicamente el error en línea 379
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_line379_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo error en línea 379..."

python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Leer y mostrar las líneas problemáticas
print("🔍 Líneas 375-385:")
for i in range(374, min(385, len(lines))):
    print(f"Línea {i+1}: {repr(lines[i])}")

# El error "positional argument follows keyword argument" generalmente ocurre
# cuando hay algo como: path("url", view, name="name", otro_arg)
# en lugar de: path("url", view, name="name")

# Buscar el problema específico
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Si encontramos un path() que podría tener el problema
    if 'path(' in line:
        # Leer el path() completo
        path_lines = [line]
        j = i + 1
        paren_count = line.count('(') - line.count(')')
        
        while j < len(lines) and paren_count > 0 and j < i + 10:
            path_lines.append(lines[j])
            paren_count += lines[j].count('(') - lines[j].count(')')
            if '),' in lines[j] and paren_count == 0:
                break
            j += 1
        
        # Verificar si hay un problema en este path()
        path_content = ''.join(path_lines)
        
        # Buscar patrones problemáticos
        # Si hay RedirectView.as_view(url="...") seguido de otro argumento posicional
        if 'RedirectView.as_view' in path_content:
            # Verificar si hay argumentos después de name=
            if 'name=' in path_content:
                name_pos = path_content.find('name=')
                after_name = path_content[name_pos:]
                # Si hay algo después de name= que no sea ), o una coma
                if '),' not in after_name[:20] and ',' in after_name[:20]:
                    # Puede haber un argumento posicional después
                    print(f"⚠️  Posible problema en path() línea {i+1}")
        
        # Agregar las líneas del path()
        new_lines.extend(path_lines)
        i = j + 1
    else:
        new_lines.append(line)
        i += 1

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# Verificar sintaxis
import ast
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print("✅ Sintaxis correcta")
except SyntaxError as e:
    print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
    if e.text:
        print(f"   Texto: {repr(e.text)}")
    
    # Si el error persiste, intentar una corrección más agresiva
    if e.lineno == 379:
        print("🔧 Aplicando corrección específica para línea 379...")
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # La línea 379 debería ser el cierre de un path()
        # Verificar si hay algo mal antes
        if 378 < len(lines):
            # Verificar la línea anterior
            prev_line = lines[377] if 377 < len(lines) else ""
            curr_line = lines[378]  # Línea 379 (0-indexed)
            
            print(f"Línea 378: {repr(prev_line)}")
            print(f"Línea 379: {repr(curr_line)}")
            
            # Si la línea 379 es solo ")," y la anterior también termina con algo raro
            if curr_line.strip() == '),' and prev_line.strip().endswith(','):
                # Puede haber una coma extra
                print("   Eliminando posible línea duplicada...")
                new_lines = lines[:378] + lines[379:]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print("✅ Línea duplicada eliminada")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

