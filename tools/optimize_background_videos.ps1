# optimize_background_videos.ps1
# Script para optimizar videos de fondo con ffmpeg
param(
  [string]$Root = "E:\projecto\e_garage",
  [switch]$DryRun = $false
)

Write-Host "OPTIMIZACION DE VIDEOS DE FONDO" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Verificar si ffmpeg está disponible
try {
  $ffmpegVersion = & ffmpeg -version 2>&1 | Select-Object -First 1
  Write-Host "FFmpeg encontrado: $ffmpegVersion" -ForegroundColor Green
} catch {
  Write-Host "FFmpeg no encontrado. Instala ffmpeg para optimizar videos." -ForegroundColor Yellow
  Write-Host "Descarga desde: https://ffmpeg.org/download.html" -ForegroundColor Gray
  exit 1
}

$bgDir = Join-Path $Root "static\taller\media\bg"
$backupDir = Join-Path $Root "tools\backup\videos_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Crear backup
if (-not $DryRun) {
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
  Copy-Item "$bgDir\*" $backupDir -Force
  Write-Host "Backup creado en: $backupDir" -ForegroundColor Green
}

# Optimizar WebM (VP9)
$webmInput = Join-Path $bgDir "bg_particles.webm"
$webmOutput = Join-Path $bgDir "bg_particles_optimized.webm"

if (Test-Path $webmInput) {
  Write-Host "`nOptimizando WebM..." -ForegroundColor Blue

  $webmCmd = "ffmpeg -i `"$webmInput`" -c:v libvpx-vp9 -b:v 1500k -crf 30 -an -movflags +faststart `"$webmOutput`""

  if ($DryRun) {
    Write-Host "[DRY RUN] Comando: $webmCmd" -ForegroundColor Yellow
  } else {
    Write-Host "Ejecutando: $webmCmd" -ForegroundColor Gray
    Invoke-Expression $webmCmd

    if (Test-Path $webmOutput) {
      $originalSize = (Get-Item $webmInput).Length
      $optimizedSize = (Get-Item $webmOutput).Length
      $savings = [math]::Round((($originalSize - $optimizedSize) / $originalSize) * 100, 2)

      Write-Host "WebM optimizado:" -ForegroundColor Green
      Write-Host "  Original: $([math]::Round($originalSize / 1MB, 2)) MB" -ForegroundColor Gray
      Write-Host "  Optimizado: $([math]::Round($optimizedSize / 1MB, 2)) MB" -ForegroundColor Gray
      Write-Host "  Ahorro: $savings%" -ForegroundColor Green

      # Reemplazar original
      Move-Item $webmOutput $webmInput -Force
    }
  }
}

# Optimizar MP4 (H.264)
$mp4Input = Join-Path $bgDir "bg_intro_6s.mp4"
$mp4Output = Join-Path $bgDir "bg_intro_6s_optimized.mp4"

if (Test-Path $mp4Input) {
  Write-Host "`nOptimizando MP4..." -ForegroundColor Blue

  $mp4Cmd = "ffmpeg -i `"$mp4Input`" -c:v libx264 -preset slow -crf 23 -an -movflags +faststart `"$mp4Output`""

  if ($DryRun) {
    Write-Host "[DRY RUN] Comando: $mp4Cmd" -ForegroundColor Yellow
  } else {
    Write-Host "Ejecutando: $mp4Cmd" -ForegroundColor Gray
    Invoke-Expression $mp4Cmd

    if (Test-Path $mp4Output) {
      $originalSize = (Get-Item $mp4Input).Length
      $optimizedSize = (Get-Item $mp4Output).Length
      $savings = [math]::Round((($originalSize - $optimizedSize) / $originalSize) * 100, 2)

      Write-Host "MP4 optimizado:" -ForegroundColor Green
      Write-Host "  Original: $([math]::Round($originalSize / 1MB, 2)) MB" -ForegroundColor Gray
      Write-Host "  Optimizado: $([math]::Round($optimizedSize / 1MB, 2)) MB" -ForegroundColor Gray
      Write-Host "  Ahorro: $savings%" -ForegroundColor Green

      # Reemplazar original
      Move-Item $mp4Output $mp4Input -Force
    }
  }
}

Write-Host "`nOPTIMIZACION COMPLETADA" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green

if (-not $DryRun) {
  Write-Host "Backup disponible en: $backupDir" -ForegroundColor Gray
  Write-Host "Videos optimizados en: $bgDir" -ForegroundColor Gray
} else {
  Write-Host "Para aplicar la optimizacion, ejecuta:" -ForegroundColor Cyan
  Write-Host "  .\tools\optimize_background_videos.ps1 -Root `"$Root`"" -ForegroundColor White
}
