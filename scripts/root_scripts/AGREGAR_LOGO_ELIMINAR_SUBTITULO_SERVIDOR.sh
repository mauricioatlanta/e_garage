#!/bin/bash
# Script para agrandar el logo y eliminar el subtítulo en selector_pais.html

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Agrandando logo y eliminando subtítulo en selector_pais.html..."

python3 << 'PYEOF'
file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Agrandar el logo principal (a 160px - el doble)
if 'height: 80px;' in content:
    content = content.replace('height: 80px;', 'height: 160px;')
    changes_made.append("✅ Logo principal agrandado (80px → 160px)")
elif 'height: 50px;' in content:
    content = content.replace('height: 50px;', 'height: 160px;')
    changes_made.append("✅ Logo principal agrandado (50px → 160px)")
else:
    changes_made.append("ℹ️  Logo principal ya está agrandado o tiene otro tamaño")

# 2. Agrandar el logo en responsive (a 120px - el doble)
if 'height: 60px;' in content and '.header-logo' in content:
    # Buscar específicamente en la sección responsive
    content = content.replace(
        '      .header-logo {\n        height: 60px;',
        '      .header-logo {\n        height: 120px;'
    )
    changes_made.append("✅ Logo responsive agrandado (60px → 120px)")
elif 'height: 40px;' in content and '.header-logo' in content:
    content = content.replace(
        '      .header-logo {\n        height: 40px;',
        '      .header-logo {\n        height: 120px;'
    )
    changes_made.append("✅ Logo responsive agrandado (40px → 120px)")
else:
    changes_made.append("ℹ️  Logo responsive ya está agrandado o tiene otro tamaño")

# 3. Mejorar el efecto de glow del logo
if 'filter: drop-shadow(0 0 30px rgba(0, 230, 255, 0.8));' in content:
    content = content.replace(
        'filter: drop-shadow(0 0 30px rgba(0, 230, 255, 0.8));',
        'filter: drop-shadow(0 0 40px rgba(0, 230, 255, 0.8));'
    )
    changes_made.append("✅ Efecto glow del logo mejorado")
elif 'filter: drop-shadow(0 0 20px rgba(0, 230, 255, 0.6));' in content:
    content = content.replace(
        'filter: drop-shadow(0 0 20px rgba(0, 230, 255, 0.6));',
        'filter: drop-shadow(0 0 40px rgba(0, 230, 255, 0.8));'
    )
    changes_made.append("✅ Efecto glow del logo mejorado")
else:
    changes_made.append("ℹ️  Efecto glow ya está actualizado")

# 4. Actualizar animación logoGlow
if 'filter: drop-shadow(0 0 20px rgba(0, 230, 255, 0.6));' in content and '@keyframes logoGlow' in content:
    content = content.replace(
        'filter: drop-shadow(0 0 20px rgba(0, 230, 255, 0.6));',
        'filter: drop-shadow(0 0 40px rgba(0, 230, 255, 0.8));'
    )
    if 'filter: drop-shadow(0 0 30px rgba(0, 230, 255, 0.9));' in content:
        content = content.replace(
            'filter: drop-shadow(0 0 30px rgba(0, 230, 255, 0.9));',
            'filter: drop-shadow(0 0 60px rgba(0, 230, 255, 1));'
        )
    changes_made.append("✅ Animación logoGlow actualizada")

# 4. Eliminar el subtítulo "Elige el país donde está tu taller"
if 'Elige el país donde está tu taller' in content:
    # Buscar y eliminar la línea completa
    import re
    # Patrón para encontrar la línea con el subtítulo
    pattern = r'<p class="subtitle">Elige el país donde está tu taller</p>\s*\n'
    content = re.sub(pattern, '', content)
    changes_made.append("✅ Subtítulo eliminado")
else:
    changes_made.append("ℹ️  Subtítulo ya está eliminado")

# Guardar cambios
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n".join(changes_made))
print("✅ Archivo actualizado")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "📋 Resumen de cambios:"
echo "  - Logo agrandado a 160px (el doble - responsive: 120px)"
echo "  - Efecto glow mejorado (40px)"
echo "  - Animación logoGlow actualizada"
echo "  - Subtítulo 'Elige el país donde está tu taller' eliminado"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"

