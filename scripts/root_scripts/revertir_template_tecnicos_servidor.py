#!/usr/bin/env python
"""
Script para REVERTIR templates/taller/configuracion/tecnicos.html en el servidor
Vuelve a usar 'base.html' en lugar de 'common/base.html'
"""
import os
import shutil
import time

file_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/taller/configuracion/tecnicos.html"

print("=" * 70)
print("REVIRTIENDO templates/taller/configuracion/tecnicos.html")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Revertir a base.html
if "{% extends 'common/base.html' %}" in content:
    content = content.replace("{% extends 'common/base.html' %}", "{% extends 'base.html' %}")
    print("✅ Template base revertido a 'base.html'")
elif '{% extends "common/base.html" %}' in content:
    content = content.replace('{% extends "common/base.html" %}', "{% extends 'base.html' %}")
    print("✅ Template base revertido a 'base.html'")

# Eliminar {% load country_url %} si existe después de {% load static %}
if "{% load static %}\n{% load country_url %}" in content:
    content = content.replace("{% load static %}\n{% load country_url %}", "{% load static %}")
    print("✅ Eliminado {% load country_url %}")

# Escribir el archivo
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Archivo revertido: {file_path}")

# Verificar
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()
    if "{% extends 'base.html' %}" in check or '{% extends "base.html" %}' in check:
        print("✅ Verificación: Template ahora extiende 'base.html'")

print("\n⚠️  Reinicia el servidor: touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py")
print("=" * 70)
