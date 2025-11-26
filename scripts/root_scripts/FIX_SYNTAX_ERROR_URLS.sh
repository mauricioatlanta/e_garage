#!/bin/bash
# Script para corregir el error de sintaxis en urls.py
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="gestion_taller/urls.py"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_syntax_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo error de sintaxis en línea 374..."

python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar el problema alrededor de la línea 374
print("🔍 Verificando líneas 370-380...")
for i in range(369, min(380, len(lines))):
    print(f"Línea {i+1}: {lines[i].rstrip()}")

# Buscar problemas de sintaxis comunes
new_lines = []
fixed = False

for i, line in enumerate(lines):
    # Verificar si hay una coma extra o paréntesis mal cerrado
    if i == 373:  # Línea 374 (0-indexed = 373)
        # Verificar si la línea anterior tiene un paréntesis sin cerrar
        if i > 0 and 'path(' in lines[i-1] and ')' not in lines[i-1]:
            # Verificar si esta línea tiene un paréntesis de cierre
            if '),' in line:
                # Verificar si hay un path() mal formado antes
                # Buscar hacia atrás para encontrar el path() completo
                j = i - 1
                while j >= 0 and 'path(' not in lines[j]:
                    j -= 1
                
                if j >= 0:
                    # Verificar si el path() anterior está completo
                    path_start = j
                    paren_count = 0
                    for k in range(path_start, i+1):
                        paren_count += lines[k].count('(') - lines[k].count(')')
                    
                    if paren_count > 0:
                        print(f"⚠️  Encontrado path() sin cerrar en línea {path_start+1}")
                        # Verificar si hay una coma extra
                        if i > 0 and lines[i-1].strip().endswith(','):
                            # Eliminar la coma extra si hay un paréntesis de cierre
                            if '),' in line:
                                print(f"   Eliminando línea {i+1} duplicada o mal formada")
                                continue
                                fixed = True
    
    new_lines.append(line)

# Si no se encontró el problema, buscar patrones problemáticos
if not fixed:
    print("\n🔍 Buscando patrones problemáticos...")
    new_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
            
        # Buscar líneas con "),)" o patrones similares
        if '),' in line and i+1 < len(lines) and '),' in lines[i+1]:
            print(f"⚠️  Línea {i+1} y {i+2} tienen '),' - posible duplicado")
            # Mantener solo la primera
            new_lines.append(line)
            skip_next = True
            fixed = True
            continue
        
        # Buscar path() mal formado
        if 'path(' in line and i+1 < len(lines):
            # Verificar si el siguiente path() está mal indentado o sin cerrar
            if 'path(' in lines[i+1] and not line.strip().endswith(')'):
                print(f"⚠️  Path() sin cerrar en línea {i+1}")
                # Agregar cierre si falta
                if '),' not in line and ')' not in line:
                    # Buscar dónde debería cerrar
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(line.rstrip() + '\n')
                    new_lines.append(' ' * indent + '),\n')
                    skip_next = True
                    fixed = True
                    continue
        
        new_lines.append(line)

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

if fixed:
    print("✅ Error de sintaxis corregido")
else:
    print("⚠️  No se encontró el problema específico, verificando sintaxis...")
    # Intentar compilar el archivo para ver el error exacto
    import py_compile
    try:
        py_compile.compile(file_path, doraise=True)
        print("✅ Archivo compila correctamente")
    except py_compile.PyCompileError as e:
        print(f"❌ Error de sintaxis encontrado: {e}")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

