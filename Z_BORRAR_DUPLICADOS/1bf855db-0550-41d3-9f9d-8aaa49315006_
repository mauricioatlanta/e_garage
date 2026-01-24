# Buscar duplicados que te estén "pisando" los templates
# Ejecutar en PowerShell desde la raíz del repo

Write-Host "🔍 BUSCANDO TEMPLATES DUPLICADOS..." -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

# ¿Cuántos 'base.html' tienes?
Write-Host "📁 BASE.HTML DUPLICADOS:" -ForegroundColor Red
Get-ChildItem -Path . -Recurse -Filter base.html | Select-Object FullName | ForEach-Object {
    Write-Host "   $($_.FullName)" -ForegroundColor White
}

Write-Host ""

# ¿Cuántos 'company_settings.html' tienes?
Write-Host "📁 COMPANY_SETTINGS.HTML DUPLICADOS:" -ForegroundColor Red
Get-ChildItem -Path . -Recurse -Filter company_settings.html | Select-Object FullName | ForEach-Object {
    Write-Host "   $($_.FullName)" -ForegroundColor White
}

Write-Host ""

# ¿Cuántos '_footer_company.html' tienes?
Write-Host "📁 _FOOTER_COMPANY.HTML DUPLICADOS:" -ForegroundColor Red
Get-ChildItem -Path . -Recurse -Filter _footer_company.html | Select-Object FullName | ForEach-Object {
    Write-Host "   $($_.FullName)" -ForegroundColor White
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ BÚSQUEDA COMPLETADA" -ForegroundColor Green

# Si aparece más de uno en rutas distintas, ese duplica y puede estar siendo tomado por el loader primero
Write-Host ""
Write-Host "💡 INTERPRETACIÓN:" -ForegroundColor Yellow
Write-Host "   - Si ves MÁS DE UN base.html → Django puede estar usando el incorrecto" -ForegroundColor White
Write-Host "   - Si ves MÁS DE UN company_settings.html → Puede estar renderizando el viejo" -ForegroundColor White
Write-Host "   - Si ves MÁS DE UN _footer_company.html → El footer puede venir de otro lugar" -ForegroundColor White
