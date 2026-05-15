#!/usr/bin/env python3
"""
Script para corregir el error de indentación en taller/documentos/views.py
Corrige específicamente el problema alrededor de la línea 1224
"""

import sys
import re

file_path = "taller/documentos/views.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
except FileNotFoundError:
    print(f"❌ Error: No se encontró el archivo {file_path}")
    sys.exit(1)

# Crear backup
backup_path = f"{file_path}.backup_indent"
print(f"📋 Creando backup en {backup_path}...")
with open(backup_path, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("✅ Backup creado")

# Buscar la línea con el cierre del f-string
target_line_idx = None
for i, line in enumerate(lines):
    if '¡Gracias por confiar en nuestros servicios!"""' in line:
        target_line_idx = i
        break

if target_line_idx is None:
    print("❌ No se encontró la línea de cierre del f-string")
    sys.exit(1)

print(f"📍 Línea de cierre encontrada en línea {target_line_idx + 1}")

# Determinar la indentación correcta
# La línea de cierre del f-string debe estar al mismo nivel que el inicio del mensaje
# Buscar hacia atrás para encontrar el inicio del bloque
base_indent = 4  # Indentación estándar dentro de try block

# Verificar la indentación de la línea de cierre
close_line_indent = len(lines[target_line_idx]) - len(lines[target_line_idx].lstrip())

# Buscar la línea con "mensaje = f""" para determinar la indentación base
for i in range(target_line_idx, max(0, target_line_idx - 15), -1):
    if 'mensaje = f"""' in lines[i]:
        base_indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"📍 Indentación base determinada: {base_indent} espacios (línea {i+1})")
        break

# Corregir las líneas siguientes al cierre del f-string
fixed_lines = []
fixed_count = 0

for i in range(target_line_idx + 1, min(target_line_idx + 20, len(lines))):
    line = lines[i]
    stripped = line.lstrip()

    # Saltar líneas vacías
    if not stripped:
        fixed_lines.append(line)
        continue

    # Saltar comentarios (mantener su indentación original si es razonable)
    if stripped.startswith("#"):
        current_indent = len(line) - len(stripped)
        if current_indent < base_indent:
            fixed_lines.append(" " * base_indent + stripped)
            if current_indent != base_indent:
                fixed_count += 1
                print(
                    f"🔧 Corregida línea {i+1} (comentario): {current_indent} -> {base_indent} espacios"
                )
        else:
            fixed_lines.append(line)
        continue

    # Para líneas de código, deben tener exactamente base_indent espacios
    current_indent = len(line) - len(stripped)

    if current_indent != base_indent:
        print(f"🔧 Corrigiendo línea {i+1}: indentación {current_indent} -> {base_indent} espacios")
        print(f"   Contenido: {repr(stripped[:50])}")
        fixed_lines.append(" " * base_indent + stripped)
        fixed_count += 1
    else:
        fixed_lines.append(line)

# Reconstruir el archivo
new_lines = (
    lines[: target_line_idx + 1] + fixed_lines + lines[target_line_idx + 1 + len(fixed_lines) :]
)

# Verificar que no hayamos perdido líneas
if len(new_lines) != len(lines):
    print(f"⚠️  Advertencia: Número de líneas cambió ({len(lines)} -> {len(new_lines)})")
    # Usar el método más conservador: solo corregir las líneas problemáticas
    new_lines = lines.copy()
    for i in range(target_line_idx + 1, min(target_line_idx + 20, len(lines))):
        line = lines[i]
        stripped = line.lstrip()
        if stripped and not stripped.startswith("#"):
            current_indent = len(line) - len(stripped)
            if current_indent != base_indent:
                new_lines[i] = " " * base_indent + stripped
                fixed_count += 1
                print(f"🔧 Corregida línea {i+1}: {current_indent} -> {base_indent} espacios")

if fixed_count > 0:
    # Escribir archivo corregido
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"\n✅ Archivo corregido: {fixed_count} línea(s) modificada(s)")
    print(f"📋 Backup guardado en: {backup_path}")

    # Verificar sintaxis
    print("\n🔍 Verificando sintaxis...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, file_path, "exec")
        print("✅ Sintaxis válida - El archivo está correcto")
    except SyntaxError as e:
        print(f"❌ Aún hay error de sintaxis en línea {e.lineno}:")
        print(f"   {e.msg}")
        if e.lineno <= len(new_lines):
            print(f"   Línea: {repr(new_lines[e.lineno-1][:80])}")
        sys.exit(1)
else:
    print("\n⚠️  No se encontraron líneas con indentación incorrecta")
    print("💡 El archivo puede estar correcto o el problema está en otra ubicación")
