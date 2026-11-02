#!/bin/bash
# Script para copiar el archivo centro_operaciones.html al servidor

# Si tienes acceso SSH directo, usa este comando:
# scp templates/taller/cl/es/dashboard/centro_operaciones.html \
#     usuario@servidor:/home/atlantareciclajes/apps/egarage/current/templates/taller/cl/es/dashboard/

# O si ya estás en el servidor, ejecuta este comando Python:
cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
import os

# Leer el archivo local (si estás en el servidor y tienes el archivo en otra ubicación)
# O simplemente copiar desde el repositorio Git

# Si el archivo ya está en el servidor y solo necesitas reiniciar:
os.system('touch /var/www/www_egarage_cl_wsgi.py')
print("✅ Servidor reiniciado")

# Si necesitas copiar desde Git:
os.system('git checkout HEAD -- templates/taller/cl/es/dashboard/centro_operaciones.html')
print("✅ Archivo restaurado desde Git")
PYEOF

