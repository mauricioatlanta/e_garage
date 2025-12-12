# Script para subir cambios del modelo Tecnico al servidor
# Ejecutar desde PowerShell: .\subir_cambios_tecnico_rol.ps1

$serverUser = "atlantareciclajes"
$serverHost = "ssh.pythonanywhere.com"
$serverBasePath = "/home/atlantareciclajes/apps/egarage/current"
$localBasePath = "E:\projecto\e_garage"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Subiendo cambios del modelo Tecnico" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Archivos a subir
$filesToUpload = @(
    @{
        Local = "$localBasePath\taller\models\tecnico.py"
        Remote = "$serverBasePath/taller/models/tecnico.py"
        Description = "Modelo Tecnico con ROL_CHOICES"
    },
    @{
        Local = "$localBasePath\taller\configuracion\rubros_logic.py"
        Remote = "$serverBasePath/taller/configuracion/rubros_logic.py"
        Description = "Lógica de rubros actualizada"
    },
    @{
        Local = "$localBasePath\taller\documentos\views_country_aware.py"
        Remote = "$serverBasePath/taller/documentos/views_country_aware.py"
        Description = "Vistas de documentos actualizadas"
    }
)

Write-Host "Archivos a subir:" -ForegroundColor Yellow
foreach ($file in $filesToUpload) {
    Write-Host "  - $($file.Description)" -ForegroundColor Gray
    Write-Host "    Local: $($file.Local)" -ForegroundColor DarkGray
    Write-Host "    Remote: $($file.Remote)" -ForegroundColor DarkGray
}
Write-Host ""

# Verificar que los archivos locales existen
Write-Host "Verificando archivos locales..." -ForegroundColor Cyan
foreach ($file in $filesToUpload) {
    if (-not (Test-Path $file.Local)) {
        Write-Host "ERROR: No se encuentra el archivo: $($file.Local)" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "  ✓ $($file.Description)" -ForegroundColor Green
    }
}
Write-Host ""

# Confirmar antes de subir
$confirm = Read-Host "¿Continuar con la subida de archivos? (s/n)"
if ($confirm -ne "s" -and $confirm -ne "S") {
    Write-Host "Operación cancelada." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Subiendo archivos..." -ForegroundColor Cyan
Write-Host ""

# Subir cada archivo
foreach ($file in $filesToUpload) {
    Write-Host "Subiendo: $($file.Description)..." -ForegroundColor Yellow
    
    try {
        $scpCommand = "scp `"$($file.Local)`" ${serverUser}@${serverHost}:`"$($file.Remote)`""
        
        Write-Host "  Comando: $scpCommand" -ForegroundColor DarkGray
        
        # Ejecutar SCP
        & scp $file.Local "${serverUser}@${serverHost}:$($file.Remote)"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Subido exitosamente" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Error al subir (código: $LASTEXITCODE)" -ForegroundColor Red
            Write-Host "    Verifica la ruta del servidor o tus credenciales SSH" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Proceso completado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "1. Conéctate al servidor SSH" -ForegroundColor White
Write-Host "2. Ejecuta: python manage.py check" -ForegroundColor White
Write-Host "3. Reinicia la aplicación en PythonAnywhere (Web > Reload)" -ForegroundColor White
Write-Host ""







