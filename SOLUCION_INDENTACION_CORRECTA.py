#!/usr/bin/env python3
"""
Script para corregir la indentación y el código del bloque de WhatsApp
"""
import os

file_path = "taller/documentos/views.py"

print("═══════════════════════════════════════════════════════════════")
print("  CORRECCIÓN DE INDENTACIÓN Y CÓDIGO")
print("═══════════════════════════════════════════════════════════════")

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Crear backup
backup_path = f"{file_path}.backup_indent"
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"📦 Backup creado: {backup_path}")

# Encontrar línea con "¡Gracias por confiar en nuestros servicios!"""
insert_after = None
for i, line in enumerate(lines):
    if '¡Gracias por confiar en nuestros servicios!"""' in line:
        insert_after = i
        print(f"✅ Cierre de f-string encontrado en línea {i+1}")
        break

if insert_after is None:
    print("❌ No se encontró la línea de cierre del f-string")
    exit(1)

# Obtener indentación correcta (la misma que la línea de cierre)
close_line = lines[insert_after]
indent = len(close_line) - len(close_line.lstrip())
indent_str = ' ' * indent
print(f"📏 Indentación: {indent} espacios")

# Buscar y eliminar líneas problemáticas DESPUÉS del cierre
lines_to_remove = []
for i in range(insert_after + 1, min(len(lines), insert_after + 20)):
    line = lines[i]
    # Buscar líneas con mensaje_encoded o url_whatsapp que estén mal indentadas o duplicadas
    if ('mensaje_encoded = mensaje.replace' in line or 
        'url_whatsapp = f"https://wa.me/' in line or
        'url_whatsapp = (' in line):
        lines_to_remove.append(i)
        print(f"   🗑️  Eliminando línea {i+1}: {line.strip()[:60]}")

# Eliminar líneas en orden inverso para mantener índices
for i in reversed(lines_to_remove):
    del lines[i]

# Insertar código correcto DESPUÉS del cierre del f-string
# El código debe tener la misma indentación que el bloque actual
correct_code = [
    '\n',
    indent_str + '# Crear URL de WhatsApp\n',
    indent_str + '# Nota: No se pueden usar backslashes directamente en expresiones f-string\n',
    indent_str + 'mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n',
    indent_str + 'url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"\n',
    '\n',
]

# Verificar si ya existe código correcto después
# Si existe, no insertar duplicado
has_correct_code = False
for i in range(insert_after + 1, min(len(lines), insert_after + 10)):
    if 'mensaje_encoded = mensaje.replace(" ", "%20")' in lines[i]:
        has_correct_code = True
        print(f"✅ Código correcto ya existe en línea {i+1}")
        break

if not has_correct_code:
    # Insertar después de la línea de cierre
    new_lines = lines[:insert_after+1] + correct_code + lines[insert_after+1:]
    print("✅ Código correcto insertado")
else:
    new_lines = lines

# Escribir archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Archivo actualizado")

# Verificar sintaxis
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    compile(content, file_path, 'exec')
    print("✅ Sintaxis Python válida")
    
    # Mostrar líneas alrededor del cambio
    print("\n📋 Líneas alrededor del cambio:")
    for i in range(max(0, insert_after - 2), min(len(new_lines), insert_after + 10)):
        marker = ">>> " if i == insert_after else "    "
        print(f"{marker}{i+1:4d}: {new_lines[i].rstrip()}")
        
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Mostrar contexto del error
    if e.lineno:
        error_idx = e.lineno - 1
        print("\n📋 Contexto del error:")
        for i in range(max(0, error_idx - 3), min(len(new_lines), error_idx + 3)):
            marker = ">>> " if i == error_idx else "    "
            print(f"{marker}{i+1:4d}: {new_lines[i].rstrip()}")
    
    print("🔄 Restaurando desde backup...")
    with open(backup_path, 'r', encoding='utf-8') as f:
        backup_content = f.read()
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(backup_content)
    exit(1)

print("\n✅ Proceso completado exitosamente")

