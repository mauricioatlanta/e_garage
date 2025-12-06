# Script para subir TODOS los cambios a produccion
# Ejecutar desde: E:\projecto\e_garage

$servidor = "atlantareciclajes@ssh.pythonanywhere.com"
$base = "~/apps/egarage/current"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SUBIENDO TODOS LOS CAMBIOS A PRODUCCION" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Templates Base
Write-Host "[1/12] Subiendo base.html principal..." -ForegroundColor Yellow
scp .\templates\base.html ${servidor}:${base}/templates/

Write-Host "[2/12] Subiendo taller/common/base.html..." -ForegroundColor Yellow
scp .\templates\taller\common\base.html ${servidor}:${base}/templates/taller/common/

# Templates USA - EN
Write-Host "[3/12] Subiendo us/en/clientes/crear_cliente.html..." -ForegroundColor Yellow
scp .\templates\us\en\clientes\crear_cliente.html ${servidor}:${base}/templates/us/en/clientes/

Write-Host "[4/12] Subiendo us/en/clientes/editar_cliente.html..." -ForegroundColor Yellow
scp .\templates\us\en\clientes\editar_cliente.html ${servidor}:${base}/templates/us/en/clientes/

# Templates USA - ES
Write-Host "[5/12] Subiendo us/es/clientes/crear_cliente.html..." -ForegroundColor Yellow
scp .\templates\us\es\clientes\crear_cliente.html ${servidor}:${base}/templates/us/es/clientes/

Write-Host "[6/12] Subiendo us/es/clientes/editar_cliente.html..." -ForegroundColor Yellow
scp .\templates\us\es\clientes\editar_cliente.html ${servidor}:${base}/templates/us/es/clientes/

Write-Host "[7/12] Subiendo us/es/clientes/cliente_form.html..." -ForegroundColor Yellow
scp .\templates\us\es\clientes\cliente_form.html ${servidor}:${base}/templates/us/es/clientes/

# Templates Taller USA - EN
Write-Host "[8/12] Subiendo taller/us/en/clientes/crear_cliente.html..." -ForegroundColor Yellow
scp .\templates\taller\us\en\clientes\crear_cliente.html ${servidor}:${base}/templates/taller/us/en/clientes/

Write-Host "[9/12] Subiendo taller/us/en/clientes/cliente_form.html..." -ForegroundColor Yellow
scp .\templates\taller\us\en\clientes\cliente_form.html ${servidor}:${base}/templates/taller/us/en/clientes/

# Templates Taller USA - ES
Write-Host "[10/12] Subiendo taller/us/es/clientes/cliente_form.html..." -ForegroundColor Yellow
scp .\templates\taller\us\es\clientes\cliente_form.html ${servidor}:${base}/templates/taller/us/es/clientes/

# Templates Comunes
Write-Host "[11/12] Subiendo taller/common/clientes/cliente_form.html..." -ForegroundColor Yellow
scp .\templates\taller\common\clientes\cliente_form.html ${servidor}:${base}/templates/taller/common/clientes/

Write-Host "[12/12] Subiendo taller/common/clientes/cliente_list.html..." -ForegroundColor Yellow
scp .\templates\taller\common\clientes\cliente_list.html ${servidor}:${base}/templates/taller/common/clientes/

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  ARCHIVOS SUBIDOS EXITOSAMENTE" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora ejecuta estos comandos para reiniciar:" -ForegroundColor Cyan
Write-Host ""
Write-Host "ssh ${servidor}" -ForegroundColor White
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor White
Write-Host "exit" -ForegroundColor White
Write-Host ""
Write-Host "Listo! Limpia cache en el celular y prueba." -ForegroundColor Green






