#!/bin/bash
# Script completo para corregir selector_pais.html en el servidor
# Detecta y corrige CSS suelto, falta de etiquetas <style>, etc.

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/public/selector_pais.html"

echo "📋 Creando backup completo..."
cp "$FILE" "$FILE.backup_completo_$(date +%Y%m%d_%H%M%S)"

echo "🔍 Analizando archivo..."

python3 << 'PYEOF'
import sys
import re

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

print(f"📄 Archivo tiene {len(lines)} líneas")

# Detectar problemas
problems = []

# 1. Buscar CSS suelto (sin etiquetas <style>)
css_pattern = re.compile(r'^[a-zA-Z0-9_#\.\-\s]+\{[^}]+\}')
css_suelto = []

for i, line in enumerate(lines):
    stripped = line.strip()
    # CSS suelto: tiene patrón CSS pero no está en etiqueta style
    if css_pattern.search(stripped) and '<style' not in line and '</style>' not in line and stripped:
        css_suelto.append((i, line.strip()[:60]))

if css_suelto:
    print(f"⚠️  Se encontraron {len(css_suelto)} líneas de CSS suelto:")
    for line_num, line_content in css_suelto[:5]:
        print(f"   Línea {line_num+1}: {line_content}...")
    problems.append("CSS suelto sin etiquetas <style>")

# 2. Verificar estructura de <style>
has_style_open = '<style>' in content or '<style ' in content
has_style_close = '</style>' in content

if not has_style_open:
    problems.append("Falta etiqueta <style>")
    print("⚠️  No se encontró etiqueta <style>")
elif not has_style_close:
    problems.append("Falta etiqueta </style>")
    print("⚠️  No se encontró etiqueta </style>")

# 3. Verificar ubicación de </style>
if has_style_open and has_style_close:
    style_pos = content.find('<style>')
    if style_pos == -1:
        style_pos = content.find('<style ')
    style_close_pos = content.find('</style>')
    head_close_pos = content.find('</head>')
    
    if style_close_pos > head_close_pos and head_close_pos != -1:
        problems.append("</style> está después de </head>")
        print("⚠️  </style> está después de </head>")

# Si hay problemas, corregirlos
if problems:
    print(f"\n🔧 Corrigiendo {len(problems)} problema(s)...")
    
    # Estrategia: reconstruir el archivo correctamente
    new_lines = []
    in_style = False
    css_collected = []
    in_head = False
    
    for i, line in enumerate(lines):
        # Detectar <head>
        if '<head>' in line or '<head ' in line:
            in_head = True
            new_lines.append(line)
            continue
        
        # Detectar </head>
        if '</head>' in line:
            # Si hay CSS recolectado, agregarlo antes de </head>
            if css_collected:
                new_lines.append('  <style>\n')
                new_lines.extend(css_collected)
                new_lines.append('  </style>\n')
                css_collected = []
            in_head = False
            new_lines.append(line)
            continue
        
        # Detectar <style>
        if '<style>' in line or '<style ' in line:
            in_style = True
            new_lines.append(line)
            continue
        
        # Detectar </style>
        if '</style>' in line:
            in_style = False
            new_lines.append(line)
            continue
        
        # Si estamos en head y encontramos CSS suelto, recolectarlo
        if in_head and not in_style:
            stripped = line.strip()
            if css_pattern.search(stripped) or (stripped and '{' in stripped and '}' in stripped):
                css_collected.append(line)
                continue  # No agregar esta línea todavía
        
        # Línea normal
        new_lines.append(line)
    
    # Si quedó CSS recolectado al final, agregarlo
    if css_collected:
        # Buscar </head> en las nuevas líneas
        for i, line in enumerate(new_lines):
            if '</head>' in line:
                new_lines.insert(i, '  <style>\n')
                new_lines.insert(i+1, *css_collected)
                new_lines.insert(i+1+len(css_collected), '  </style>\n')
                break
    
    # Escribir archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Archivo corregido")
    
    # Verificar corrección
    with open(file_path, 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    # Verificar que no quede CSS suelto
    new_css_suelto = []
    for i, line in enumerate(new_content.splitlines()):
        stripped = line.strip()
        if css_pattern.search(stripped) and '<style' not in line and '</style>' not in line and stripped:
            new_css_suelto.append(i+1)
    
    if new_css_suelto:
        print(f"⚠️  Aún hay CSS suelto en líneas: {new_css_suelto[:5]}")
    else:
        print("✅ No queda CSS suelto")
    
    # Verificar estructura final
    if '<style>' in new_content and '</style>' in new_content:
        final_style_pos = new_content.find('<style>')
        final_style_close_pos = new_content.find('</style>')
        final_head_close_pos = new_content.find('</head>')
        
        if final_style_pos < final_style_close_pos < final_head_close_pos:
            print("✅ Estructura final correcta")
        else:
            print("⚠️  Verificar estructura manualmente")
else:
    print("✅ No se encontraron problemas")

print("\n✅ Análisis completado")
PYEOF

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"
echo ""
echo "💡 Recarga la página con Ctrl+F5 para ver los cambios"

