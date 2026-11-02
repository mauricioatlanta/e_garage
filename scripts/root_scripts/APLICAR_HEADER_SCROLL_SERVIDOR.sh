#!/bin/bash
# Script para aplicar cambios en el header del selector de países
# - Header se oculta al hacer scroll hacia abajo
# - Logo queda como título de la página

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando cambios en selector_pais.html..."

# Backup
cp templates/public/selector_pais.html templates/public/selector_pais.html.backup_$(date +%Y%m%d_%H%M%S)

python3 << 'PYEOF'
import re

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Agregar clase 'hidden' al CSS del header
old_header_css = r'\.page-header \{[^}]*\}'
new_header_css = """    .page-header {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 100;
      padding: 2rem;
      background: rgba(10, 18, 40, 0.95);
      backdrop-filter: blur(30px);
      border-bottom: 2px solid rgba(0, 230, 255, 0.3);
      box-shadow: 0 8px 40px rgba(0, 0, 0, 0.6);
      transform: translateY(0);
      transition: transform 0.3s ease-in-out;
    }
    
    .page-header.hidden {
      transform: translateY(-100%);
    }"""

content = re.sub(
    r'/\* Header con logo[^*]*\*/[^{]*\.page-header \{[^}]*\}',
    new_header_css,
    content,
    flags=re.DOTALL
)

# Si no se reemplazó, buscar solo el bloque CSS
if 'transform: translateY(0)' not in content:
    # Buscar el bloque exacto
    pattern = r'(/\* Header con logo[^*]*\*/[^{]*\.page-header \{)[^}]*(padding: 2rem;)[^}]*(box-shadow: 0 8px 40px rgba\(0, 0, 0, 0\.6\);)\s*(\})'
    replacement = r'\1\n      transform: translateY(0);\n      transition: transform 0.3s ease-in-out;\n    }\n    \n    .page-header.hidden {\n      transform: translateY(-100%);\n    }'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 2. Cambiar padding del body (eliminar espacio para header fijo)
content = re.sub(
    r'body \{[^}]*padding: 200px 2rem 4rem;[^}]*\}',
    'body {\n      background: #0a0a23;\n      font-family: \'Orbitron\', \'Rajdhani\', sans-serif;\n      color: #fff;\n      min-height: 100vh;\n      position: relative;\n      padding: 2rem;\n    }',
    content,
    flags=re.DOTALL
)

# 3. Agregar id al header
content = re.sub(
    r'<header class="page-header">',
    '<header class="page-header" id="pageHeader">',
    content
)

# 4. Agregar script para ocultar/mostrar header al hacer scroll
if 'let lastScrollTop' not in content:
    script = """
  <script>
    // Ocultar header al hacer scroll hacia abajo, mostrarlo al hacer scroll hacia arriba
    let lastScrollTop = 0;
    const header = document.getElementById('pageHeader');
    
    window.addEventListener('scroll', function() {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      
      if (scrollTop > lastScrollTop && scrollTop > 100) {
        // Scrolling down - ocultar header
        header.classList.add('hidden');
      } else {
        // Scrolling up - mostrar header
        header.classList.remove('hidden');
      }
      
      lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    });
  </script>"""
    
    # Insertar antes de </body>
    content = content.replace('</body>', script + '\n</body>')

# 5. Ajustar padding en media queries
content = re.sub(
    r'@media \(max-width: 900px\) \{[^}]*padding: 180px 1\.5rem 3rem;[^}]*\}',
    '@media (max-width: 900px) {\n      body {\n        padding: 1.5rem;\n      }',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'@media \(max-width: 600px\) \{[^}]*padding: 160px 1rem 2rem;[^}]*\}',
    '@media (max-width: 600px) {\n      body {\n        padding: 1rem;\n      }',
    content,
    flags=re.DOTALL
)

# Guardar
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Cambios aplicados correctamente")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



