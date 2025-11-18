#!/usr/bin/env python
"""
Script para actualizar templates/taller/configuracion/tecnicos.html en el servidor
Cambia el template base de 'taller/base.html' a 'base.html'
"""
import os
import shutil
import time

file_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/taller/configuracion/tecnicos.html"

print("=" * 70)
print("ACTUALIZANDO templates/taller/configuracion/tecnicos.html EN EL SERVIDOR")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Cambiar el template base
old_extends = "{% extends 'taller/base.html' %}"
new_extends = "{% extends 'base.html' %}"

if old_extends in content:
    content = content.replace(old_extends, new_extends)
    print("✅ Template base cambiado de 'taller/base.html' a 'base.html'")
else:
    # Buscar variantes
    if "extends 'taller/base.html'" in content or 'extends "taller/base.html"' in content:
        content = content.replace("{% extends 'taller/base.html' %}", new_extends)
        content = content.replace('{% extends "taller/base.html" %}', new_extends)
        print("✅ Template base actualizado (variantes)")
    else:
        print("⚠️  No se encontró 'taller/base.html' en el template")

# Escribir el archivo actualizado
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo actualizado: {file_path}")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()
    if "{% extends 'base.html' %}" in check or '{% extends "base.html" %}' in check:
        print("✅ Verificación: Template ahora extiende 'base.html'")
    if "taller/base.html" not in check:
        print("✅ Verificación: No hay referencias a 'taller/base.html'")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py")
print("=" * 70)
