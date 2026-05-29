#!/bin/bash
# Script para corregir la función enviar_documento_whatsapp en views.py

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo función enviar_documento_whatsapp en views.py..."

python3 << 'PYEOF'
file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar sintaxis primero
import ast
try:
    ast.parse(content)
    print("✅ La sintaxis del archivo es correcta")
except SyntaxError as e:
    print(f"❌ Error de sintaxis encontrado: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Buscar la función enviar_documento_whatsapp y corregirla
    lines = content.split('\n')
    
    # Encontrar el inicio de la función
    func_start = None
    for i, line in enumerate(lines):
        if 'def enviar_documento_whatsapp' in line:
            func_start = i
            break
    
    if func_start is None:
        print("❌ No se encontró la función enviar_documento_whatsapp")
        sys.exit(1)
    
    print(f"📍 Función encontrada en línea {func_start + 1}")
    
    # Encontrar el final de la función (buscar la siguiente función o el final del archivo)
    func_end = len(lines)
    for i in range(func_start + 1, len(lines)):
        if lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
            # Si la línea no está indentada y no está vacía, probablemente es otra función
            if lines[i].strip().startswith('def ') or lines[i].strip().startswith('class '):
                func_end = i
                break
    
    print(f"📍 Función termina aproximadamente en línea {func_end}")
    
    # Corregir la indentación de todas las líneas dentro de la función
    func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
    corrected = False
    
    for i in range(func_start + 1, func_end):
        line = lines[i]
        stripped = line.lstrip()
        
        if not stripped:  # Línea vacía
            continue
        
        if stripped.startswith('#'):  # Comentario
            continue
        
        # Calcular la indentación actual
        current_indent = len(line) - len(stripped)
        
        # Si la línea está al mismo nivel o menos que la función, es un error
        if current_indent <= func_indent and not stripped.startswith('"""') and not stripped.startswith("'''"):
            # Esta línea debería estar dentro de la función, necesita más indentación
            # Usar func_indent + 4 como mínimo
            lines[i] = ' ' * (func_indent + 4) + stripped
            corrected = True
            print(f"   🔧 Línea {i+1}: indentación corregida")
        elif 'return JsonResponse(' in line and current_indent < func_indent + 4:
            # Específicamente corregir el return JsonResponse
            lines[i] = ' ' * (func_indent + 4) + stripped
            corrected = True
            print(f"   🔧 Línea {i+1} (return JsonResponse): indentación corregida")
    
    if corrected:
        content = '\n'.join(lines)
        
        # Verificar sintaxis nuevamente
        try:
            ast.parse(content)
            print("✅ Sintaxis corregida y verificada")
            
            # Guardar el archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Archivo guardado")
        except SyntaxError as e2:
            print(f"❌ Aún hay errores después de la corrección: {e2}")
            print(f"   Línea {e2.lineno}: {e2.text}")
            sys.exit(1)
    else:
        print("ℹ️  No se encontraron problemas de indentación obvios")
        print("   Intentando corrección más agresiva...")
        
        # Buscar específicamente la línea con return JsonResponse alrededor de la línea 1231
        target_line = 1230  # Línea 1231 en índice 0-based
        if target_line < len(lines):
            line = lines[target_line]
            if 'return JsonResponse' in line:
                # Forzar indentación correcta
                func_indent = 4  # Asumir que la función tiene 4 espacios de indentación
                stripped = line.lstrip()
                lines[target_line] = ' ' * (func_indent + 4) + stripped
                print(f"   🔧 Línea {target_line + 1}: indentación forzada a 8 espacios")
                
                content = '\n'.join(lines)
                
                try:
                    ast.parse(content)
                    print("✅ Sintaxis corregida")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("✅ Archivo guardado")
                except SyntaxError as e3:
                    print(f"❌ Error persistente: {e3}")
                    sys.exit(1)
PYEOF

echo ""
echo "✅✅✅ Corrección aplicada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



