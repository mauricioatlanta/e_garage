#!/bin/bash
# Script completo para corregir CSS apareciendo como texto
# Verifica y corrige TODO el archivo en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/public/selector_pais.html"

echo "📋 Creando backup completo..."
cp "$FILE" "$FILE.backup_completo_$(date +%Y%m%d_%H%M%S)"

echo "🔍 Analizando archivo completo..."

python3 << 'PYEOF'
import re
import sys

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

print(f"📄 Archivo tiene {len(lines)} líneas")

# Buscar TODOS los problemas posibles
problems = []

# 1. Buscar CSS suelto (sin <style>)
css_pattern = re.compile(r'^[a-zA-Z0-9_#\.\-\s]+\{[^}]+\}')
css_suelto = []

for i, line in enumerate(lines):
    stripped = line.strip()
    if css_pattern.search(stripped) and '<style' not in line and '</style>' not in line and stripped:
        css_suelto.append((i+1, stripped[:60]))

if css_suelto:
    problems.append(f"CSS suelto encontrado en {len(css_suelto)} líneas")
    print(f"⚠️  CSS suelto en líneas: {[l[0] for l in css_suelto[:5]]}")

# 2. Verificar estructura de <style>
style_open_pos = content.find('<style>')
style_open_pos_alt = content.find('<style ')
style_close_pos = content.find('</style>')

if style_open_pos == -1 and style_open_pos_alt == -1:
    problems.append("No se encontró etiqueta <style>")
    print("❌ No se encontró <style>")
elif style_close_pos == -1:
    problems.append("No se encontró etiqueta </style>")
    print("❌ No se encontró </style>")
else:
    style_pos = style_open_pos if style_open_pos != -1 else style_open_pos_alt
    if style_pos > style_close_pos:
        problems.append("</style> aparece antes de <style>")
        print("❌ </style> antes de <style>")
    else:
        print("✅ Estructura de <style> básica correcta")

# 3. Buscar CSS después de </style> pero antes de </head>
head_close_pos = content.find('</head>')
if style_close_pos != -1 and head_close_pos != -1:
    if style_close_pos < head_close_pos:
        # Verificar si hay CSS entre </style> y </head>
        between_content = content[style_close_pos+8:head_close_pos]
        if css_pattern.search(between_content):
            problems.append("CSS encontrado después de </style> pero antes de </head>")
            print("⚠️  CSS después de </style>")

# 4. Buscar CSS después de </head> o en el body
body_start = content.find('<body>')
if body_start != -1:
    body_content = content[body_start:]
    if css_pattern.search(body_content):
        problems.append("CSS encontrado en el body")
        print("⚠️  CSS en el body")

# Si hay problemas, corregirlos
if problems:
    print(f"\n🔧 Corrigiendo {len(problems)} problema(s)...")
    
    # Estrategia: Reconstruir el archivo correctamente
    new_lines = []
    in_style = False
    css_collected = []
    head_found = False
    head_closed = False
    
    for i, line in enumerate(lines):
        # Detectar <head>
        if '<head>' in line or '<head ' in line:
            head_found = True
            new_lines.append(line)
            continue
        
        # Detectar </head>
        if '</head>' in line:
            # Antes de cerrar head, asegurar que </style> esté si hay CSS
            if css_collected and not in_style:
                new_lines.append('  <style>\n')
                new_lines.extend(css_collected)
                new_lines.append('  </style>\n')
                css_collected = []
            elif in_style and css_collected:
                new_lines.extend(css_collected)
                new_lines.append('  </style>\n')
                css_collected = []
                in_style = False
            new_lines.append(line)
            head_closed = True
            continue
        
        # Detectar <style>
        if '<style>' in line or '<style ' in line:
            in_style = True
            new_lines.append(line)
            continue
        
        # Detectar </style>
        if '</style>' in line:
            if css_collected:
                new_lines.extend(css_collected)
                css_collected = []
            new_lines.append(line)
            in_style = False
            continue
        
        # Si estamos en head y encontramos CSS, recopilarlo
        if head_found and not head_closed:
            stripped = line.strip()
            if css_pattern.search(stripped) or (stripped and '{' in stripped and '}' in stripped):
                if not in_style:
                    css_collected.append(line)
                    continue
                else:
                    new_lines.append(line)
                    continue
        
        # Línea normal
        new_lines.append(line)
    
    # Si quedó CSS recopilado sin procesar, agregarlo
    if css_collected:
        # Buscar </head> en las nuevas líneas
        for i in range(len(new_lines)-1, -1, -1):
            if '</head>' in new_lines[i]:
                new_lines.insert(i, '  <style>\n')
                new_lines.insert(i+1, *css_collected)
                new_lines.insert(i+1+len(css_collected), '  </style>\n')
                break
    
    # Escribir archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Archivo reconstruido")
    
    # Verificar resultado
    with open(file_path, 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    # Verificar que no quede CSS suelto
    final_css_suelto = []
    for match in css_pattern.finditer(new_content):
        pos = match.start()
        # Verificar que esté dentro de <style>
        style_before = new_content.rfind('<style>', 0, pos)
        style_after = new_content.find('</style>', pos)
        if style_before == -1 or style_after == -1 or style_after < style_before:
            final_css_suelto.append(match.group()[:50])
    
    if final_css_suelto:
        print(f"⚠️  Aún queda CSS suelto: {len(final_css_suelto)} instancias")
    else:
        print("✅ No queda CSS suelto")
        
    # Verificar estructura final
    if '<style>' in new_content and '</style>' in new_content:
        s_pos = new_content.find('<style>')
        s_close_pos = new_content.find('</style>')
        h_close_pos = new_content.find('</head>')
        if s_pos < s_close_pos < h_close_pos:
            print("✅ Estructura final correcta")
        else:
            print("⚠️  Estructura puede tener problemas")
else:
    print("✅ No se encontraron problemas obvios")
    print("💡 El problema puede estar en otro lugar (cache, otro template, etc.)")

print("\n✅ Análisis completado")
PYEOF

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"
echo ""
echo "💡 Si el problema persiste, verifica:"
echo "   1. Limpia la caché del navegador (Ctrl+Shift+Delete)"
echo "   2. Verifica que no haya otro template siendo usado"
echo "   3. Revisa si hay CSS en archivos estáticos"

