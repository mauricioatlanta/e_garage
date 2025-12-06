# Script para actualizar botones de navegacion en movil - base.html
# Fecha: 4 de Diciembre, 2025

Write-Host "=== Actualizando Botones de Navegacion para Movil ===" -ForegroundColor Cyan
Write-Host ""

# 1. Git add, commit y push
Write-Host "[*] Preparando cambios..." -ForegroundColor Yellow
git add templates/base.html

Write-Host "[*] Haciendo commit..." -ForegroundColor Yellow
git commit -m "fix: Forzar visibilidad de texto en botones de navegacion para movil - Agregar media queries ultra especificos para moviles pequenios y tablets - Aumentar especificidad de selectores CSS para anular estilos anteriores - Forzar flex-direction column y texto visible con maxima prioridad - Mejorar contraste con text-shadow mas intenso - Iconos y texto mas grandes para mejor usabilidad - Fix para dashboard principal en pantallas menores a 768px"

Write-Host "[*] Subiendo a GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "[OK] Cambios subidos a GitHub exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "=== Siguiente Paso: Actualizar Servidor ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Conectate al servidor SSH y ejecuta:" -ForegroundColor Yellow
Write-Host ""
Write-Host "cd ~/e_garage" -ForegroundColor White
Write-Host "git pull origin main" -ForegroundColor White
Write-Host "cp ~/e_garage/templates/base.html ~/apps/egarage/current/templates/" -ForegroundColor White
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor White
Write-Host ""
Write-Host "[OK] Despues, prueba en movil: https://www.egarage.cl/us/" -ForegroundColor Green
Write-Host "[OK] Los botones deben mostrar TEXTO + ICONO" -ForegroundColor Green
Write-Host ""






