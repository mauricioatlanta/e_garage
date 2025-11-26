#!/bin/bash
# Script para corregir específicamente la línea 1231 en views.py

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo indentación en línea 1231 de views.py..."

# Primero, hacer backup
cp taller/documentos/views.py taller/documentos/views.py.backup_$(date +%Y%m%d_%H%M%S)

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
    sys.exit(0)
except SyntaxError as e:
    print(f"❌ Error de sintaxis encontrado: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Línea problemática (índice 0-based)
    error_line_idx = e.lineno - 1
    
    if error_line_idx >= len(lines):
        print(f"❌ Línea {e.lineno} está fuera del archivo")
        sys.exit(1)
    
    print(f"\n📍 Línea problemática ({e.lineno}):")
    print(f"   '{lines[error_line_idx].rstrip()}'")
    
    # Mostrar contexto
    start = max(0, error_line_idx - 10)
    end = min(len(lines), error_line_idx + 10)
    print(f"\n   Contexto (líneas {start+1} a {end}):")
    for i in range(start, end):
        marker = ">>>" if i == error_line_idx else "   "
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"{marker} {i+1:4d} [{indent:2d}]: {lines[i].rstrip()}")
    
    # Buscar la función que contiene esta línea
    func_start = None
    for i in range(error_line_idx, -1, -1):
        if lines[i].strip().startswith('def '):
            func_start = i
            break
    
    if func_start is None:
        print("❌ No se encontró la función que contiene esta línea")
        sys.exit(1)
    
    print(f"\n📍 Función encontrada en línea {func_start + 1}: {lines[func_start].strip()}")
    
    # Calcular indentación correcta
    func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
    correct_indent = func_indent + 4  # Dentro de función = indentación de función + 4
    
    print(f"   Indentación de función: {func_indent} espacios")
    print(f"   Indentación correcta dentro de función: {correct_indent} espacios")
    
    # Corregir la línea problemática
    line_content = lines[error_line_idx].lstrip()
    current_indent = len(lines[error_line_idx]) - len(line_content)
    
    print(f"\n   Indentación actual: {current_indent} espacios")
    print(f"   Contenido: '{line_content[:50]}...'")
    
    # Corregir
    lines[error_line_idx] = ' ' * correct_indent + line_content + '\n'
    print(f"   ✅ Corregida a {correct_indent} espacios")
    
    # También corregir líneas siguientes si están mal indentadas
    # (puede haber un bloque completo mal indentado)
    fixed_count = 1
    for i in range(error_line_idx + 1, min(error_line_idx + 20, len(lines))):
        line = lines[i]
        stripped = line.lstrip()
        
        if not stripped:  # Línea vacía
            continue
        
        if stripped.startswith('#'):  # Comentario
            continue
        
        # Si la línea está al mismo nivel o menos que la función, es un error
        current_indent = len(line) - len(stripped)
        
        # Si está dentro de la función pero mal indentada
        if current_indent <= func_indent and not stripped.startswith('def ') and not stripped.startswith('class '):
            # Verificar si debería estar dentro de la función
            # (si hay un 'return' o está dentro de un bloque)
            if 'return' in stripped or stripped.startswith('}') or stripped.startswith(')'):
                lines[i] = ' ' * correct_indent + stripped + '\n'
                fixed_count += 1
                print(f"   🔧 Línea {i+1}: también corregida")
    
    print(f"\n✅ Total de líneas corregidas: {fixed_count}")
    
    # Verificar sintaxis nuevamente
    try:
        content = ''.join(lines)
        ast.parse(content)
        print("✅✅✅ Sintaxis corregida y verificada")
        
        # Guardar el archivo corregido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("✅ Archivo guardado")
    except SyntaxError as e2:
        print(f"\n❌ Aún hay errores de sintaxis después de la corrección: {e2}")
        print(f"   Línea {e2.lineno}: {e2.text}")
        
        # Intentar restaurar desde Git como último recurso
        print("\n🔄 Intentando restaurar desde Git...")
        import subprocess
        result = subprocess.run(['git', 'checkout', 'HEAD', '--', file_path], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Archivo restaurado desde Git")
            # Ahora aplicar la corrección manualmente
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar y reemplazar la línea problemática específicamente
            if 'return JsonResponse(' in content:
                # Encontrar la función completa y reemplazarla
                import re
                # Patrón más específico
                pattern = r'(def enviar_documento_whatsapp\([^)]+\):.*?)(return JsonResponse\([^)]+\))'
                replacement = r'\1    return JsonResponse('
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ Corrección manual aplicada")
        else:
            print(f"❌ Error al restaurar desde Git: {result.stderr}")
            sys.exit(1)
PYEOF

echo ""
echo "✅✅✅ Corrección aplicada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



