# Script para actualizar template de clientes con mejoras para movil
# Fecha: 4 de Diciembre, 2025

Write-Host "=== Actualizando Template de Clientes para Movil ===" -ForegroundColor Cyan
Write-Host ""

# 1. Git add, commit y push
Write-Host "[*] Preparando cambios..." -ForegroundColor Yellow
git add templates/taller/common/clientes/lista_clientes.html

Write-Host "[*] Haciendo commit..." -ForegroundColor Yellow
git commit -m "fix: Mejorar visibilidad de botones en movil para lista de clientes - Aumentar tamanio de botones y texto - Agregar estilos especificos para movil - Hacer botones mas consistentes con otros modulos (documentos) - Mejorar contraste y legibilidad en pantallas pequenias - Iconos y texto mas grandes para mejor usabilidad tactil"

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
Write-Host "cp -r ~/e_garage/templates/taller/common ~/apps/egarage/current/templates/taller/" -ForegroundColor White
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor White
Write-Host ""
Write-Host "[OK] Despues, prueba en: https://www.egarage.cl/us/clientes/" -ForegroundColor Green
Write-Host ""
