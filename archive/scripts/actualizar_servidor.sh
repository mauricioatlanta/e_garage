#!/bin/bash
# Script para actualizar reportes de kilometraje en el servidor

echo "🚀 Actualizando reportes de kilometraje en el servidor..."

# 1. Actualizar código
echo "📥 Actualizando código desde git..."
cd /ruta/al/proyecto/e_garage
git pull origin main

# 2. Verificar que los archivos existen
echo "✅ Verificando archivos..."
if [ ! -f "taller/reportes/kilometraje_reportes.py" ]; then
    echo "❌ ERROR: No se encuentra taller/reportes/kilometraje_reportes.py"
    exit 1
fi

if [ ! -f "templates/taller/reportes/reportes.html" ]; then
    echo "❌ ERROR: No se encuentra templates/taller/reportes/reportes.html"
    exit 1
fi

# 3. Verificar que el template tiene el enlace
if ! grep -q "kilometraje/recordatorios" templates/taller/reportes/reportes.html; then
    echo "❌ ERROR: El template no tiene el enlace a recordatorios"
    exit 1
fi

# 4. Aplicar migraciones
echo "📊 Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

# 5. Limpiar cache de Python
echo "🧹 Limpiando cache..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# 6. Recolectar estáticos
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# 7. Reiniciar servidor
echo "🔄 Reiniciando servidor..."
# Descomentar la línea que corresponda a tu configuración:
# sudo systemctl restart gunicorn
# sudo systemctl restart uwsgi
# sudo systemctl restart apache2
# sudo supervisorctl restart gunicorn

echo "✅ Actualización completada!"
echo "🧪 Verifica que funciona:"
echo "   - /reportes/kilometraje/recordatorios/"
echo "   - /reportes/"

