#!/bin/bash
# Script para rediseñar completamente el selector de país con diseño futurista

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🎨 Rediseñando selector de país con diseño futurista..."

python3 << 'PYEOF'
import re

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

changes_made = []

# 1. Aumentar margin-top del selector-container (de 100px a 220px)
if 'margin-top: 100px;' in content:
    content = content.replace('margin-top: 100px;', 'margin-top: 220px;')
    changes_made.append("✅ Margin-top aumentado a 220px")
elif 'margin-top: 220px;' in content:
    changes_made.append("ℹ️  Margin-top ya está en 220px")
else:
    # Buscar y reemplazar cualquier margin-top menor
    content = re.sub(r'margin-top:\s*\d+px;', 'margin-top: 220px;', content)
    changes_made.append("✅ Margin-top actualizado a 220px")

# 2. Cambiar country-buttons a grid de 2 columnas
old_buttons = '''    .country-buttons {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-bottom: 1rem;
    }'''

new_buttons = '''    .country-buttons {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1.2rem;
      margin-bottom: 1.5rem;
    }
    
    @media (max-width: 768px) {
      .country-buttons {
        grid-template-columns: 1fr;
        gap: 1rem;
      }
    }'''

if old_buttons in content:
    content = content.replace(old_buttons, new_buttons)
    changes_made.append("✅ Botones cambiados a grid de 2 columnas")
elif 'grid-template-columns: repeat(2, 1fr);' in content:
    changes_made.append("ℹ️  Botones ya están en grid")
else:
    # Buscar patrón más flexible
    if 'display: flex;' in content and 'flex-direction: column;' in content:
        content = re.sub(
            r'\.country-buttons\s*\{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;[^}]*\}',
            new_buttons,
            content,
            flags=re.DOTALL
        )
        changes_made.append("✅ Botones cambiados a grid (patrón flexible)")

# 3. Mejorar estilos de country-btn
if 'min-height: 75px;' in content:
    content = content.replace('min-height: 75px;', 'min-height: 85px;')
    changes_made.append("✅ Altura mínima de botones aumentada")

if 'border-radius: 16px;' in content and '.country-btn' in content:
    # Reemplazar border-radius en country-btn
    content = re.sub(
        r'(\.country-btn\s*\{[^}]*?)border-radius:\s*16px;',
        r'\1border-radius: 20px;',
        content,
        flags=re.DOTALL
    )
    changes_made.append("✅ Border-radius aumentado a 20px")

# 4. Mejorar efectos hover
if 'transform: translateY(-4px) scale(1.02);' in content and '.country-btn:hover' in content:
    content = content.replace(
        'transform: translateY(-4px) scale(1.02);',
        'transform: translateY(-6px) scale(1.03);'
    )
    changes_made.append("✅ Efecto hover mejorado")

# 5. Actualizar media queries
if 'margin-top: 80px;' in content and '@media' in content:
    # Buscar en media queries
    content = re.sub(
        r'(@media[^{]*\{[^}]*\.selector-container[^}]*margin-top:\s*)80px;',
        r'\1180px;',
        content,
        flags=re.DOTALL
    )
    changes_made.append("✅ Media queries actualizadas")

# 6. Mejorar efectos de flag y country-name
if 'font-size: 2.8rem;' in content and '.flag' in content:
    content = content.replace('font-size: 2.8rem;', 'font-size: 3.2rem;')
    changes_made.append("✅ Tamaño de flag aumentado")

# Guardar cambios
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n".join(changes_made))
print("✅ Archivo actualizado")
PYEOF

echo ""
echo "✅✅✅ Rediseño aplicado ✅✅✅"
echo ""
echo "📋 Resumen de cambios:"
echo "  - Margin-top aumentado a 220px (para que los botones no queden ocultos)"
echo "  - Botones en grid de 2 columnas (mejor distribución)"
echo "  - Botones más grandes y futuristas (85px altura mínima)"
echo "  - Efectos hover mejorados (más pronunciados)"
echo "  - Diseño responsive mejorado"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



