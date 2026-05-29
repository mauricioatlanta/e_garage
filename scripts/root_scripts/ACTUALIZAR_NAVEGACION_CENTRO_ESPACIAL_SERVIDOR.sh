#!/bin/bash
# Script para actualizar la navegación en centro_operaciones_espacial.html
# Aplica los mismos estilos de botones que en la página de clientes

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
from pathlib import Path
import re

file_path = 'templates/taller/us/en/dashboard/centro_operaciones_espacial.html'

print(f"📝 Actualizando navegación en {file_path}...\n")

if not Path(file_path).exists():
    print(f"❌ Error: {file_path} no existe")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la sección de navegación actual
nav_pattern = r'<!-- Navigation horizontal.*?</nav>'
nav_match = re.search(nav_pattern, content, re.DOTALL)

if not nav_match:
    print("❌ No se encontró la sección de navegación")
    exit(1)

# Nueva sección de navegación con los mismos estilos que base.html
new_nav = '''<!-- Navigation horizontal - ORDEN ALFABÉTICO -->
<nav class="w-full bg-black/80 backdrop-blur-xl border-b-2 border-white/30 shadow-lg py-4 px-6 z-50 relative" style="box-shadow: 0 0 20px rgba(255, 255, 255, 0.2), 0 4px 15px rgba(0, 0, 0, 0.5);">
  <div class="flex flex-col items-center justify-center gap-3">
    {% if request.user.is_authenticated %}
      <!-- Fila 1: CENTER, CLIENTS, DOCUMENTS, SETTINGS -->
      <div class="flex items-center justify-center gap-3 flex-wrap" style="white-space: nowrap;">
        <a href="/us/centro-operaciones-espacial/" class="nav-button-standard">
          <span class="nav-icon">🚀</span>
          <span>{% trans "CENTER" %}</span>
        </a>
        <a href="/us/clientes/" class="nav-button-standard">
          <span class="nav-icon">👥</span>
          <span>{% trans "CLIENTS" %}</span>
        </a>
        <a href="/us/documentos/" class="nav-button-standard">
          <span class="nav-icon">📄</span>
          <span>{% trans "DOCUMENTS" %}</span>
        </a>
        <a href="/us/en/settings/" class="nav-button-standard">
          <span class="nav-icon">⚙️</span>
          <span>{% trans "SETTINGS" %}</span>
        </a>
      </div>

      <!-- Fila 2: PARTS, REPORTS, SERVICES, VEHICLES, LOGOUT -->
      <div class="flex items-center justify-center gap-3 flex-wrap" style="white-space: nowrap;">
        <a href="/us/repuestos/" class="nav-button-standard">
          <span class="nav-icon">🔧</span>
          <span>{% trans "PARTS" %}</span>
        </a>
        <a href="/us/reportes/" class="nav-button-standard">
          <span class="nav-icon">📊</span>
          <span>{% trans "REPORTS" %}</span>
        </a>
        <a href="/us/servicios/" class="nav-button-standard">
          <span class="nav-icon">🛠️</span>
          <span>{% trans "SERVICES" %}</span>
        </a>
        <a href="/us/vehiculos/" class="nav-button-standard">
          <span class="nav-icon">🚗</span>
          <span>{% trans "VEHICLES" %}</span>
        </a>
        <form action="/accounts/logout/" method="post" style="display: inline;">
          {% csrf_token %}
          <button type="submit" class="nav-button-standard logout-btn" style="cursor: pointer;">
            <span class="nav-icon">🚪</span>
            <span>{% trans "LOGOUT" %}</span>
          </button>
        </form>
      </div>
    {% endif %}
  </div>
</nav>'''

# Reemplazar la sección de navegación
content = content[:nav_match.start()] + new_nav + content[nav_match.end():]

# Guardar el archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Navegación actualizada con éxito")
print("   - Contenedor con mismos estilos que base.html")
print("   - Botones organizados en dos filas alfabéticamente")
print("   - Mismos estilos CSS nav-button-standard")

PYEOF

touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

