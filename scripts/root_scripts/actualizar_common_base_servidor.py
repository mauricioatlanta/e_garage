#!/usr/bin/env python
"""
Script para actualizar common/base.html en el servidor
Elimina la flor azul, el emoji del edificio y cambia el color del título a blanco
"""
import os
import shutil
import time
import re

file_path = (
    "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/common/base.html"
)

print("=" * 70)
print("ACTUALIZANDO templates/common/base.html EN EL SERVIDOR")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Cambio 1: Cambiar el color del título a blanco
old_css = ".company-title {\n      color: var(--company-primary);\n      text-shadow: 0 0 20px var(--company-primary), 0 0 40px var(--company-primary);\n      filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));\n    }"
new_css = ".company-title {\n      color: #ffffff !important;\n      text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);\n      filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));\n    }"

if old_css in content:
    content = content.replace(old_css, new_css)
    print("✅ Cambio 1: Color del título cambiado a blanco")
else:
    # Buscar con regex
    pattern = r"\.company-title\s*\{[^}]+\}"
    if re.search(pattern, content, re.MULTILINE | re.DOTALL):
        content = re.sub(
            pattern, new_css.replace("\n", "\n"), content, flags=re.MULTILINE | re.DOTALL
        )
        print("✅ Cambio 1: Color del título actualizado (usando regex)")
    else:
        print("⚠️  Cambio 1: No se encontró el CSS exacto")

# Cambio 2: Eliminar la flor azul (marcador de debug)
if "🌼 AZUL" in content:
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if "🌼 AZUL" in line:
            print(f"✅ Cambio 2: Eliminando línea con flor azul: {line[:50]}...")
            continue  # Saltar esta línea
        new_lines.append(line)
    content = "\n".join(new_lines)
    print("✅ Cambio 2: Flor azul eliminada")
else:
    print("✅ Cambio 2: La flor azul ya fue eliminada o no existe")

# Cambio 3: Eliminar el emoji del edificio 🏢
if "🏢" in content:
    lines = content.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        if "🏢" in lines[i]:
            # Buscar el inicio del bloque (puede ser un div con el emoji)
            start = max(0, i - 3)
            # Buscar el fin del bloque
            end = min(len(lines), i + 3)
            # Verificar si es un bloque completo que debemos eliminar
            block_text = "\n".join(lines[start : end + 1])
            if '<div class="company-logo' in block_text and "🏢</span>" in block_text:
                # Es un bloque completo, eliminarlo
                print(
                    f"✅ Cambio 3: Eliminando bloque con emoji del edificio (líneas {start+1}-{end+1})"
                )
                i = end + 1
                continue
            else:
                # Solo eliminar la línea con el emoji
                print(f"✅ Cambio 3: Eliminando línea con emoji del edificio: {lines[i][:50]}...")
                i += 1
                continue
        new_lines.append(lines[i])
        i += 1
    content = "\n".join(new_lines)
    print("✅ Cambio 3: Emoji del edificio eliminado")
else:
    print("✅ Cambio 3: El emoji del edificio ya fue eliminado o no existe")

# Escribir el archivo actualizado
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo actualizado: {file_path}")
print(f"✅ Tamaño: {len(content)} caracteres")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    content_check = f.read()
    if "color: #ffffff" in content_check or "color:#ffffff" in content_check:
        print("✅ Verificación: Color blanco encontrado en el CSS")
    if "🌼 AZUL" not in content_check:
        print("✅ Verificación: Flor azul no encontrada (eliminada)")
    else:
        print("⚠️  Advertencia: La flor azul aún existe en el archivo")
    if "🏢" not in content_check:
        print("✅ Verificación: Emoji del edificio no encontrado (eliminado)")
    else:
        print("⚠️  Advertencia: El emoji del edificio aún existe en el archivo")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py")
print("=" * 70)
