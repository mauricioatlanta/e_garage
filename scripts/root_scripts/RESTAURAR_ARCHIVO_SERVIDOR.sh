#!/bin/bash
# Script para restaurar taller/documentos/views.py desde Git en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "🔄 Restaurando taller/documentos/views.py desde Git..."

# Crear backup del archivo actual
if [ -f "taller/documentos/views.py" ]; then
    cp taller/documentos/views.py taller/documentos/views.py.backup.$(date +%Y%m%d_%H%M%S)
    echo "📦 Backup creado"
fi

# Restaurar desde Git
git checkout HEAD -- taller/documentos/views.py

if [ $? -eq 0 ]; then
    echo "✅ Archivo restaurado desde Git"
    
    # Verificar sintaxis
    python3 -m py_compile taller/documentos/views.py 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Sintaxis Python válida"
    else
        echo "⚠️  Error de sintaxis detectado"
        exit 1
    fi
else
    echo "❌ Error al restaurar desde Git"
    exit 1
fi

echo ""
echo "🔄 Reiniciando servidor WSGI..."
touch /var/www/www_egarage_cl_wsgi.py

echo ""
echo "✅ Proceso completado"



