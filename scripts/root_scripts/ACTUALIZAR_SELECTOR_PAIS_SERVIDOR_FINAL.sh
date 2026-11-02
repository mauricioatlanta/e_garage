#!/bin/bash
# Script FINAL para actualizar selector_pais.html en el servidor
# Aplica: eliminar duplicado USA, mejorar botones, fondo animado, logo solo

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
from pathlib import Path
import re

file_path = 'templates/public/selector_pais.html'

print(f"📝 Actualizando {file_path}...\n")

if not Path(file_path).exists():
    print(f"❌ Error: {file_path} no existe")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Cambiar título
if 'eGarage - Selecciona tu país' in content:
    content = content.replace('eGarage - Selecciona tu país', 'eGarage')
    changes_made.append("✅ Título actualizado")

# 2. Eliminar texto del header (dejar solo logo)
if '<h1 class="header-title">eGarage</h1>' in content:
    content = content.replace('<h1 class="header-title">eGarage</h1>', '')
    changes_made.append("✅ Texto eliminado del header")

# 3. Eliminar duplicado de USA
usa_count = len(re.findall(r'href="/us/"', content))
if usa_count > 1:
    # Encontrar todas las ocurrencias de botones USA
    pattern = r'<a href="/us/" class="country-btn usa">.*?</a>'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    if len(matches) > 1:
        # Eliminar el segundo match
        second = matches[1]
        content = content[:second.start()] + content[second.end():]
        changes_made.append("✅ Duplicado USA eliminado")

# 4. Agregar fondo animado si no existe
if 'gridMove' not in content:
    # Buscar después de body {
    body_style_end = content.find('    }\n\n    /* Partículas')
    if body_style_end > 0:
        fondo_css = '''    }

    /* Fondo animado con gradiente y grid */
    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        linear-gradient(135deg, #0a0a23 0%, #1a1a2e 50%, #0f1419 100%),
        repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 230, 255, 0.03) 2px, rgba(0, 230, 255, 0.03) 4px),
        repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(0, 230, 255, 0.03) 2px, rgba(0, 230, 255, 0.03) 4px);
      background-size: 100% 100%, 50px 50px, 50px 50px;
      animation: gridMove 20s linear infinite;
      z-index: 0;
    }

    @keyframes gridMove {
      0% { background-position: 0 0, 0 0, 0 0; }
      100% { background-position: 0 0, 50px 50px, 50px 50px; }
    }

    body::after {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
        radial-gradient(circle at 20% 30%, rgba(0, 230, 255, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(0, 184, 212, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(0, 116, 217, 0.08) 0%, transparent 70%);
      animation: pulse 8s ease-in-out infinite;
      z-index: 0;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.8; transform: scale(1.1); }
    }

    /* Partículas de fondo animadas */
'''
        content = content[:body_style_end] + fondo_css + content[body_style_end+5:]
        changes_made.append("✅ Fondo animado agregado")

# 5. Actualizar partículas HTML a 6
particle_count = content.count('<div class="particle"></div>')
if particle_count < 6:
    particles_div = re.search(r'<div class="bg-particles">.*?</div>', content, re.DOTALL)
    if particles_div:
        new_particles = '''  <div class="bg-particles">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
  </div>'''
        content = content[:particles_div.start()] + new_particles + content[particles_div.end():]
        changes_made.append(f"✅ Partículas actualizadas ({particle_count} → 6)")

# 6. Mejorar efectos hover de botones
if 'inset 0 0 20px rgba(255, 255, 255, 0.1);' not in content:
    hover_pattern = r'\.country-btn:hover \{[^}]*\}'
    new_hover = '''.country-btn:hover {
      transform: translateY(-4px) scale(1.02);
      box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(0, 230, 255, 0.3),
        inset 0 0 20px rgba(255, 255, 255, 0.1);
      border-color: rgba(0, 230, 255, 0.6);
    }'''
    if re.search(hover_pattern, content, re.DOTALL):
        content = re.sub(hover_pattern, new_hover, content, flags=re.DOTALL)
        changes_made.append("✅ Efectos hover mejorados")

# Guardar
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

if changes_made:
    print("\n".join(changes_made))
    print(f"\n✅ Archivo {file_path} actualizado")
else:
    print("ℹ️  No se encontraron cambios necesarios")

PYEOF

touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

