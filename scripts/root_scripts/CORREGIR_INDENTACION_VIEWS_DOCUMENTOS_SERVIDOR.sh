#!/bin/bash
# Script para corregir el error de indentación en taller/documentos/views.py línea 1231

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo error de indentación en views.py línea 1231..."

python3 << 'PYEOF'
import sys
import ast

file_path = "taller/documentos/views.py"

# Leer el archivo
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar sintaxis
try:
    content = ''.join(lines)
    ast.parse(content)
    print("✅ La sintaxis del archivo es correcta")
except SyntaxError as e:
    print(f"❌ Error de sintaxis encontrado: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    print(f"   Mensaje: {e.msg}")
    
    # Buscar la línea problemática
    error_line = e.lineno - 1  # Convertir a índice 0-based
    
    if error_line < len(lines):
        print(f"\n   Línea problemática ({e.lineno}):")
        print(f"   '{lines[error_line].rstrip()}'")
        
        # Mostrar contexto
        start = max(0, error_line - 5)
        end = min(len(lines), error_line + 5)
        print(f"\n   Contexto alrededor de la línea {e.lineno}:")
        for i in range(start, end):
            marker = ">>>" if i == error_line else "   "
            print(f"{marker} {i+1:4d}: {lines[i].rstrip()}")
        
        # Intentar corregir la indentación
        if 'return JsonResponse(' in lines[error_line]:
            # Calcular la indentación correcta basándose en la función
            # Buscar la definición de la función
            func_start = None
            for i in range(error_line, -1, -1):
                if lines[i].strip().startswith('def '):
                    func_start = i
                    break
            
            if func_start is not None:
                # La indentación dentro de una función debería ser 4 espacios
                # Buscar el nivel de indentación de la función
                func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
                # Las líneas dentro de la función deberían tener func_indent + 4
                correct_indent = func_indent + 4
                
                # Corregir la línea
                line_content = lines[error_line].lstrip()
                lines[error_line] = ' ' * correct_indent + line_content
                print(f"\n   ✅ Línea corregida: indentación cambiada a {correct_indent} espacios")
            else:
                # Si no encontramos la función, usar 4 espacios por defecto
                line_content = lines[error_line].lstrip()
                lines[error_line] = '    ' + line_content
                print(f"\n   ✅ Línea corregida: indentación cambiada a 4 espacios")
        else:
            # Para otros tipos de errores, intentar corregir basándose en el contexto
            # Buscar la línea anterior con contenido
            prev_line = error_line - 1
            while prev_line >= 0 and not lines[prev_line].strip():
                prev_line -= 1
            
            if prev_line >= 0:
                prev_indent = len(lines[prev_line]) - len(lines[prev_line].lstrip())
                # Si la línea anterior tiene contenido, usar la misma indentación
                line_content = lines[error_line].lstrip()
                lines[error_line] = ' ' * prev_indent + line_content
                print(f"\n   ✅ Línea corregida: indentación alineada con línea anterior")
    
    # Verificar sintaxis nuevamente
    try:
        content = ''.join(lines)
        ast.parse(content)
        print("\n✅✅✅ Sintaxis corregida y verificada")
        
        # Guardar el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ Archivo guardado")
    except SyntaxError as e2:
        print(f"\n❌ Aún hay errores de sintaxis después de la corrección: {e2}")
        print(f"   Línea {e2.lineno}: {e2.text}")
        sys.exit(1)
else:
    print("✅ Archivo verificado correctamente")
PYEOF

echo ""
echo "✅✅✅ Corrección aplicada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



