#!/bin/bash
# Script de despliegue para fix de ciudades en móvil
# Ejecutar en servidor PythonAnywhere

echo "=================================================="
echo "🚀 Desplegando fix: Carga de ciudades en móviles"
echo "=================================================="
echo ""

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encuentra manage.py"
    echo "   Asegúrate de estar en: ~/apps/egarage/current"
    exit 1
fi

echo "✅ Directorio correcto detectado"
echo ""

# 2. Activar virtualenv
echo "📦 Activando virtualenv..."
source ~/.virtualenvs/venv_egarage310/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Error activando virtualenv"
    exit 1
fi
echo "✅ Virtualenv activado"
echo ""

# 3. Mostrar archivos que se van a actualizar
echo "📄 Archivos modificados:"
echo "   - ubicacion/static/ubicacion/js/ubicacion.js"
echo "   - taller/clientes/forms.py"
echo ""

# 4. Verificar que los archivos existen
if [ ! -f "ubicacion/static/ubicacion/js/ubicacion.js" ]; then
    echo "❌ Error: No se encuentra ubicacion/static/ubicacion/js/ubicacion.js"
    exit 1
fi

if [ ! -f "taller/clientes/forms.py" ]; then
    echo "❌ Error: No se encuentra taller/clientes/forms.py"
    exit 1
fi

echo "✅ Archivos fuente encontrados"
echo ""

# 5. Backup de archivos actuales
echo "💾 Creando backup de archivos actuales..."
BACKUP_DIR="backups/fix_movil_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp ubicacion/static/ubicacion/js/ubicacion.js "$BACKUP_DIR/" 2>/dev/null
cp taller/clientes/forms.py "$BACKUP_DIR/" 2>/dev/null
echo "✅ Backup creado en: $BACKUP_DIR"
echo ""

# 6. Collectstatic
echo "🔄 Ejecutando collectstatic..."
python manage.py collectstatic --noinput --clear
if [ $? -ne 0 ]; then
    echo "❌ Error ejecutando collectstatic"
    exit 1
fi
echo "✅ Collectstatic completado"
echo ""

# 7. Verificar archivos generados
echo "🔍 Verificando archivos generados..."
if [ -f "static/ubicacion/js/ubicacion.js" ]; then
    echo "✅ static/ubicacion/js/ubicacion.js generado"
else
    echo "⚠️  Advertencia: static/ubicacion/js/ubicacion.js no encontrado"
fi

if [ -f "staticfiles/ubicacion/js/ubicacion.js" ]; then
    echo "✅ staticfiles/ubicacion/js/ubicacion.js generado"
else
    echo "⚠️  Advertencia: staticfiles/ubicacion/js/ubicacion.js no encontrado"
fi
echo ""

# 8. Verificar contenido del archivo
echo "🔍 Verificando contenido del archivo JavaScript..."
if grep -q "if (!estadoSelect || !ciudadSelect)" static/ubicacion/js/ubicacion.js; then
    echo "✅ Código actualizado detectado en el archivo"
else
    echo "⚠️  Advertencia: El archivo puede no tener el fix aplicado"
fi
echo ""

# 9. Reload webapp
echo "♻️  Reloading webapp..."
touch /var/www/www_egarage_cl_wsgi.py
if [ $? -eq 0 ]; then
    echo "✅ Webapp reloaded (www.egarage.cl)"
else
    echo "⚠️  Advertencia: No se pudo reload automático"
    echo "   Por favor, hazlo manualmente desde:"
    echo "   https://www.pythonanywhere.com/user/atlantareciclajes/webapps/"
fi
echo ""

# 10. Resumen final
echo "=================================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=================================================="
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Probar en navegador:"
echo "   https://www.egarage.cl/cl/es/clientes/crear/"
echo ""
echo "2. Abrir Console (F12) y verificar logs:"
echo "   - '[ubicacion] Inicializando...'"
echo "   - '[ubicacion] Estado/región cambiado: X'"
echo "   - '[ubicacion] XX ciudades cargadas exitosamente'"
echo ""
echo "3. Probar en móvil real:"
echo "   - Abrir URL desde celular"
echo "   - Seleccionar región"
echo "   - Verificar que ciudades se cargan"
echo ""
echo "4. Si hay problemas:"
echo "   - Revisar: $BACKUP_DIR (backup de archivos anteriores)"
echo "   - Limpiar caché del navegador (Ctrl+Shift+Delete)"
echo "   - Ver logs: tail -f /var/log/www.egarage.cl.error.log"
echo ""
echo "=================================================="





