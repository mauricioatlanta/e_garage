#!/usr/bin/env python
"""
Script para actualizar templates/taller/configuracion/tecnicos.html en el servidor
Cambia el template base a 'common/base.html' y agrega {% load country_url %}
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
    lines = f.readlines()

# Actualizar las primeras líneas
new_lines = []
updated_extends = False
updated_load = False

for i, line in enumerate(lines):
    if i == 0 and (
        "extends 'base.html'" in line
        or 'extends "base.html"' in line
        or "extends 'taller/base.html'" in line
    ):
        new_lines.append("{% extends 'common/base.html' %}\n")
        updated_extends = True
        print("✅ Template base cambiado a 'common/base.html'")
    elif i == 1 and "{% load static %}" in line:
        new_lines.append(line)
        # Agregar {% load country_url %} después de static
        if i + 1 < len(lines) and "{% load country_url %}" not in lines[i + 1]:
            new_lines.append("{% load country_url %}\n")
            updated_load = True
            print("✅ Agregado {% load country_url %}")
    elif "{% load country_url %}" in line:
        # Ya existe, no duplicar
        if not updated_load:
            new_lines.append(line)
            updated_load = True
    else:
        new_lines.append(line)

# Si no se actualizó, buscar y reemplazar manualmente
if not updated_extends:
    content = "".join(new_lines)
    if "{% extends 'base.html' %}" in content:
        content = content.replace("{% extends 'base.html' %}", "{% extends 'common/base.html' %}")
        print("✅ Template base actualizado (método alternativo)")
    elif '{% extends "base.html" %}' in content:
        content = content.replace('{% extends "base.html" %}', "{% extends 'common/base.html' %}")
        print("✅ Template base actualizado (método alternativo)")
    elif "{% extends 'taller/base.html' %}" in content:
        content = content.replace(
            "{% extends 'taller/base.html' %}", "{% extends 'common/base.html' %}"
        )
        print("✅ Template base actualizado (método alternativo)")

    if "{% load country_url %}" not in content.split("\n")[0:5]:
        # Agregar después de {% load static %}
        if "{% load static %}" in content:
            content = content.replace(
                "{% load static %}", "{% load static %}\n{% load country_url %}"
            )
            if not updated_load:
                print("✅ Agregado {% load country_url %} (método alternativo)")

    new_lines = content.splitlines(True)

# Escribir el archivo actualizado
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"\n✅ Archivo actualizado: {file_path}")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()
    if "{% extends 'common/base.html' %}" in check or '{% extends "common/base.html" %}' in check:
        print("✅ Verificación: Template ahora extiende 'common/base.html'")
    if "{% load country_url %}" in check:
        print("✅ Verificación: {% load country_url %} encontrado")
    if "taller/base.html" not in check and "extends 'base.html'" not in check:
        print("✅ Verificación: No hay referencias a otros templates base")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py")
print("=" * 70)
