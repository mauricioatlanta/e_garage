#!/bin/bash
# Script para restaurar views.py completo desde Git

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Restaurando views.py completo desde Git..."

# Hacer backup
cp taller/documentos/views.py taller/documentos/views.py.backup_$(date +%Y%m%d_%H%M%S)

# Restaurar desde Git
git checkout HEAD -- taller/documentos/views.py

echo "✅ Archivo restaurado desde Git"

# Verificar sintaxis
python3 << 'PYEOF'
import ast

file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

try:
    ast.parse(content)
    print("✅ Sintaxis verificada correctamente después de restaurar desde Git")
except SyntaxError as e:
    print(f"❌ Error de sintaxis después de restaurar: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Si Git también tiene el error, corregir manualmente la línea 1231
    lines = content.split('\n')
    error_line_idx = e.lineno - 1
    
    if error_line_idx < len(lines):
        print(f"\n🔧 Corrigiendo línea {e.lineno} manualmente...")
        
        # Buscar la función
        func_start = None
        for i in range(error_line_idx, -1, -1):
            if 'def enviar_documento_whatsapp' in lines[i]:
                func_start = i
                break
        
        if func_start:
            func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
            correct_indent = func_indent + 4
            
            print(f"   Indentación de función: {func_indent}")
            print(f"   Indentación correcta: {correct_indent}")
            
            # Corregir la línea problemática y las siguientes si es necesario
            for i in range(error_line_idx, min(error_line_idx + 10, len(lines))):
                line = lines[i]
                stripped = line.lstrip()
                
                if not stripped:
                    continue
                
                current_indent = len(line) - len(stripped)
                
                # Si es el return JsonResponse o líneas relacionadas, corregir
                if 'return JsonResponse' in line or (i > error_line_idx and current_indent < func_indent + 4):
                    lines[i] = ' ' * correct_indent + stripped
                    print(f"   ✅ Línea {i+1} corregida")
                    
                    # Si encontramos el cierre, parar
                    if stripped == ')' and i > error_line_idx:
                        break
            
            # Guardar
            content = '\n'.join(lines)
            
            # Verificar nuevamente
            try:
                ast.parse(content)
                print("✅ Sintaxis corregida y verificada")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ Archivo guardado")
            except SyntaxError as e2:
                print(f"❌ Error persistente: {e2}")
                print(f"   Línea {e2.lineno}: {e2.text}")
                sys.exit(1)
        else:
            print("❌ No se encontró la función")
            sys.exit(1)
PYEOF

echo ""
echo "✅✅✅ Archivo restaurado y verificado ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



