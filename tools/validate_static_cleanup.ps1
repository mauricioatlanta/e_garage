# validate_static_cleanup.ps1
# Valida que la limpieza de archivos estáticos sea correcta
param(
  [string]$Root = "E:\projecto\e_garage",
  [string]$StaticDir = "E:\projecto\e_garage\static"
)

Write-Host "🔍 VALIDACIÓN DE LIMPIEZA DE ARCHIVOS ESTÁTICOS" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

$errors = @()
$warnings = @()
$success = @()

# Función para agregar error
function Add-Error {
  param([string]$Message)
  $errors += $Message
  Write-Host "❌ ERROR: $Message" -ForegroundColor Red
}

# Función para agregar warning
function Add-Warning {
  param([string]$Message)
  $warnings += $Message
  Write-Host "⚠️ WARNING: $Message" -ForegroundColor Yellow
}

# Función para agregar éxito
function Add-Success {
  param([string]$Message)
  $success += $Message
  Write-Host "✅ $Message" -ForegroundColor Green
}

# VALIDACIÓN 1: Estructura de directorios
Write-Host "`n📁 VALIDANDO ESTRUCTURA DE DIRECTORIOS..." -ForegroundColor Blue

$expectedDirs = @(
  "taller\common\css",
  "taller\common\js",
  "taller\common\img",
  "taller\common\fonts",
  "taller\common\media",
  "taller\cl\css",
  "taller\cl\js",
  "taller\cl\img",
  "taller\us\css",
  "taller\us\js",
  "taller\us\img",
  "vendor"
)

foreach ($dir in $expectedDirs) {
  $fullPath = Join-Path $StaticDir $dir
  if (Test-Path $fullPath) {
    Add-Success "Directorio existe: $dir"
  } else {
    Add-Warning "Directorio faltante: $dir"
  }
}

# VALIDACIÓN 2: Archivos problemáticos
Write-Host "`n🚫 VALIDANDO AUSENCIA DE ARCHIVOS PROBLEMÁTICOS..." -ForegroundColor Blue

$problematicPatterns = @(
  "*.map",
  "*.psd",
  "*.ai",
  "*.fig",
  "*.zip",
  "*.rar",
  "*.7z"
)

foreach ($pattern in $problematicPatterns) {
  $files = Get-ChildItem -Path $StaticDir -Recurse -Filter $pattern -ErrorAction SilentlyContinue
  if ($files.Count -gt 0) {
    Add-Error "Archivos problemáticos encontrados ($pattern): $($files.Count)"
    foreach ($file in $files) {
      Write-Host "   - $($file.FullName.Replace($StaticDir, ''))" -ForegroundColor Gray
    }
  } else {
    Add-Success "No hay archivos $pattern"
  }
}

# VALIDACIÓN 3: Archivos no-minificados vs minificados
Write-Host "`n📦 VALIDANDO VERSIONES MINIFICADAS..." -ForegroundColor Blue

$cssFiles = Get-ChildItem -Path $StaticDir -Recurse -Filter "*.css" -ErrorAction SilentlyContinue
$jsFiles = Get-ChildItem -Path $StaticDir -Recurse -Filter "*.js" -ErrorAction SilentlyContinue

foreach ($file in $cssFiles) {
  if ($file.Name -notmatch '\.min\.css$') {
    $minFile = $file.Name -replace '\.css$', '.min.css'
    $minPath = Join-Path $file.Directory $minFile
    if (Test-Path $minPath) {
      Add-Warning "Archivo no-minificado coexiste con minificado: $($file.Name)"
    }
  }
}

foreach ($file in $jsFiles) {
  if ($file.Name -notmatch '\.min\.js$') {
    $minFile = $file.Name -replace '\.js$', '.min.js'
    $minPath = Join-Path $file.Directory $minFile
    if (Test-Path $minPath) {
      Add-Warning "Archivo no-minificado coexiste con minificado: $($file.Name)"
    }
  }
}

# VALIDACIÓN 4: Nombres de archivos
Write-Host "`n🏷️ VALIDANDO NOMBRES DE ARCHIVOS..." -ForegroundColor Blue

