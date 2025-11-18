#!/bin/bash
# COMANDO SIMPLE PARA EJECUTAR EN EL SERVIDOR
# Copia y pega este comando completo en el servidor:

cd /home/atlantareciclajes/apps/egarage/current && \
sed -i '/^<<<<<<</d; /^=======$/d; /^>>>>>>>/d' taller/documentos/views.py && \
python3 -m py_compile taller/documentos/views.py && \
touch /var/www/www_egarage_cl_wsgi.py && \
echo "✅ Conflictos limpiados y servidor reiniciado"

