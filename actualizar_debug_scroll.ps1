# Script para actualizar archivos con FIX de scroll automático en móviles a producción
# Ejecutar desde: E:\projecto\e_garage

Write-Host "Subiendo archivos con FIX anti-scroll automático para móviles..." -ForegroundColor Cyan

# 1. Subir base.html principal (con espias de scroll y focus)
Write-Host ""
Write-Host "1. Subiendo base.html principal..." -ForegroundColor Yellow
scp .\templates\base.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/

# 2. Subir base.html de taller/common (con espias)
Write-Host ""
Write-Host "2. Subiendo base.html de taller..." -ForegroundColor Yellow
scp .\templates\taller\common\base.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/common/

Write-Host ""
Write-Host "Archivos subidos. Ahora reinicia la aplicacion:" -ForegroundColor Green
Write-Host ""
Write-Host "ssh atlantareciclajes@ssh.pythonanywhere.com" -ForegroundColor White
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor White
Write-Host "exit" -ForegroundColor White
Write-Host ""
Write-Host "Listo! La proteccion anti-scroll para moviles esta activa en produccion" -ForegroundColor Green
Write-Host "El problema de scroll automatico en moviles deberia estar resuelto." -ForegroundColor Green

