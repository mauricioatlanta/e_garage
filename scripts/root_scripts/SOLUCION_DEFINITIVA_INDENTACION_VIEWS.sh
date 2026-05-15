#!/bin/bash
# Solución definitiva: restaurar desde Git y corregir si es necesario

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando solución definitiva para indentación..."

# Backup
cp taller/documentos/views.py taller/documentos/views.py.backup_$(date +%Y%m%d_%H%M%S)

# Restaurar desde Git
echo "📥 Restaurando desde Git..."
git checkout HEAD -- taller/documentos/views.py 2>&1

# Verificar y corregir
python3 << 'PYEOF'
import sys
import ast

file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar sintaxis
try:
    content = ''.join(lines)
    ast.parse(content)
    print("✅ Archivo tiene sintaxis correcta después de restaurar desde Git")
    sys.exit(0)
except SyntaxError as e:
    print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
    print(f"   Línea: {e.text}")
    
    error_idx = e.lineno - 1
    
    # Buscar función
    func_start = None
    for i in range(error_idx, -1, -1):
        if 'def enviar_documento_whatsapp' in lines[i]:
            func_start = i
            break
    
    if not func_start:
        print("❌ No se encontró la función")
        sys.exit(1)
    
    func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
    correct_indent = func_indent + 4
    
    print(f"📍 Función en línea {func_start+1}, indentación correcta: {correct_indent}")
    
    # Corregir línea problemática y siguientes relacionadas
    fixed = False
    for i in range(error_idx, min(error_idx + 15, len(lines))):
        line = lines[i]
        stripped = line.lstrip()
        
        if not stripped:
            continue
        
        current_indent = len(line) - len(stripped)
        
        # Si es return JsonResponse o está mal indentada dentro de la función
        if 'return JsonResponse' in line or (current_indent < func_indent + 4 and i > func_start):
            if current_indent != correct_indent:
                lines[i] = ' ' * correct_indent + stripped + '\n'
                fixed = True
                print(f"   🔧 Línea {i+1}: {current_indent} -> {correct_indent} espacios")
            
            # Si encontramos el cierre, también corregir
            if stripped == ')' and i > error_idx:
                # Verificar siguiente línea
                if i + 1 < len(lines) and lines[i+1].strip() == '':
                    break
    
    if not fixed:
        # Forzar corrección de la línea específica
        line = lines[error_idx]
        stripped = line.lstrip()
        lines[error_idx] = ' ' * correct_indent + stripped + '\n'
        print(f"   🔧 Línea {error_idx+1}: forzada a {correct_indent} espacios")
        fixed = True
    
    if fixed:
        # Verificar sintaxis
        content = ''.join(lines)
        try:
            ast.parse(content)
            print("✅ Sintaxis corregida y verificada")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print("✅ Archivo guardado")
        except SyntaxError as e2:
            print(f"❌ Error persistente: {e2}")
            print(f"   Línea {e2.lineno}: {e2.text}")
            
            # Mostrar más contexto
            error_lines = content.split('\n')
            start = max(0, e2.lineno - 5)
            end = min(len(error_lines), e2.lineno + 5)
            for i in range(start, end):
                marker = ">>>" if i == e2.lineno - 1 else "   "
                print(f"{marker} {i+1:4d}: {error_lines[i]}")
            
            sys.exit(1)
    else:
        print("⚠️  No se pudo corregir automáticamente")
        sys.exit(1)
PYEOF

echo ""
echo "✅✅✅ Solución aplicada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