$allFiles = Get-ChildItem -Path $StaticDir -Recurse -File -ErrorAction SilentlyContinue
foreach ($file in $allFiles) {
  $fileName = $file.Name

  # Verificar mayúsculas
  if ($fileName -cmatch '[A-Z]') {
    Add-Warning "Archivo con mayúsculas: $fileName"
  }

  # Verificar espacios
  if ($fileName -match ' ') {
    Add-Error "Archivo con espacios: $fileName"
  }

  # Verificar caracteres especiales
  if ($fileName -match '[^\w\-\.]') {
    Add-Warning "Archivo con caracteres especiales: $fileName"
  }

  # Verificar nombres problemáticos
  if ($fileName -match '(experimental|temp|tmp|test|debug|old|backup|copy|v\d+)$') {
    Add-Warning "Archivo con nombre problemático: $fileName"
  }
}

# VALIDACIÓN 5: Duplicados
Write-Host "`n🔄 VALIDANDO DUPLICADOS..." -ForegroundColor Blue

$fileHashes = @{}
foreach ($file in $allFiles) {
  try {
    $hash = Get-FileHash -Path $file.FullName -Algorithm SHA1
    if ($fileHashes.ContainsKey($hash.Hash)) {
      Add-Error "Archivo duplicado encontrado: $($file.Name) (igual a $($fileHashes[$hash.Hash]))"
    } else {
      $fileHashes[$hash.Hash] = $file.Name
    }
  } catch {
    Add-Warning "No se pudo calcular hash para: $($file.Name)"
  }
}

# VALIDACIÓN 6: Tamaño total
Write-Host "`n📊 VALIDANDO TAMAÑO TOTAL..." -ForegroundColor Blue

$totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)

Add-Success "Tamaño total: $totalSizeMB MB"

if ($totalSizeMB -gt 50) {
  Add-Warning "Tamaño total muy grande: $totalSizeMB MB (considerar optimización)"
}

# VALIDACIÓN 7: Archivos críticos
Write-Host "`n🎯 VALIDANDO ARCHIVOS CRÍTICOS..." -ForegroundColor Blue

$criticalFiles = @(
  "taller\common\css\style.css",
  "taller\common\css\dashboard.css",
  "taller\common\js\main.js",
  "taller\common\img\logo.png"
)

foreach ($criticalFile in $criticalFiles) {
  $fullPath = Join-Path $StaticDir $criticalFile
  if (Test-Path $fullPath) {
    Add-Success "Archivo crítico existe: $criticalFile"
  } else {
    Add-Warning "Archivo crítico faltante: $criticalFile"
  }
}

# RESUMEN FINAL
Write-Host "`n📋 RESUMEN DE VALIDACIÓN" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

Write-Host "✅ Éxitos: $($success.Count)" -ForegroundColor Green
Write-Host "⚠️ Warnings: $($warnings.Count)" -ForegroundColor Yellow
Write-Host "❌ Errores: $($errors.Count)" -ForegroundColor Red

if ($errors.Count -eq 0) {
  Write-Host "`n🎉 VALIDACIÓN EXITOSA - La limpieza está correcta" -ForegroundColor Green
} else {
  Write-Host "`n⚠️ VALIDACIÓN CON PROBLEMAS - Revisar errores" -ForegroundColor Yellow
}

# Generar reporte
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportFile = Join-Path $Root "tools\reports\validation_report_$timestamp.txt"

$report = @"
VALIDACIÓN DE LIMPIEZA DE ARCHIVOS ESTÁTICOS
===========================================
Fecha: $(Get-Date)
Directorio: $StaticDir

ESTADÍSTICAS:
- Total archivos: $($allFiles.Count)
- Tamaño total: $totalSizeMB MB
- Éxitos: $($success.Count)
- Warnings: $($warnings.Count)
- Errores: $($errors.Count)

ERRORES:
"@

foreach ($error in $errors) {
  $report += "`n- $error"
}

$report += "`n`nWARNINGS:"
foreach ($warning in $warnings) {
  $report += "`n- $warning"
}

$report += "`n`nÉXITOS:"
foreach ($s in $success) {
  $report += "`n- $s"
}

Set-Content -Path $reportFile -Value $report -Encoding UTF8
Write-Host "`n📄 Reporte guardado en: $reportFile" -ForegroundColor Blue

Write-Host "`n===============================================" -ForegroundColor Cyan
