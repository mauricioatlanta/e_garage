#!/bin/bash
# Script para agregar el botón "Add Vehicle" en la lista de vehículos US

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
from pathlib import Path
import re

file_path = 'templates/taller/us/en/vehiculos/lista_vehiculos.html'

print(f"📝 Agregando botón 'Add Vehicle' en {file_path}...\n")

if not Path(file_path).exists():
    print(f"❌ Error: {file_path} no existe")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la sección de búsqueda y filtros
search_pattern = r'<!-- Search and Filter Section -->'
search_match = re.search(search_pattern, content)

if not search_match:
    print("❌ No se encontró la sección 'Search and Filter Section'")
    exit(1)

# Verificar si ya existe el header con el botón
if 'Header with Add Button' in content:
    print("ℹ️  El botón 'Add Vehicle' ya existe en la template")
    exit(0)

# Nuevo header con botón
new_header = '''<!-- Header with Add Button -->
<div class="mb-6">
    <div class="glass-card p-4">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-300 via-lime-300 to-green-400">
                    {% trans "Vehicle Fleet" %}
                </h1>
                <p class="text-gray-400 text-xs mt-0.5">{% trans "Manage your vehicle fleet" %}</p>
            </div>
            {% country_url 'vehiculos:crear_vehiculo' as url_crear_vehiculo %}
            <a href="{{ url_crear_vehiculo }}"
               class="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600/20 to-green-600/20 border border-emerald-400/40 text-emerald-300 hover:from-emerald-500/30 hover:to-green-500/30 hover:text-emerald-200 transition-all duration-300"
               aria-label="{% trans 'Add new vehicle' %}">
                <span>➕</span>
                <span class="hidden sm:inline">{% trans "Add Vehicle" %}</span>
            </a>
        </div>
    </div>
</div>

<!-- Search and Filter Section -->'''

# Reemplazar la sección de búsqueda
content = content[:search_match.start()] + new_header + content[search_match.end():]

# Guardar el archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Botón 'Add Vehicle' agregado con éxito")
print("   - Header con título y descripción")
print("   - Botón con estilo futurista")
print("   - URL generada con country_url tag")

PYEOF

touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

