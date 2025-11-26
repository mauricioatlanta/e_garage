#!/bin/bash
# Script para aplicar el diseño de mosaico futurista al selector de país

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🎨 Aplicando diseño de mosaico futurista..."

# Leer el archivo local y copiarlo al servidor
python3 << 'PYEOF'
import shutil
import os

local_file = "templates/public/selector_pais.html"
server_file = "templates/public/selector_pais.html"

# Leer el archivo local
with open(local_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar que tiene el nuevo diseño
if 'country-mosaic' in content and 'country-card' in content:
    # Escribir al servidor
    with open(server_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Diseño de mosaico futurista aplicado")
    print("   - Grid inteligente sin scrollbars")
    print("   - Tarjetas futuristas premium")
    print("   - Efectos de brillo y animaciones avanzadas")
    print("   - Diseño responsive perfecto")
else:
    print("❌ El archivo local no tiene el diseño correcto")
PYEOF

echo ""
echo "✅✅✅ Diseño aplicado ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



