#!/bin/bash
# Script para corregir el f-string con backslash en views.py
# Ejecutar en el servidor: bash fix_fstring_servidor.sh

cd /home/atlantareciclajes/apps/egarage/current || exit 1

FILE="taller/documentos/views.py"

echo "🔧 Corrigiendo f-string en $FILE..."

# Buscar y corregir el f-string problemático
# Buscar líneas con f-string que contengan .replace('\n')
sed -i 's|\(f"[^"]*wa\.me[^"]*\)\(mensaje\.replace.*\.replace.*\\n.*\)|# Nota: No se pueden usar backslashes directamente en expresiones f-string\n    mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n    url_whatsapp = \1{mensaje_encoded}|g' "$FILE"

# Si el patrón anterior no funcionó, intentar con otro patrón
# Buscar: f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20').replace('\n', '%0A')}"
sed -i 's|f"https://wa\.me/{telefono}?text={mensaje\.replace('\'' '\'', '\''%20'\''\)\.replace('\''\\n'\'', '\''%0A'\'')}"|# Crear URL de WhatsApp\n    # Nota: No se pueden usar backslashes directamente en expresiones f-string\n    mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"|g' "$FILE"

# Verificar sintaxis
python3 -m py_compile "$FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Sintaxis Python válida"
else
    echo "⚠️  Error de sintaxis detectado"
    echo "🔄 Restaurando desde Git..."
    git fetch origin main
    git checkout origin/main -- "$FILE"
    
    # Verificar de nuevo
    python3 -m py_compile "$FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Archivo restaurado desde Git y sintaxis válida"
    else
        echo "❌ Error persistente después de restaurar"
        exit 1
    fi
fi

# Reiniciar servidor
touch /var/www/www_egarage_cl_wsgi.py
echo "✅ Servidor WSGI reiniciado"

echo ""
echo "✅ Proceso completado"

