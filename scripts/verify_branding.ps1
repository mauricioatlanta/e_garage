# Script de verificación del sistema de branding unificado
# Uso: .\scripts\verify_branding.ps1

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "🎨 VERIFICACIÓN DEL SISTEMA DE BRANDING UNIFICADO" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan

$checks = @()

# Check 1: Context processor file exists
Write-Host "`n[1/7] Verificando context processor..." -ForegroundColor Yellow
if (Test-Path "taller/context_processors/company_branding_unified.py") {
    Write-Host "  ✅ Context processor existe" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "  ❌ Context processor NO encontrado" -ForegroundColor Red
    $checks += $false
}

# Check 2: Template include exists
Write-Host "`n[2/7] Verificando template include..." -ForegroundColor Yellow
if (Test-Path "templates/_includes/brand_header.html") {
    Write-Host "  ✅ Template include existe" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "  ❌ Template include NO encontrado" -ForegroundColor Red
    $checks += $false
}

# Check 3: Settings has defaults
Write-Host "`n[3/7] Verificando settings.py..." -ForegroundColor Yellow
$settingsContent = Get-Content "gestion_taller/settings.py" -Raw
if ($settingsContent -match "DEFAULT_BRAND_LOGO_URL") {
    Write-Host "  ✅ Defaults de branding configurados" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "  ❌ Defaults de branding NO encontrados" -ForegroundColor Red
    $checks += $false
}

# Check 4: base.html uses include
Write-Host "`n[4/7] Verificando base.html..." -ForegroundColor Yellow
$baseContent = Get-Content "templates/base.html" -Raw
if ($baseContent -match 'include "_includes/brand_header.html"') {
    Write-Host "  ✅ base.html usa el include correcto" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "  ❌ base.html NO usa el include" -ForegroundColor Red
    $checks += $false
}

# Check 5: base.html uses BRAND variables
Write-Host "`n[5/7] Verificando variables BRAND en CSS..." -ForegroundColor Yellow
if ($baseContent -match 'BRAND\.primary_color') {
    Write-Host "  ✅ Variables BRAND en uso" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "  ❌ Variables BRAND NO encontradas" -ForegroundColor Red
    $checks += $false
}

# Check 6: Context processor registered in settings
Write-Host "`n[6/7] Verificando registro del context processor..." -ForegroundColor Yellow
if ($settingsContent -match "taller\.context_processors\.company_branding") {
    Write-Host "  ✅ Context processor registrado" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "  ❌ Context processor NO registrado" -ForegroundColor Red
    $checks += $false
}

# Check 7: Documentation exists
Write-Host "`n[7/7] Verificando documentación..." -ForegroundColor Yellow
if (Test-Path "docs/BRANDING_UNIFICADO_COMPLETADO.md") {
    Write-Host "  ✅ Documentación completa existe" -ForegroundColor Green
    $checks += $true
} else {
    Write-Host "  ❌ Documentación NO encontrada" -ForegroundColor Red
    $checks += $false
}

# Summary
Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "📊 RESUMEN" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

$passed = ($checks | Where-Object { $_ -eq $true }).Count
$total = $checks.Count
if ($total -gt 0) {
    $percentage = [math]::Round(($passed / $total) * 100, 2)
} else {
    $percentage = 0
}

Write-Host "`nChecks pasados: $passed/$total ($percentage%)" -ForegroundColor White

if ($passed -eq $total) {
    Write-Host "`n🎉 ¡TODOS LOS CHECKS PASARON!" -ForegroundColor Green
    Write-Host "`n✅ El sistema de branding unificado está correctamente instalado" -ForegroundColor Green
    Write-Host "`n💡 Próximos pasos:" -ForegroundColor Cyan
    Write-Host "   1. Ejecuta: python manage.py check_logo" -ForegroundColor White
    Write-Host "   2. Visita: http://127.0.0.1:8000/us/centro-operaciones-espacial/" -ForegroundColor White
    Write-Host "   3. Verifica que el logo aparezca en el header" -ForegroundColor White
} else {
    Write-Host "`n⚠️  ALGUNOS CHECKS FALLARON" -ForegroundColor Yellow
    Write-Host "`nRevisa los errores arriba y corrige los problemas." -ForegroundColor White
}

Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan

Read-Host -Prompt "`nPresiona Enter para continuar"
