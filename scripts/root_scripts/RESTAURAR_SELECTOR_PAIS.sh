#!/bin/bash
# Script para restaurar el template selector_pais.html correctamente
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="templates/public/selector_pais.html"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_restore_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Verificando y corrigiendo estructura..."

python3 << 'PYEOF'
import sys
import re

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar problemas comunes
problems = []

# 1. Verificar que </style> exista
if '</style>' not in content:
    problems.append("Falta etiqueta </style>")
    # Buscar </head> y agregar </style> antes
    content = content.replace('</head>', '  </style>\n</head>', 1)

# 2. Verificar que <style> esté antes de </style>
style_pos = content.find('<style>')
style_close_pos = content.find('</style>')

if style_pos == -1:
    problems.append("No se encontró <style>")
    sys.exit(1)

if style_close_pos == -1:
    problems.append("No se encontró </style>")
    sys.exit(1)

if style_pos > style_close_pos:
    problems.append("</style> aparece antes de <style>")
    sys.exit(1)

# 3. Verificar que no haya CSS duplicado o fuera de style
# Buscar patrones de CSS fuera de las etiquetas style
head_content = content[content.find('<head>'):content.find('</head>')]
style_content = content[style_pos:style_close_pos+8]

# Verificar si hay CSS en head pero fuera de style
css_pattern = re.compile(r'\{[^}]*:[^}]*\}')
css_in_head = css_pattern.findall(head_content)
css_in_style = css_pattern.findall(style_content)

if len(css_in_head) > len(css_in_style):
    problems.append("CSS encontrado fuera de etiquetas <style>")

# 4. Si hay problemas, reconstruir el archivo
if problems:
    print(f"⚠️  Problemas encontrados: {', '.join(problems)}")
    print("🔧 Reconstruyendo archivo...")
    
    # Leer líneas
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Reconstruir correctamente
    new_lines = []
    in_style = False
    style_lines = []
    
    for line in lines:
        if '<style>' in line or '<style ' in line:
            in_style = True
            new_lines.append(line)
        elif '</style>' in line:
            in_style = False
            # Agregar todas las líneas de estilo acumuladas
            new_lines.extend(style_lines)
            style_lines = []
            new_lines.append(line)
        elif in_style:
            style_lines.append(line)
        else:
            new_lines.append(line)
    
    # Si quedaron líneas de estilo sin cerrar, agregarlas antes de </head>
    if style_lines:
        for i, line in enumerate(new_lines):
            if '</head>' in line:
                new_lines.insert(i, '  </style>\n')
                break
    
    # Escribir archivo corregido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Archivo reconstruido")
else:
    print("✅ No se encontraron problemas de estructura")

# Verificar sintaxis final
with open(file_path, 'r', encoding='utf-8') as f:
    final_content = f.read()
    
if '<style>' in final_content and '</style>' in final_content:
    final_style_pos = final_content.find('<style>')
    final_style_close_pos = final_content.find('</style>')
    if final_style_pos < final_style_close_pos:
        print("✅ Estructura final correcta")
    else:
        print("❌ Error: estructura aún incorrecta")
        sys.exit(1)
else:
    print("❌ Error: etiquetas style faltantes")
    sys.exit(1)
PYEOF

echo ""
echo "✅ Proceso completado"
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

