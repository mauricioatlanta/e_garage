#!/bin/bash
# Script para corregir CSS que aparece como texto (falta etiqueta <style>)
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/public/selector_pais.html"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_css_fix_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo CSS sin etiqueta <style>..."

python3 << 'PYEOF'
import sys
import re

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

# Detectar CSS suelto (sin etiquetas <style>)
# Buscar patrones como: body{margin:0;...} o .wrap{max-width:...}
css_pattern = re.compile(r'^[a-zA-Z0-9_#\.\-\s]+\{[^}]+\}')

css_found_outside = False
css_start_line = None
css_end_line = None

# Buscar CSS fuera de etiquetas style
in_style_tag = False
for i, line in enumerate(lines):
    if '<style>' in line or '<style ' in line:
        in_style_tag = True
    if '</style>' in line:
        in_style_tag = False
    
    # Si encontramos CSS fuera de style tags
    if not in_style_tag and css_pattern.search(line.strip()) and '<style' not in line and '</style>' not in line:
        if css_start_line is None:
            css_start_line = i
            css_found_outside = True
        css_end_line = i

if css_found_outside:
    print(f"⚠️  CSS encontrado fuera de etiquetas <style> (líneas {css_start_line+1}-{css_end_line+1})")
    print("🔧 Envolviendo CSS en etiquetas <style>...")
    
    # Buscar dónde insertar el <style>
    # Preferiblemente en el <head>, antes de </head>
    head_close_idx = None
    for i, line in enumerate(lines):
        if '</head>' in line:
            head_close_idx = i
            break
    
    if head_close_idx is None:
        # Si no hay </head>, buscar </body> o el final del archivo
        for i, line in enumerate(lines):
            if '</body>' in line:
                head_close_idx = i
                break
        if head_close_idx is None:
            head_close_idx = len(lines)
    
    # Extraer el CSS suelto
    css_lines = lines[css_start_line:css_end_line+1]
    
    # Eliminar las líneas de CSS sueltas
    new_lines = lines[:css_start_line] + lines[css_end_line+1:]
    
    # Insertar el CSS envuelto en <style> antes de </head>
    # Primero verificar si ya hay un <style> en el head
    has_style_in_head = False
    style_insert_idx = head_close_idx
    
    for i in range(head_close_idx):
        if '<style>' in new_lines[i] or '<style ' in new_lines[i]:
            has_style_in_head = True
            # Buscar el </style> correspondiente
            for j in range(i+1, head_close_idx):
                if '</style>' in new_lines[j]:
                    # Insertar el nuevo CSS antes del </style> existente
                    style_insert_idx = j
                    break
            break
    
    # Si no hay <style> existente, crear uno nuevo
    if not has_style_in_head:
        # Insertar <style> y </style> con el CSS entre ellos
        style_block = ['  <style>\n'] + css_lines + ['  </style>\n']
        new_lines = new_lines[:style_insert_idx] + style_block + new_lines[style_insert_idx:]
    else:
        # Agregar el CSS al <style> existente
        new_lines = new_lines[:style_insert_idx] + css_lines + new_lines[style_insert_idx:]
    
    # Escribir archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ CSS envuelto en etiquetas <style>")
else:
    print("✅ No se encontró CSS fuera de etiquetas <style>")
    
    # Verificar que las etiquetas <style> existan y estén correctas
    if '<style>' not in content and '<style ' not in content:
        print("⚠️  No se encontró etiqueta <style>")
        print("🔧 Agregando etiquetas <style>...")
        
        # Buscar </head> y agregar <style> antes
        for i, line in enumerate(lines):
            if '</head>' in line:
                # Buscar si hay CSS antes de </head>
                css_before_head = False
                for j in range(max(0, i-20), i):
                    if css_pattern.search(lines[j].strip()):
                        css_before_head = True
                        break
                
                if css_before_head:
                    # Envolver el CSS en <style>
                    # Buscar dónde empieza el CSS
                    css_start = None
                    for j in range(max(0, i-20), i):
                        if css_pattern.search(lines[j].strip()):
                            css_start = j
                            break
                    
                    if css_start is not None:
                        # Agregar <style> antes del CSS
                        lines.insert(css_start, '  <style>\n')
                        # Agregar </style> antes de </head>
                        lines.insert(i+1, '  </style>\n')
                
                break
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Etiquetas <style> agregadas")
    else:
        print("✅ Estructura de <style> correcta")

print("✅ Verificación completada")
PYEOF

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"
echo ""
echo "💡 Recarga la página en el navegador (Ctrl+F5) para ver los cambios"

