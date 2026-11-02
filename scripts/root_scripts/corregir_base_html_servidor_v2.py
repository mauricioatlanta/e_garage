#!/usr/bin/env python
"""
Script para corregir la estructura rota de templates/common/base.html en el servidor
Reemplaza la sección del header con la versión correcta
"""
import os
import shutil
import time
import re

file_path = (
    "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/common/base.html"
)

print("=" * 70)
print("CORRIGIENDO templates/common/base.html EN EL SERVIDOR")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Sección correcta del header (sin flor azul, sin emoji, con título blanco)
correct_header_section = """<!-- Header y navegación unificados (ahora con branding dinámico) -->
{% if request.path != "/cl/" and request.path != "/us/" %}
<header class="company-header flex items-center gap-6 p-6">
  {% if company_logo_url or COMPANY_LOGO %}
    {% if '/static/images/' not in company_logo_url|default:COMPANY_LOGO %}
    <img src="{{ company_logo_url|default:COMPANY_LOGO }}"
         alt="{{ company_name|default:COMPANY_NAME|default:'eGarage' }} Logo"
         class="company-logo h-20 w-auto rounded-lg shadow-lg border-2 border-opacity-30"
         style="border-color: {{ primary_color|default:'#00ffff' }}; max-width: 200px; object-fit: contain;">
    {% endif %}
  {% endif %}

  <div class="flex flex-col">
    <h1 class="company-title text-4xl font-bold drop-shadow-lg">
      {{ company_name|default:COMPANY_NAME|default:"eGarage" }}
    </h1>
    {% if company_tagline or COMPANY_TAGLINE %}
      <span class="text-xl text-gray-300 font-medium mt-1">{{ company_tagline|default:COMPANY_TAGLINE }}</span>
    {% elif request.user.is_authenticated %}
      <span class="text-xl text-gray-300 font-medium mt-1">
        {% if LANGUAGE_CODE == 'es' %}Sistema de Gestión de Talleres{% else %}Workshop Management System{% endif %}
      </span>
    {% endif %}
  </div>"""

# Buscar y reemplazar la sección problemática
# Buscar desde el comentario "Header y navegación" hasta el cierre del div "flex flex-col"
pattern = r'<!-- Header y navegación unificados[^<]*?<header class="company-header[^<]*?</header>'
# Patrón más específico
pattern2 = r"<!-- Header y navegación unificados.*?</div>\s*</header>"

# Intentar encontrar la sección completa
match = re.search(
    r'<!-- Header y navegación unificados.*?<div class="flex flex-col">.*?</div>\s*</header>',
    content,
    re.DOTALL,
)

if match:
    # Reemplazar la sección encontrada
    start_pos = match.start()
    end_pos = match.end()

    # Encontrar dónde termina realmente el header (buscar el siguiente bloque después del header)
    # Buscar el cierre del header y el siguiente elemento
    after_match = content[end_pos : end_pos + 200]

    # Construir la sección correcta
    new_section = correct_header_section + "\n"

    # Reemplazar
    content = content[:start_pos] + new_section + content[end_pos:]
    print("✅ Sección del header reemplazada")
else:
    # Si no se encuentra con el patrón, buscar manualmente
    # Buscar el inicio del comentario
    start_marker = "<!-- Header y navegación unificados"
    start_idx = content.find(start_marker)

    if start_idx != -1:
        # Buscar el cierre del header (buscar </header> después de encontrar el div flex-col)
        # Buscar el div flex-col dentro del header
        div_pattern = r'<div class="flex flex-col">.*?</div>'
        div_match = re.search(div_pattern, content[start_idx:], re.DOTALL)

        if div_match:
            # Encontrar el </header> después del div
            header_end = content.find("</header>", start_idx + div_match.end())
            if header_end != -1:
                header_end += len("</header>")
                # Reemplazar
                content = content[:start_idx] + correct_header_section + "\n" + content[header_end:]
                print("✅ Sección del header reemplazada (método alternativo)")
            else:
                print("⚠️  No se encontró el cierre del header")
        else:
            print("⚠️  No se encontró el div flex-col")
    else:
        print("⚠️  No se encontró el marcador de inicio")

# También asegurarse de que el CSS del título sea blanco
if "color: var(--company-primary)" in content and "company-title" in content:
    # Reemplazar el CSS del título
    old_css_pattern = r"\.company-title\s*\{[^}]+\}"
    new_css = """.company-title {
      color: #ffffff !important;
      text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
      filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
    }"""
    content = re.sub(old_css_pattern, new_css, content, flags=re.MULTILINE | re.DOTALL)
    print("✅ CSS del título actualizado a blanco")

# Eliminar cualquier referencia a la flor azul o emoji del edificio que pueda quedar
if "🌼 AZUL" in content:
    content = content.replace("🌼 AZUL", "")
    content = re.sub(r"<div[^>]*>🌼 AZUL</div>", "", content)
    print("✅ Flor azul eliminada")

if "🏢" in content and "company-logo" in content:
    # Buscar y eliminar bloques con el emoji del edificio
    emoji_pattern = r"<div[^>]*company-logo[^>]*>.*?🏢.*?</div>"
    content = re.sub(emoji_pattern, "", content, flags=re.DOTALL)
    print("✅ Emoji del edificio eliminado")

# Escribir el archivo corregido
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ Archivo corregido: {file_path}")
print(f"✅ Tamaño: {len(content)} caracteres")

# Verificar la estructura
with open(file_path, "r", encoding="utf-8") as f:
    check = f.read()

    # Verificar que no haya ifs sin cerrar
    if_count = check.count("{% if company_logo_url or COMPANY_LOGO %}")
    endif_count = check.count("{% endif %}")

    if if_count <= endif_count:
        print("✅ Verificación: Estructura de if/endif parece correcta")
    else:
        print(f"⚠️  Advertencia: {if_count} if(s) pero solo {endif_count} endif(s)")

    if "🌼 AZUL" not in check:
        print("✅ Verificación: Flor azul no encontrada")
    if "color: #ffffff" in check or "color:#ffffff" in check:
        print("✅ Verificación: Color blanco encontrado en CSS")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py")
print("=" * 70)
