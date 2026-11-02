#!/usr/bin/env python
"""
Script para actualizar taller/views_extra/views_configuracion.py en el servidor
Actualiza los decoradores @login_required para usar login_url=None
"""
import os
import shutil
import time

file_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/taller/views_extra/views_configuracion.py"

print("=" * 70)
print("ACTUALIZANDO taller/views_extra/views_configuracion.py EN EL SERVIDOR")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Cambio 1: Actualizar decorador de configuracion_empresa
old_decorator1 = "@login_required\ndef configuracion_empresa(request):"
new_decorator1 = (
    "@login_required(login_url=None)  # Usa LOGIN_URL global\ndef configuracion_empresa(request):"
)

if old_decorator1 in content:
    content = content.replace(old_decorator1, new_decorator1)
    print("✅ Cambio 1: Decorador de configuracion_empresa actualizado")
else:
    # Buscar variantes
    if "@login_required" in content and "def configuracion_empresa" in content:
        lines = content.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            if (
                "@login_required" in line
                and i + 1 < len(lines)
                and "def configuracion_empresa" in lines[i + 1]
            ):
                new_lines.append("@login_required(login_url=None)  # Usa LOGIN_URL global")
                print(f"✅ Cambio 1: Decorador actualizado en línea {i+1}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)

# Cambio 2: Actualizar decorador de configuracion_tecnicos
old_decorator2 = "@login_required\ndef configuracion_tecnicos(request):"
new_decorator2 = (
    "@login_required(login_url=None)  # Usa LOGIN_URL global\ndef configuracion_tecnicos(request):"
)

if old_decorator2 in content:
    content = content.replace(old_decorator2, new_decorator2)
    print("✅ Cambio 2: Decorador de configuracion_tecnicos actualizado")
else:
    # Buscar variantes
    if "@login_required" in content and "def configuracion_tecnicos" in content:
        lines = content.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            if (
                "@login_required" in line
                and i + 1 < len(lines)
                and "def configuracion_tecnicos" in lines[i + 1]
            ):
                new_lines.append("@login_required(login_url=None)  # Usa LOGIN_URL global")
                print(f"✅ Cambio 2: Decorador actualizado en línea {i+1}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)

# Cambio 3: Eliminar import redundante de redirect dentro de la función
if "from django.shortcuts import redirect" in content:
    # Buscar dentro de la función configuracion_tecnicos
    func_start = content.find("def configuracion_tecnicos")
    if func_start != -1:
        func_content = content[func_start:]
        if "from django.shortcuts import redirect" in func_content:
            # Eliminar la línea
            lines = content.split("\n")
            new_lines = []
            for i, line in enumerate(lines):
                if (
                    "from django.shortcuts import redirect" in line and i > func_start // 80
                ):  # Aproximadamente después del inicio de la función
                    context = "\n".join(lines[max(0, i - 3) : i + 3])
                    if "Redirección dinámica" in context or "configuracion_tecnicos" in context:
                        print(f"✅ Cambio 3: Eliminando import redundante en línea {i+1}")
                        continue
                new_lines.append(line)
            content = "\n".join(new_lines)

# Escribir el archivo actualizado
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo actualizado: {file_path}")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()
    if "@login_required(login_url=None)" in check:
        print("✅ Verificación: Decoradores actualizados correctamente")
    if (
        "from django.shortcuts import redirect"
        not in check[
            check.find("def configuracion_tecnicos") : check.find("def configuracion_tecnicos")
            + 5000
        ]
    ):
        print("✅ Verificación: No hay imports redundantes dentro de la función")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py")
print("=" * 70)
