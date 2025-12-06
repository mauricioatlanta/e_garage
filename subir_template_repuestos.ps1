# Subir template de repuestos faltante a produccion

Write-Host "Subiendo template de repuestos..." -ForegroundColor Cyan

# Subir el template correcto
scp .\templates\taller\common\repuestos\repuesto_list.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/common/repuestos/

Write-Host ""
Write-Host "Ahora reinicia la aplicacion:" -ForegroundColor Green
Write-Host "ssh atlantareciclajes@ssh.pythonanywhere.com" -ForegroundColor White
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor White
Write-Host "exit" -ForegroundColor White





