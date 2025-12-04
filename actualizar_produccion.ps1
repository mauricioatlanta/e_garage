# Script para actualizar archivos en produccion (PythonAnywhere)
# Ejecutar desde: E:\projecto\e_garage

Write-Host "Subiendo archivos modificados a PythonAnywhere..." -ForegroundColor Cyan

# 1. Subir el nuevo archivo JavaScript
Write-Host ""
Write-Host "1. Subiendo nuevo archivo JS..." -ForegroundColor Yellow
scp .\static\js\clientes_usa_estado_ciudad.js atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/static/js/

# 2. Subir el template modificado
Write-Host ""
Write-Host "2. Subiendo template modificado..." -ForegroundColor Yellow
scp .\templates\us\en\clientes\crear_cliente.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/us/en/clientes/

Write-Host ""
Write-Host "Archivos subidos. Ahora ejecuta estos comandos en PythonAnywhere:" -ForegroundColor Green
Write-Host ""
Write-Host "ssh atlantareciclajes@ssh.pythonanywhere.com" -ForegroundColor White
Write-Host "cd ~/apps/egarage/current" -ForegroundColor White
Write-Host "python manage.py collectstatic --noinput" -ForegroundColor White
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor White
Write-Host ""
Write-Host "Listo! Los cambios estaran activos en produccion" -ForegroundColor Green

