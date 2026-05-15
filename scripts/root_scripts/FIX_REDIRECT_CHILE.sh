#!/bin/bash
# Script para corregir la redirección de Chile
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="taller/urls_extra/chile.py"

echo "📋 Creando backup..."
cp "$FILE" "$FILE.backup_redirect_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo redirección de /cl/es/ a /cl/..."

python3 << 'PYEOF'
file_path = "taller/urls_extra/chile.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar la redirección
if '/cl/egarage/' in content:
    content = content.replace('/cl/egarage/', '/cl/')
    print("✅ Redirección corregida: /cl/egarage/ -> /cl/")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Archivo actualizado")
else:
    print("✅ La redirección ya está correcta o no se encontró")
PYEOF

echo "🔄 Reiniciando servidor..."
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor reiniciado"

