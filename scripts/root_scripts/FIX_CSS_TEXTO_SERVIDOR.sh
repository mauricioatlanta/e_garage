#!/bin/bash
# Script para corregir el problema de CSS renderizado como texto
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🔍 Verificando template selector_pais.html..."

FILE="templates/public/selector_pais.html"

if [ ! -f "$FILE" ]; then
    echo "❌ No se encontró el archivo $FILE"
    exit 1
fi

# Crear backup
cp "$FILE" "$FILE.backup_$(date +%Y%m%d_%H%M%S)"
echo "📋 Backup creado"

# Verificar si hay problemas con las etiquetas style
echo "🔍 Verificando estructura del archivo..."

# Verificar que la etiqueta <style> esté cerrada correctamente
if ! grep -q "</style>" "$FILE"; then
    echo "⚠️  No se encontró cierre de etiqueta </style>"
    echo "🔧 Corrigiendo..."
    
    # Buscar la línea con </head> y agregar </style> antes si falta
    python3 << 'PYEOF'
import sys

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar si hay </style>
has_style_close = any('</style>' in line for line in lines)

if not has_style_close:
    # Buscar </head> y agregar </style> antes
    for i, line in enumerate(lines):
        if '</head>' in line:
            # Insertar </style> antes de </head>
            lines.insert(i, '  </style>\n')
            break
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Etiqueta </style> agregada")
else:
    print("✅ Etiqueta </style> encontrada")
PYEOF
fi

# Verificar que no haya CSS fuera de las etiquetas style
echo "🔍 Verificando CSS fuera de etiquetas..."

# Buscar líneas con CSS que no estén dentro de <style>
python3 << 'PYEOF'
import sys
import re

file_path = "templates/public/selector_pais.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

# Verificar estructura
in_style = False
in_head = False
problems = []

for i, line in enumerate(lines, 1):
    if '<head>' in line or '<head ' in line:
        in_head = True
    if '</head>' in line:
        in_head = False
    if '<style>' in line or '<style ' in line:
        in_style = True
    if '</style>' in line:
        in_style = False
    
    # Detectar CSS fuera de style tags
    if not in_style and in_head:
        # Buscar patrones de CSS
        if re.search(r'\{[^}]*:[^}]*\}', line) and '<style' not in line and '</style>' not in line:
            problems.append((i, line.strip()[:60]))

if problems:
    print(f"⚠️  Se encontraron {len(problems)} posibles problemas:")
    for line_num, line_content in problems[:5]:
        print(f"   Línea {line_num}: {line_content}")
else:
    print("✅ No se encontraron problemas de estructura")

# Verificar que el archivo tenga la estructura correcta
if '<style>' in content and '</style>' in content:
    style_start = content.find('<style>')
    style_end = content.find('</style>')
    if style_start < style_end:
        print("✅ Estructura de <style> correcta")
    else:
        print("❌ Problema: </style> aparece antes de <style>")
        sys.exit(1)
else:
    print("❌ No se encontraron etiquetas <style> o </style>")
    sys.exit(1)
PYEOF

# Verificar encoding
echo ""
echo "🔍 Verificando encoding..."
file -bi "$FILE" | grep -q "utf-8" && echo "✅ Encoding UTF-8 correcto" || echo "⚠️  Encoding puede ser incorrecto"

# Verificar que no haya caracteres extraños que rompan el HTML
echo ""
echo "🔍 Verificando caracteres problemáticos..."
if grep -qP '[^\x00-\x7F]' "$FILE" 2>/dev/null; then
    echo "⚠️  Archivo contiene caracteres no-ASCII (puede ser normal para emojis)"
else
    echo "✅ Solo caracteres ASCII"
fi

echo ""
echo "✅ Verificación completada"
echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

