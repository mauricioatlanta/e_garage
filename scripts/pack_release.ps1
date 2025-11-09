# empaqueta una release excluyendo venv, __pycache__, media, static_root, .git y zips previos
$ErrorActionPreference = 'Stop'

# Obtener versión del sistema
$versionFile = "taller/version.py"
$version = "unknown"
if (Test-Path $versionFile) {
    $content = Get-Content $versionFile -Raw
    if ($content -match '__version__\s*=\s*"([^"]+)"') {
        $version = $matches[1]
    }
}

$stamp   = Get-Date -Format "yyyy-MM-dd_HHmm"
$release = "egarage_v${version}_${stamp}.zip"

# 1) staging temporal
$staging = Join-Path $env:TEMP "eg_release_$stamp"
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Path $staging | Out-Null

# 2) copia del proyecto -> staging, EXCLUYENDO carpetas/archivos
# /MIR = espejo; /XD = excluir dirs; /XF = excluir files; /R:0 /W:0 = sin reintentos
robocopy . $staging /MIR `
  /XD ".git" ".venv" "venv" "media" "static_root" `
  /XD "__pycache__" `
  /XF "*.zip" "*.pyc" `
  /R:0 /W:0 | Out-Null

# 3) comprimir staging -> zip
if (Test-Path $release) { Remove-Item $release -Force }
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $release -CompressionLevel Optimal

# 4) limpiar staging
Remove-Item $staging -Recurse -Force

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "✅ RELEASE EMPAQUETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Archivo: " -NoNewline -ForegroundColor Yellow
Write-Host "$release" -ForegroundColor White
Write-Host "🏷️  Versión: " -NoNewline -ForegroundColor Yellow
Write-Host "$version" -ForegroundColor White
Write-Host "📅 Fecha: " -NoNewline -ForegroundColor Yellow
Write-Host "$stamp" -ForegroundColor White
Write-Host ""
$fileSize = (Get-Item $release).Length / 1MB
Write-Host "💾 Tamaño: " -NoNewline -ForegroundColor Yellow
Write-Host ("{0:N2} MB" -f $fileSize) -ForegroundColor White
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
