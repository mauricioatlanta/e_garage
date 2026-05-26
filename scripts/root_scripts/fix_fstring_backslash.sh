#!/bin/bash
# Script para corregir el error de f-string con backslash en el servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"
CURRENT_DIR="/home/atlantareciclajes/apps/egarage/current"

cd "$RELEASE_DIR" || exit 1

echo "🔍 Buscando f-string con backslash en taller/documentos/views.py..."

# Verificar si el archivo tiene el problema
if grep -q "f\"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20').replace('\\\\n', '%0A')}\"" "taller/documentos/views.py" 2>/dev/null; then
    echo "⚠️  Problema encontrado. Corrigiendo..."
    
    # Crear un archivo temporal con la corrección
    cat > /tmp/fix_views.py << 'PYTHONFIX'
# Buscar y reemplazar la línea problemática
import re

with open('taller/documentos/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para encontrar la línea problemática
pattern = r'(\s+)(url_whatsapp = \(\s+f"https://wa\.me/\{telefono\}\?text=\{mensaje\.replace\(\' \', \'%20\'\)\.replace\(\'\\n\', \'%0A\'\)\}"\s+\))'

# Reemplazo
replacement = r'\1# Nota: No se pueden usar backslashes directamente en expresiones f-string\n\1mensaje_encoded = mensaje.replace(\' \', \'%20\').replace(\'\\n\', \'%0A\')\n\1url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"'

new_content = re.sub(pattern, replacement, content)

with open('taller/documentos/views.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Archivo corregido")
PYTHONFIX

    # Ejecutar el script de Python para hacer el reemplazo
    python3 /tmp/fix_views.py
    
    # Verificar sintaxis
    if python3 -m py_compile "taller/documentos/views.py" 2>/dev/null; then
        echo "✅ Sintaxis verificada correctamente"
    else
        echo "⚠️  Error de sintaxis. Aplicando corrección manual..."
        
        # Corrección manual más simple usando sed
        sed -i '1215,1217c\
    # Crear URL de WhatsApp\
    # Nota: No se pueden usar backslashes directamente en expresiones f-string\
    mensaje_encoded = mensaje.replace('\'' '\'', '\''%20'\'').replace('\''\\n'\'', '\''%0A'\'')\
    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"' "taller/documentos/views.py"
        
        # Verificar nuevamente
        if python3 -m py_compile "taller/documentos/views.py" 2>/dev/null; then
            echo "✅ Corrección manual exitosa"
        else
            echo "❌ Error: No se pudo corregir automáticamente"
            exit 1
        fi
    fi
else
    echo "✅ El archivo ya está corregido o no tiene el problema"
fi

# Verificar que no haya más f-strings problemáticos
echo ""
echo "🔍 Verificando otros f-strings problemáticos..."
if grep -n "f\".*replace.*\\\\" "taller/documentos/views.py" 2>/dev/null; then
    echo "⚠️  Se encontraron más f-strings problemáticos"
else
    echo "✅ No se encontraron más f-strings problemáticos"
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_digitalocean_com_wsgi.py
echo "✅ Servidor reiniciado"



