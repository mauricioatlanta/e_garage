#!/bin/bash
# Script para actualizar archivos en producción (PythonAnywhere)
# Ejecutar desde: E:\projecto\e_garage

echo "📤 Subiendo archivos modificados a PythonAnywhere..."

# 1. Subir el nuevo archivo JavaScript
echo ""
echo "1️⃣ Subiendo nuevo archivo JS..."
scp ./static/js/clientes_usa_estado_ciudad.js atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/static/js/

# 2. Subir el template modificado
echo ""
echo "2️⃣ Subiendo template modificado..."
scp ./templates/us/en/clientes/crear_cliente.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/us/en/clientes/

echo ""
echo "✅ Archivos subidos. Ahora ejecuta estos comandos en PythonAnywhere:"
echo ""
echo "ssh atlantareciclajes@ssh.pythonanywhere.com"
echo "cd ~/apps/egarage/current"
echo "python manage.py collectstatic --noinput"
echo "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py"
echo ""
echo "🎉 Listo! Los cambios estarán activos en producción"









