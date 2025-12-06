# Script para fix FINAL de botones en lista de clientes - con estilos inline forzados
# Fecha: 4 de Diciembre, 2025

Write-Host "=== FIX FINAL - Botones Lista Clientes con Estilos Inline Forzados ===" -ForegroundColor Cyan
Write-Host ""

# 1. Git add, commit y push
Write-Host "[*] Preparando cambios..." -ForegroundColor Yellow
git add templates/taller/common/clientes/lista_clientes.html

Write-Host "[*] Haciendo commit..." -ForegroundColor Yellow
git commit -m "fix: FORZAR visibilidad de texto en botones de clientes con estilos inline - Agregar estilos inline con !important en cada boton - Selectores CSS ultra especificos para movil - Forzar display inline-flex, visibility visible, opacity 1 - Color cyan brillante con text-shadow intenso - Iconos 1.4rem y texto 0.9rem en movil - Gap entre icono y texto para separacion clara - Este fix es especifico para template de clientes que no mostraba texto"

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
Write-Host "[OK] Luego prueba ESPECIFICAMENTE: https://www.egarage.cl/us/clientes/" -ForegroundColor Green
Write-Host "[OK] Los botones VER / EDITAR / ELIMINAR deben mostrar TEXTO + ICONO" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE: Este fix es ESPECIFICO para el template de clientes" -ForegroundColor Yellow
Write-Host "Los demas templates ya funcionan correctamente" -ForegroundColor Yellow
Write-Host ""





