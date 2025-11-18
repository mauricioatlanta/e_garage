#!/bin/bash
# Script simple para corregir el f-string con backslash

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"

cd "$RELEASE_DIR" || exit 1

echo "🔧 Corrigiendo f-string en taller/documentos/views.py..."

# Primero intentar actualizar desde Git
echo "📥 Actualizando desde Git..."
git pull origin main 2>&1 | head -5

# Si el pull no funcionó o el archivo aún tiene el problema, corregirlo manualmente
if grep -q "f\"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20').replace('\\\\n', '%0A')}\"" "taller/documentos/views.py" 2>/dev/null || \
   grep -q "mensaje.replace.*'\\\\n'" "taller/documentos/views.py" 2>/dev/null; then
    
    echo "⚠️  Problema detectado. Aplicando corrección..."
    
    # Usar Python para hacer el reemplazo de forma segura
    python3 << 'PYEOF'
import re

file_path = 'taller/documentos/views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la línea problemática (alrededor de línea 1216)
for i, line in enumerate(lines):
    # Buscar el patrón problemático
    if 'url_whatsapp' in line and 'mensaje.replace' in line and '\\n' in line:
        # Encontrar dónde termina el bloque (buscar el paréntesis de cierre)
        j = i
        while j < len(lines) and ')' not in lines[j]:
            j += 1
        
        # Reemplazar las líneas
        new_lines = [
            "    # Crear URL de WhatsApp\n",
            "    # Nota: No se pueden usar backslashes directamente en expresiones f-string\n",
            "    mensaje_encoded = mensaje.replace(' ', '%20').replace('\\n', '%0A')\n",
            "    url_whatsapp = f\"https://wa.me/{telefono}?text={mensaje_encoded}\"\n"
        ]
        
        lines[i:j+1] = new_lines
        print(f"✅ Líneas {i+1}-{j+1} reemplazadas")
        break

# Escribir el archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Archivo corregido")
PYEOF

    # Verificar sintaxis
    if python3 -m py_compile "taller/documentos/views.py" 2>/dev/null; then
        echo "✅ Sintaxis verificada correctamente"
    else
        echo "❌ Error de sintaxis después de la corrección"
        exit 1
    fi
else
    echo "✅ El archivo ya está corregido"
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
echo "✅ Servidor reiniciado"

