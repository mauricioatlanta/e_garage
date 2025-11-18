#!/bin/bash
# Script para restaurar views.py desde el repositorio Git
# Esto reemplazará el archivo completo con la versión correcta desde origin/main

cd /home/atlantareciclajes/apps/egarage/current

echo "═══════════════════════════════════════════════════════════════"
echo "  RESTAURANDO views.py DESDE GIT"
echo "═══════════════════════════════════════════════════════════════"

# Crear backup del archivo actual
echo "📦 Creando backup del archivo actual..."
cp taller/documentos/views.py taller/documentos/views.py.backup_error_$(date +%Y%m%d_%H%M%S)

# Restaurar desde origin/main
echo "🔄 Restaurando desde origin/main..."
git checkout origin/main -- taller/documentos/views.py

# Verificar sintaxis
echo "✅ Verificando sintaxis..."
if python3 -m py_compile taller/documentos/views.py 2>/dev/null; then
    echo "✅ Sintaxis Python válida"
else
    echo "❌ Error de sintaxis detectado"
    echo "🔄 Restaurando desde backup anterior..."
    cp taller/documentos/views.py.backup_error_* taller/documentos/views.py 2>/dev/null
    exit 1
fi

# Reiniciar WSGI
echo "🔄 Reiniciando servidor WSGI..."
touch /var/www/www_egarage_cl_wsgi.py

echo "✅ Proceso completado"
echo ""
echo "💡 Si el error persiste, ejecuta:"
echo "   git show origin/main:taller/documentos/views.py > taller/documentos/views.py"

