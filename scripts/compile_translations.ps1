# Script PowerShell para compilar archivos de traducción (.po) en producción
# Este script debe ejecutarse después de cada actualización de traducciones
# para asegurar que los archivos .mo estén actualizados y no haya impacto en rendimiento

Write-Host "🌐 Compilando archivos de traducción..." -ForegroundColor Cyan

# Activar entorno virtual si existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

# Compilar todos los archivos .po a .mo
Write-Host "📝 Ejecutando compilemessages..." -ForegroundColor Yellow
python manage.py compilemessages

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al compilar traducciones" -ForegroundColor Red
    exit 1
}

# Verificar que los archivos .mo se hayan generado correctamente
Write-Host "✅ Verificando archivos compilados..." -ForegroundColor Green

$localeDirs = @("locale", "taller\locale", "ubicacion\locale")

foreach ($localeDir in $localeDirs) {
    if (Test-Path $localeDir) {
        Write-Host "📁 Verificando $localeDir..." -ForegroundColor Cyan
        $moFiles = Get-ChildItem -Path $localeDir -Filter "*.mo" -Recurse
        foreach ($moFile in $moFiles) {
            Write-Host "  ✓ $($moFile.Name) compilado correctamente" -ForegroundColor Green
        }
    }
}

Write-Host "✅ Compilación de traducciones completada exitosamente" -ForegroundColor Green
Write-Host "📝 Los archivos .mo están listos para producción" -ForegroundColor Green


