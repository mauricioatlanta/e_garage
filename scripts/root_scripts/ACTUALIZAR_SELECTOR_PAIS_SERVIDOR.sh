#!/bin/bash
# Script para actualizar selector_pais.html en el servidor con todos los cambios

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
from pathlib import Path

file_path = 'templates/public/selector_pais.html'

print(f"📝 Actualizando {file_path} con todos los cambios...\n")

if not Path(file_path).exists():
    print(f"❌ Error: {file_path} no existe")
    exit(1)

# Leer el contenido actual
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Cambiar título
if '<title>eGarage - Selecciona tu país</title>' in content:
    content = content.replace(
        '<title>eGarage - Selecciona tu país</title>',
        '<title>eGarage</title>'
    )
    changes_made.append("✅ Título actualizado")

# 2. Eliminar texto "eGarage" del header (dejar solo logo)
if '<h1 class="header-title">eGarage</h1>' in content:
    content = content.replace(
        '      <img src="{% static \'img/egarage_logo.png\' %}" alt="eGarage" class="header-logo">\n      <h1 class="header-title">eGarage</h1>',
        '      <img src="{% static \'img/egarage_logo.png\' %}" alt="eGarage" class="header-logo">'
    )
    changes_made.append("✅ Texto 'eGarage' eliminado del header (solo logo)")

# 3. Eliminar duplicado de USA - buscar si hay dos entradas de USA
usa_count = content.count('href="/us/"')
if usa_count > 1:
    # Encontrar y eliminar el segundo USA
    # Buscar el patrón completo del botón USA
    import re
    usa_pattern = r'<a href="/us/" class="country-btn usa">.*?</a>'
    matches = list(re.finditer(usa_pattern, content, re.DOTALL))
    if len(matches) > 1:
        # Eliminar el segundo match
        second_match = matches[1]
        content = content[:second_match.start()] + content[second_match.end():]
        changes_made.append("✅ Duplicado de USA eliminado")
else:
    print("ℹ️  Solo hay una entrada de USA (correcto)")

# 4. Verificar si el fondo animado ya está implementado
if 'body::before' not in content or 'gridMove' not in content:
    # Agregar fondo animado después de la definición de body
    body_end = content.find('    }\n\n    /* Partículas de fondo */')
    if body_end > 0:
        fondo_animado = '''
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
'''
        content = content[:body_end] + fondo_animado + content[body_end:]
        changes_made.append("✅ Fondo animado agregado")
    else:
        print("⚠️  No se pudo encontrar el lugar para agregar el fondo animado")

# 5. Mejorar partículas de fondo
if '.particle:nth-child(4)' in content and '.particle:nth-child(5)' not in content:
    # Reemplazar la sección de partículas
    particle_section = '''    /* Partículas de fondo animadas */
    .bg-particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
      overflow: hidden;
      pointer-events: none;
    }
    .particle {
      position: absolute;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(0, 230, 255, 0.4) 0%, transparent 70%);
      animation: float 15s infinite ease-in-out;
      box-shadow: 0 0 20px rgba(0, 230, 255, 0.5);
    }
    .particle:nth-child(1) { width: 120px; height: 120px; left: 10%; top: 20%; animation-delay: 0s; }
    .particle:nth-child(2) { width: 90px; height: 90px; left: 80%; top: 30%; animation-delay: 2s; }
    .particle:nth-child(3) { width: 150px; height: 150px; left: 50%; top: 60%; animation-delay: 4s; }
    .particle:nth-child(4) { width: 100px; height: 100px; left: 20%; top: 80%; animation-delay: 6s; }
    .particle:nth-child(5) { width: 80px; height: 80px; left: 70%; top: 10%; animation-delay: 8s; }
    .particle:nth-child(6) { width: 110px; height: 110px; left: 30%; top: 50%; animation-delay: 10s; }
    @keyframes float {
      0%, 100% { transform: translateY(0) translateX(0) scale(1); opacity: 0.4; }
      25% { transform: translateY(-40px) translateX(20px) scale(1.1); opacity: 0.6; }
      50% { transform: translateY(-60px) translateX(-30px) scale(0.9); opacity: 0.5; }
      75% { transform: translateY(-20px) translateX(40px) scale(1.05); opacity: 0.7; }
    }'''
    
    # Buscar y reemplazar la sección de partículas
    import re
    old_particle_pattern = r'/\* Partículas de fondo.*?@keyframes float.*?\n    \}'
    if re.search(old_particle_pattern, content, re.DOTALL):
        content = re.sub(old_particle_pattern, particle_section, content, flags=re.DOTALL)
        changes_made.append("✅ Partículas de fondo mejoradas")
    else:
        print("ℹ️  Partículas ya pueden estar actualizadas")

# 6. Mejorar estilos de botones (agregar efectos más futuristas)
if 'box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);' not in content:
    # Mejorar el hover de los botones
    content = content.replace(
        '.country-btn:hover {',
        '.country-btn:hover {\n      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 230, 255, 0.3);'
    )
    changes_made.append("✅ Efectos hover mejorados en botones")

# Actualizar partículas en el HTML
if content.count('<div class="particle"></div>') < 6:
    # Buscar el div bg-particles y actualizar
    import re
    particles_div_pattern = r'(<div class="bg-particles">.*?</div>)'
    new_particles = '''  <div class="bg-particles">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
  </div>'''
    if re.search(particles_div_pattern, content, re.DOTALL):
        content = re.sub(particles_div_pattern, new_particles, content, flags=re.DOTALL)
        changes_made.append("✅ Partículas HTML actualizadas (6 partículas)")

# Guardar
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

if changes_made:
    print("\n".join(changes_made))
    print(f"\n✅ Archivo {file_path} actualizado correctamente")
else:
    print("ℹ️  No se encontraron cambios necesarios (puede que ya estén aplicados)")

PYEOF

touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"
echo ""
echo "🎉 ¡Selector de países actualizado!"

