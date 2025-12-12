# Script de despliegue seguro para Windows PowerShell
# Uso: .\scripts\deploy_produccion_seguro.ps1 [directorio_destino]

param(
    [string]$DestDir = "deploy"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "🔒 DESPLIEGUE SEGURO - EGARAGE" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# Verificar que el código está ofuscado
if (-not (Test-Path "taller\utils\motor_ia_core_compiled")) {
    Write-Host "❌ ERROR: Código ofuscado no encontrado" -ForegroundColor Red
    Write-Host "⚠️  Ejecuta primero: python scripts\ofuscar_motor_ia.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Código ofuscado encontrado" -ForegroundColor Green
Write-Host ""

# Crear directorio de despliegue
Write-Host "[1/5] Creando directorio de despliegue..." -ForegroundColor Blue
if (Test-Path $DestDir) {
    Remove-Item -Recurse -Force $DestDir
}
New-Item -ItemType Directory -Path $DestDir | Out-Null

# Copiar archivos del proyecto
Write-Host "[2/5] Copiando archivos del proyecto..." -ForegroundColor Blue

# Copiar todo excepto archivos/carpetas excluidos
Get-ChildItem -Path . -Recurse -File | Where-Object {
    $_.FullName -notmatch "\\venv\\" -and
    $_.FullName -notmatch "\\.venv\\" -and
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\.git\\" -and
    $_.FullName -notmatch "\\__pycache__\\" -and
    $_.FullName -notmatch "\\motor_ia_core_compiled\\" -and
    $_.Name -ne "motor_ia_core.py" -and
    $_.Extension -ne ".pyc" -and
    $_.Extension -ne ".log" -and
    $_.Name -ne "db.sqlite3"
} | ForEach-Object {
    $relativePath = $_.FullName.Substring((Get-Location).Path.Length + 1)
    $destPath = Join-Path $DestDir $relativePath
    $destDirPath = Split-Path $destPath -Parent
    if (-not (Test-Path $destDirPath)) {
        New-Item -ItemType Directory -Path $destDirPath -Force | Out-Null
    }
    Copy-Item $_.FullName -Destination $destPath -Force
}

# Copiar código ofuscado
Write-Host "[3/5] Copiando código ofuscado..." -ForegroundColor Blue
$obfuscatedSource = "taller\utils\motor_ia_core_compiled"
$obfuscatedDest = Join-Path $DestDir "taller\utils\motor_ia_core_compiled"
Copy-Item -Recurse -Force $obfuscatedSource $obfuscatedDest

# Verificar que el código fuente NO está en el despliegue
Write-Host "[4/5] Verificando seguridad..." -ForegroundColor Blue

$sourceFile = Join-Path $DestDir "taller\utils\motor_ia_core.py"
if (Test-Path $sourceFile) {
    Write-Host "❌ ERROR CRÍTICO: Código fuente encontrado en despliegue" -ForegroundColor Red
    Write-Host "   El archivo motor_ia_core.py NO debe estar en producción" -ForegroundColor Red
    Remove-Item $sourceFile -Force
    Write-Host "⚠️  Archivo eliminado automáticamente" -ForegroundColor Yellow
}

# Verificar que el código ofuscado SÍ está
if (-not (Test-Path $obfuscatedDest)) {
    Write-Host "❌ ERROR: Código ofuscado no encontrado en despliegue" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Verificación de seguridad completada" -ForegroundColor Green

# Crear archivo de verificación
Write-Host "[5/5] Creando archivo de verificación..." -ForegroundColor Blue
$deployInfo = @"
Despliegue Seguro de eGarage
Fecha: $(Get-Date)
Versión: $(git rev-parse --short HEAD 2>$null)

✅ Código fuente del core de IA EXCLUIDO
✅ Código ofuscado INCLUIDO
✅ Listo para producción

IMPORTANTE:
- NO contiene motor_ia_core.py (código fuente)
- SÍ contiene motor_ia_core_compiled/ (código ofuscado)
- El wrapper motor_ia.py importará automáticamente el código ofuscado
"@

$deployInfo | Out-File -FilePath (Join-Path $DestDir "DEPLOY_INFO.txt") -Encoding UTF8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ DESPLIEGUE COMPLETADO" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "📦 Directorio de despliegue: $DestDir" -ForegroundColor Blue
Write-Host "📄 Información: $DestDir\DEPLOY_INFO.txt" -ForegroundColor Blue
Write-Host ""

Write-Host "⚠️  RECORDATORIO:" -ForegroundColor Yellow
Write-Host "   - Verifica que motor_ia_core.py NO está en $DestDir"
Write-Host "   - Verifica que motor_ia_core_compiled\ SÍ está en $DestDir"
Write-Host "   - Ejecuta tests en el servidor antes de activar"
Write-Host ""





