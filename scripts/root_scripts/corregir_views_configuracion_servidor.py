#!/usr/bin/env python
"""
Script para corregir taller/views_extra/views_configuracion.py en el servidor
Elimina el import redundante de redirect que causa UnboundLocalError
"""
import os
import shutil
import time

file_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/taller/views_extra/views_configuracion.py"

print("=" * 70)
print("CORRIGIENDO taller/views_extra/views_configuracion.py")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Cambio 1: Eliminar el import redundante de redirect dentro de la función
old_import = """        # Redirección dinámica basada en el país del usuario
        from django.shortcuts import redirect

        if hasattr(request.user, "empresa") and request.user.empresa.pais == "US":"""
new_code = """        # Redirección dinámica basada en el país del usuario
        if hasattr(request.user, "empresa") and request.user.empresa.pais == "US":"""

if old_import in content:
    content = content.replace(old_import, new_code)
    print("✅ Cambio 1: Import redundante de redirect eliminado")
else:
    # Buscar variantes
    if "from django.shortcuts import redirect" in content:
        lines = content.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            if (
                "from django.shortcuts import redirect" in line and i > 200
            ):  # Solo dentro de la función
                # Verificar contexto
                context = "\n".join(lines[max(0, i - 2) : i + 3])
                if "Redirección dinámica" in context or "configuracion_tecnicos" in context:
                    print(f"✅ Cambio 1: Eliminando import redundante en línea {i+1}")
                    continue  # Saltar esta línea
            new_lines.append(line)
        content = "\n".join(new_lines)
        print("✅ Cambio 1: Import redundante eliminado (método alternativo)")

# Cambio 2: Agregar return redirect en casos de error de validación
# Buscar el bloque de validación y agregar returns donde falten
validation_patterns = [
    (
        'if not tecnico:\n                messages.error(request, "❌ Técnico no encontrado.")',
        'if not tecnico:\n                messages.error(request, "❌ Técnico no encontrado.")\n                return redirect("configuracion_tecnicos")',
    ),
    (
        'elif not nuevo_nombre or len(nuevo_nombre) < 2:\n                messages.error(request, "❌ El nombre debe tener al menos 2 caracteres.")',
        'elif not nuevo_nombre or len(nuevo_nombre) < 2:\n                messages.error(request, "❌ El nombre debe tener al menos 2 caracteres.")\n                return redirect("configuracion_tecnicos")',
    ),
]

for old_pattern, new_pattern in validation_patterns:
    if old_pattern in content and new_pattern not in content:
        content = content.replace(old_pattern, new_pattern)
        print(f"✅ Cambio 2: Agregado return redirect en validación")

# Cambio 3: Actualizar redirección al final para usar namespace
old_redirect = 'return redirect("/us/configuracion/tecnicos/")'
new_redirect = 'return redirect("usa:configuracion_tecnicos")'

if old_redirect in content:
    content = content.replace(old_redirect, new_redirect)
    print("✅ Cambio 3: Redirección actualizada para usar namespace")

# Escribir el archivo corregido
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo corregido: {file_path}")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()
    if (
        "from django.shortcuts import redirect"
        not in check[check.find("def configuracion_tecnicos") :]
    ):
        print("✅ Verificación: No hay imports redundantes dentro de la función")
    else:
        print("⚠️  Advertencia: Puede haber imports redundantes")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py")
print("=" * 70)
