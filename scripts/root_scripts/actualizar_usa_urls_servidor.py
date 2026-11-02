#!/usr/bin/env python
"""
Script para actualizar taller/urls_extra/usa.py en el servidor
Hace que /us/en/settings/ use la misma vista que /us/settings/
"""
import os
import shutil
import time

file_path = (
    "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/taller/urls_extra/usa.py"
)

print("=" * 70)
print("ACTUALIZANDO taller/urls_extra/usa.py EN EL SERVIDOR")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Reemplazar futuristic_company_settings_view por company_settings_view en la ruta en/settings/
old_line = "        futuristic_company_settings_view,"
new_line = "        company_settings_view,  # Usar la misma vista que /us/settings/"

if old_line in content:
    content = content.replace(old_line, new_line)
    print("✅ Vista actualizada: /us/en/settings/ ahora usa company_settings_view")
else:
    # Buscar variantes
    if "futuristic_company_settings_view" in content:
        # Buscar la línea exacta con contexto
        lines = content.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            if "futuristic_company_settings_view" in line and "en/settings" in "\n".join(
                lines[max(0, i - 3) : i + 1]
            ):
                new_lines.append(new_line)
                print(f"✅ Vista actualizada en línea {i+1}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        print("⚠️  No se encontró futuristic_company_settings_view en el archivo")

# Escribir el archivo actualizado
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo actualizado: {file_path}")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()
    if "company_settings_view" in check and "en/settings" in check:
        if (
            "futuristic_company_settings_view" not in check
            or check.count("futuristic_company_settings_view") == 0
        ):
            print("✅ Verificación: /us/en/settings/ ahora usa company_settings_view")
        else:
            print("⚠️  Advertencia: Todavía hay referencias a futuristic_company_settings_view")
    else:
        print("⚠️  Advertencia: No se pudo verificar el cambio")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py")
print("=" * 70)
