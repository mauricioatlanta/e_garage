#!/usr/bin/env python3
"""
Script para corregir la línea 1229 en views.py
Ejecutar en el servidor: python3 CORREGIR_LINEA_1229.py
"""
import os

file_path = "taller/documentos/views.py"

if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} no encontrado")
    print(f"   cd /home/atlantareciclajes/apps/egarage/current")
    exit(1)

print(f"📄 Procesando {file_path}...")

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Crear backup
backup_path = f"{file_path}.backup3"
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"📦 Backup creado: {backup_path}")

# Mostrar líneas alrededor de 1229
print("\n📋 Líneas alrededor de 1229:")
for i in range(1225, min(len(lines), 1235)):
    marker = ">>> " if i == 1228 else "    "
    print(f"{marker}{i+1:4d}: {lines[i].rstrip()}")

# Buscar la línea problemática (1229 o cerca)
target_line_idx = None
for i in range(max(0, 1225), min(len(lines), 1235)):
    line = lines[i]
    # Buscar línea con f-string que tenga wa.me y mensaje.replace con \n
    if ('wa.me' in line and 'f"' in line and 'mensaje' in line and 
        ('replace' in line or '\\n' in line or "'\\n'" in line)):
        target_line_idx = i
        print(f"\n⚠️  Línea problemática encontrada en línea {i+1}")
        print(f"   {line.strip()}")
        break

if target_line_idx is None:
    print("\n⚠️  No se encontró la línea problemática en el rango esperado")
    print("   Buscando en todo el archivo...")
    for i, line in enumerate(lines):
        if 'wa.me' in line and 'mensaje' in line and ('replace' in line or '\\n' in line):
            print(f"   Línea {i+1}: {line.strip()[:100]}")
    exit(1)

# Verificar contexto: debe estar después del cierre de un f-string multilinea
# Buscar si hay """ antes (dentro de 20 líneas anteriores)
context_ok = False
for i in range(max(0, target_line_idx - 20), target_line_idx):
    if '"""' in lines[i] and i < target_line_idx - 1:
        # Verificar que después no haya otro """
        for j in range(i + 1, target_line_idx):
            if '"""' in lines[j]:
                context_ok = True
                break
        if context_ok:
            break

if not context_ok:
    print("⚠️  Contexto no verificado, continuando de todas formas...")

# Obtener indentación
problem_line = lines[target_line_idx]
indent = len(problem_line) - len(problem_line.lstrip())
indent_str = ' ' * indent

# Extraer variable telefono del f-string
import re
telefono_match = re.search(r'\{([^}]+)\}', problem_line)
telefono_var = telefono_match.group(1) if telefono_match else 'telefono'
print(f"   Variable telefono encontrada: {telefono_var}")
print(f"   Indentación: {indent} espacios")

# Crear nuevo código
new_code = [
    indent_str + '# Crear URL de WhatsApp\n',
    indent_str + '# Nota: No se pueden usar backslashes directamente en expresiones f-string\n',
    indent_str + 'mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n',
    indent_str + f'url_whatsapp = f"https://wa.me/{{{telefono_var}}}?text={{mensaje_encoded}}"\\n'
]

print("\n✅ Código a insertar:")
for line in new_code:
    print(f"   {line.rstrip()}")

# Reemplazar la línea problemática
new_lines = lines[:target_line_idx] + new_code + lines[target_line_idx + 1:]

# Escribir el archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print(f"\n✅ Archivo actualizado (línea {target_line_idx + 1} reemplazada)")

# Verificar sintaxis
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    compile(content, file_path, 'exec')
    print("✅ Sintaxis Python válida")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    print("🔄 Restaurando desde backup...")
    with open(backup_path, 'r', encoding='utf-8') as f:
        backup_content = f.read()
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(backup_content)
    exit(1)

print("\n✅ Proceso completado")
print("\n💡 Reinicia el servidor WSGI:")
print("   touch /var/www/www_egarage_cl_wsgi.py")

