#!/usr/bin/env python
"""
Script para actualizar base.html en el servidor
Elimina el emoji del edificio y cambia el color del título a blanco
"""
import os
import shutil
import time

file_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/base.html"

print("=" * 70)
print("ACTUALIZANDO base.html EN EL SERVIDOR")
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
old_css = ".company-title{color:var(--company-primary);text-shadow:0 0 20px var(--company-primary),0 0 40px var(--company-primary);filter:drop-shadow(0 4px 8px rgba(0,0,0,.3))}"
new_css = ".company-title{color:#ffffff !important;text-shadow:0 0 10px rgba(255,255,255,0.5);filter:drop-shadow(0 4px 8px rgba(0,0,0,.3))}"

if old_css in content:
    content = content.replace(old_css, new_css)
    print("✅ Cambio 1: Color del título cambiado a blanco")
elif new_css in content:
    print("✅ Cambio 1: El color ya está en blanco")
else:
    print("⚠️  Cambio 1: No se encontró el CSS exacto, buscando variantes...")
    # Buscar y reemplazar cualquier variante
    import re

    pattern = r"\.company-title\{[^}]+\}"
    if re.search(pattern, content):
        content = re.sub(pattern, new_css, content)
        print("✅ Cambio 1: Color del título actualizado (usando regex)")

# Cambio 2: Eliminar el emoji del edificio (el div completo cuando no hay logo)
old_div = """    {% else %}
      <div class="company-logo h-20 w-20 rounded-lg flex items-center justify-center shadow-lg border-2 border-opacity-30"
           style="background: linear-gradient(135deg, {{ company_color|default:'#00ffff' }}80, {{ company_color|default:'#00ffff' }}40); border-color: {{ company_color|default:'#00ffff' }};">
        <span class="text-3xl font-bold text-white">🏢</span>
      </div>
    {% endif %}"""

if old_div in content:
    content = content.replace(old_div, "    {% endif %}")
    print("✅ Cambio 2: Emoji del edificio eliminado")
else:
    # Buscar variantes
    if "🏢" in content:
        # Buscar el bloque completo que contiene el emoji
        lines = content.split("\n")
        new_lines = []
        skip_next = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            if "🏢" in line:
                # Encontrar el inicio del bloque {% else %}
                start_idx = i
                # Retroceder para encontrar el {% else %}
                for j in range(i, max(0, i - 10), -1):
                    if "{% else %}" in lines[j]:
                        start_idx = j
                        break
                # Encontrar el final del bloque {% endif %}
                end_idx = i
                for j in range(i, min(len(lines), i + 10)):
                    if "{% endif %}" in lines[j]:
                        end_idx = j
                        break
                # Eliminar todas las líneas del bloque excepto el {% endif %}
                for j in range(start_idx, end_idx):
                    if j < len(lines):
                        lines[j] = None
                lines[end_idx] = "    {% endif %}"
                print(
                    f"✅ Cambio 2: Emoji del edificio eliminado (líneas {start_idx+1}-{end_idx+1})"
                )
            else:
                new_lines.append(line)
        content = "\n".join([l for l in lines if l is not None])
    else:
        print("✅ Cambio 2: El emoji ya fue eliminado o no existe")

# Escribir el archivo actualizado
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo actualizado: {file_path}")
print(f"✅ Tamaño: {len(content)} caracteres")

# Verificar los cambios
with open(file_path, "r", encoding="utf-8") as f:
    content_check = f.read()
    if "color:#ffffff" in content_check or "color: #ffffff" in content_check:
        print("✅ Verificación: Color blanco encontrado en el CSS")
    if "🏢" not in content_check:
        print("✅ Verificación: Emoji del edificio no encontrado (eliminado)")
    else:
        print("⚠️  Advertencia: El emoji aún existe en el archivo")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py")
print("=" * 70)
