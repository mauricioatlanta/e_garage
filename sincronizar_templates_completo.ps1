# Script para sincronizar TODA la carpeta de templates a produccion
# Ejecutar desde: E:\projecto\e_garage

$servidor = "atlantareciclajes@ssh.pythonanywhere.com"
$rutaLocal = ".\templates\"
$rutaRemota = "~/apps/egarage/current/templates/"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SINCRONIZANDO TODA LA CARPETA DE TEMPLATES" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "ADVERTENCIA: Esto va a subir TODOS los templates." -ForegroundColor Yellow
Write-Host "Esto puede tomar varios minutos..." -ForegroundColor Yellow
Write-Host ""

# Usar scp recursivo
Write-Host "Subiendo templates completos..." -ForegroundColor Green
scp -r $rutaLocal ${servidor}:${rutaRemota}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  TEMPLATES SINCRONIZADOS" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora REINICIA la aplicacion:" -ForegroundColor Cyan
Write-Host ""
Write-Host "ssh ${servidor}" -ForegroundColor White
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor White
Write-Host "exit" -ForegroundColor White
Write-Host ""





