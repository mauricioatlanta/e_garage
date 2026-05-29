# Buscar duplicados en templates_canonical (el directorio que Django está leyendo)
# Ejecutar en PowerShell desde la raíz del repo

Write-Host "🔍 BUSCANDO TEMPLATES DUPLICADOS EN TEMPLATES_CANONICAL..." -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan

# ¿Cuántos 'base.html' tienes en templates_canonical?
Write-Host "📁 BASE.HTML EN TEMPLATES_CANONICAL:" -ForegroundColor Red
Get-ChildItem -Path "templates_canonical" -Recurse -Filter base.html | Select-Object FullName | ForEach-Object {
    Write-Host "   $($_.FullName)" -ForegroundColor White
}

Write-Host ""

# ¿Cuántos 'company_settings.html' tienes en templates_canonical?
Write-Host "📁 COMPANY_SETTINGS.HTML EN TEMPLATES_CANONICAL:" -ForegroundColor Red
Get-ChildItem -Path "templates_canonical" -Recurse -Filter company_settings.html | Select-Object FullName | ForEach-Object {
    Write-Host "   $($_.FullName)" -ForegroundColor White
}

Write-Host ""

# ¿Cuántos '_footer_company.html' tienes en templates_canonical?
Write-Host "📁 _FOOTER_COMPANY.HTML EN TEMPLATES_CANONICAL:" -ForegroundColor Red
Get-ChildItem -Path "templates_canonical" -Recurse -Filter _footer_company.html | Select-Object FullName | ForEach-Object {
    Write-Host "   $($_.FullName)" -ForegroundColor White
}

Write-Host ""

# Verificar que el directorio templates_canonical existe y tiene contenido
Write-Host "📂 VERIFICACIÓN DE TEMPLATES_CANONICAL:" -ForegroundColor Green
if (Test-Path "templates_canonical") {
    $totalFiles = (Get-ChildItem -Path "templates_canonical" -Recurse -File | Measure-Object).Count
    Write-Host "   ✅ Directorio existe con $totalFiles archivos" -ForegroundColor Green

    $commonDir = Get-ChildItem -Path "templates_canonical" -Recurse -Directory -Name "common" | Select-Object -First 1
    if ($commonDir) {
        Write-Host "   ✅ Subdirectorio 'common' encontrado" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ Subdirectorio 'common' NO encontrado" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Directorio 'templates_canonical' NO EXISTE" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "✅ BÚSQUEDA COMPLETADA" -ForegroundColor Green

# Si aparece más de uno en rutas distintas, ese duplica y puede estar siendo tomado por el loader primero
Write-Host ""
Write-Host "💡 INTERPRETACIÓN:" -ForegroundColor Yellow
Write-Host "   - Si ves MÁS DE UN base.html → Django puede estar usando el incorrecto" -ForegroundColor White
Write-Host "   - Si ves MÁS DE UN company_settings.html → Puede estar renderizando el viejo" -ForegroundColor White
Write-Host "   - Si ves MÁS DE UN _footer_company.html → El footer puede venir de otro lugar" -ForegroundColor White
Write-Host "   - Si templates_canonical NO existe → Django está usando otro directorio" -ForegroundColor White
