# Script de checklist de salud para eGarage
# Ejecuta todas las verificaciones necesarias para confirmar que el sistema está sano

Write-Host "🚀 CHECKLIST DE SALUD DE EGARAGE" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green

$ErrorActionPreference = "Stop"
$exitCode = 0

function Test-Command {
    param($Command, $Description)
    Write-Host "🔍 $Description" -ForegroundColor Yellow
    try {
        Invoke-Expression $Command
        Write-Host "✅ $Description - OK" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ $Description - ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 1. Arranque mínimo
Write-Host "`n📋 1. ARRANQUE MÍNIMO" -ForegroundColor Cyan
if (-not (Test-Command '$env:DJANGO_SETTINGS_MODULE="gestion_taller.settings.min"; python manage.py check' "Django mínimo")) {
    $exitCode = 1
}

# 2. Arranque seguro (sin logging ruidoso)
Write-Host "`n📋 2. ARRANQUE SEGURO" -ForegroundColor Cyan
if (-not (Test-Command '$env:DJANGO_SETTINGS_MODULE="gestion_taller.settings"; $env:EGARAGE_SAFE_MODE="1"; python manage.py check' "Django modo seguro")) {
    $exitCode = 1
}

# 3. Migraciones y estado DB
Write-Host "`n📋 3. MIGRACIONES Y BASE DE DATOS" -ForegroundColor Cyan
if (-not (Test-Command 'python manage.py makemigrations --check' "Verificar migraciones pendientes")) {
    $exitCode = 1
}
if (-not (Test-Command 'python manage.py migrate --check' "Verificar estado de migraciones")) {
    $exitCode = 1
}

# 4. Archivos estáticos e i18n
Write-Host "`n📋 4. ARCHIVOS ESTÁTICOS E I18N" -ForegroundColor Cyan
if (-not (Test-Command 'python manage.py collectstatic --noinput --dry-run' "Verificar archivos estáticos")) {
    $exitCode = 1
}
if (-not (Test-Command 'python manage.py compilemessages --dry-run' "Verificar mensajes i18n")) {
    $exitCode = 1
}

# 5. Smoke tests personalizados
Write-Host "`n📋 5. SMOKE TESTS PERSONALIZADOS" -ForegroundColor Cyan
if (-not (Test-Command 'python tools/eg_diag.py' "Diagnóstico automatizado")) {
    $exitCode = 1
}

# 6. Verificar estructura de directorios críticos
Write-Host "`n📋 6. ESTRUCTURA DE DIRECTORIOS" -ForegroundColor Cyan
$criticalDirs = @("templates_canonical", "locale", "static", "media", "logs")
foreach ($dir in $criticalDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ Directorio $dir existe" -ForegroundColor Green
    } else {
        Write-Host "❌ Directorio $dir no existe" -ForegroundColor Red
        $exitCode = 1
    }
}

# Resumen final
Write-Host "`n" + ("=" * 60) -ForegroundColor Green
if ($exitCode -eq 0) {
    Write-Host "🎉 ¡SISTEMA COMPLETAMENTE SANO!" -ForegroundColor Green
    Write-Host "   Todos los checks pasaron exitosamente." -ForegroundColor Green
} else {
    Write-Host "⚠️  SE ENCONTRARON PROBLEMAS" -ForegroundColor Red
    Write-Host "   Revisa los errores anteriores antes de continuar." -ForegroundColor Red
}
Write-Host ("=" * 60) -ForegroundColor Green

exit $exitCode
