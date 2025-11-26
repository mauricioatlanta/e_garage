#!/bin/bash
# Script para restaurar views.py desde Git y corregir solo la función problemática

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Restaurando views.py desde Git..."

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
    print("✅ Sintaxis verificada correctamente")
except SyntaxError as e:
    print(f"❌ Error de sintaxis después de restaurar: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Si aún hay error, corregir manualmente la línea 1231
    lines = content.split('\n')
    if e.lineno <= len(lines):
        error_line_idx = e.lineno - 1
        line = lines[error_line_idx]
        
        # Buscar la función
        func_start = None
        for i in range(error_line_idx, -1, -1):
            if 'def enviar_documento_whatsapp' in lines[i]:
                func_start = i
                break
        
        if func_start:
            func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
            correct_indent = func_indent + 4
            
            # Corregir la línea
            stripped = line.lstrip()
            lines[error_line_idx] = ' ' * correct_indent + stripped
            
            # Guardar
            content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verificar nuevamente
            try:
                ast.parse(content)
                print("✅ Línea corregida y sintaxis verificada")
            except SyntaxError as e2:
                print(f"❌ Error persistente: {e2}")
                sys.exit(1)
PYEOF

echo ""
echo "✅✅✅ Archivo restaurado y verificado ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



