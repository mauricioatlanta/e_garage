#!/usr/bin/env python
"""
Script para corregir la navegación en templates/base.html en el servidor
Cambia flex-wrap a flex-nowrap para que los botones estén en una sola línea
"""
import os
import shutil
import time

file_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/base.html"

print("=" * 70)
print("CORRIGIENDO NAVEGACIÓN EN templates/base.html")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Cambiar flex-wrap a flex-nowrap y agregar overflow-x-auto
old_line = (
    '    <div class="flex flex-wrap items-center justify-center gap-3 max-w-7xl w-full px-4">'
)
new_line = '    <div class="flex flex-nowrap items-center justify-center gap-3 max-w-7xl w-full px-4 overflow-x-auto">'

if old_line in content:
    content = content.replace(old_line, new_line)
    print("✅ Navegación corregida: flex-wrap cambiado a flex-nowrap")
else:
    # Buscar variantes
    if "flex-wrap" in content and "main-navigation" in content:
        lines = content.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            if "flex-wrap" in line and "main-navigation" in "\n".join(lines[max(0, i - 2) : i + 2]):
                # Reemplazar flex-wrap con flex-nowrap y agregar overflow-x-auto
                new_line = line.replace("flex-wrap", "flex-nowrap")
                if "overflow-x-auto" not in new_line:
                    # Agregar overflow-x-auto antes del cierre de la clase
                    new_line = new_line.replace('">', ' overflow-x-auto">')
                new_lines.append(new_line)
                print(f"✅ Navegación corregida en línea {i+1}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        print("⚠️  No se encontró flex-wrap en la navegación")

# Escribir el archivo actualizado
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo actualizado: {file_path}")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()
    if "flex-nowrap" in check and "main-navigation" in check:
        print("✅ Verificación: flex-nowrap encontrado en la navegación")
    if "overflow-x-auto" in check and "main-navigation" in check:
        print("✅ Verificación: overflow-x-auto encontrado en la navegación")
    if "flex-wrap" not in check or check.find("flex-wrap") > check.find("main-navigation") + 500:
        print("✅ Verificación: flex-wrap eliminado de la navegación")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py")
print("=" * 70)
