# Script para diagnosticar el logo de la empresa
# Uso: .\scripts\check_logo.ps1

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "🔍 DIAGNÓSTICO DE LOGOS - eGarage" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan

Write-Host "`n📋 Ejecutando diagnóstico...`n" -ForegroundColor Yellow

# Ejecutar el management command
python manage.py check_logo

Write-Host "`n✅ Diagnóstico completado!" -ForegroundColor Green
Write-Host "`n💡 INSTRUCCIONES:`n" -ForegroundColor Cyan
Write-Host "   1. Si el logo NO está configurado:" -ForegroundColor White
Write-Host "      - Ve a Settings: http://127.0.0.1:8000/us/settings/" -ForegroundColor Gray
Write-Host "      - Sube tu logo en la sección 'Profile'" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Si el logo YA está configurado:" -ForegroundColor White
Write-Host "      - Recarga la página: Ctrl + Shift + R" -ForegroundColor Gray
Write-Host "      - Ve a: http://127.0.0.1:8000/us/centro-operaciones-espacial/" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. El caché ha sido limpiado automáticamente" -ForegroundColor White
Write-Host ""

Read-Host -Prompt "Presiona Enter para continuar"
