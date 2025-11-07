# apply_static_cleanup.ps1
# Script completo para limpieza de archivos estáticos en producción
param(
  [string]$Root = "E:\projecto\e_garage",
  [string]$StaticDir = "E:\projecto\e_garage\static",
  [switch]$DryRun = $false,
  [switch]$Force = $false
)

# Configuración
$ReportsDir = Join-Path $Root "tools\reports"
$QuarantineDir = Join-Path $Root "tools\quarantine"
$BackupDir = Join-Path $Root "tools\backup\static_cleanup"

# Crear directorios necesarios
New-Item -ItemType Directory -Force -Path $QuarantineDir | Out-Null
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host "LIMPIEZA DE ARCHIVOS ESTATICOS - eGarage" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Directorio base: $Root" -ForegroundColor Gray
Write-Host "Directorio static: $StaticDir" -ForegroundColor Gray
Write-Host "Modo: $(if ($DryRun) { 'DRY RUN' } else { 'APLICAR CAMBIOS' })" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Red' })
Write-Host ""

# Función para crear backup
function Backup-File {
  param([string]$FilePath)
  if (Test-Path $FilePath) {
    $relativePath = $FilePath.Replace("$StaticDir\", "")
    $backupPath = Join-Path $BackupDir $relativePath
    $backupParent = Split-Path $backupPath -Parent
    New-Item -ItemType Directory -Force -Path $backupParent | Out-Null
    Copy-Item $FilePath $backupPath -Force
    return $backupPath
  }
  return $null
}

# Función para mover a cuarentena
function Move-ToQuarantine {
  param([string]$FilePath, [string]$Reason)
  if (Test-Path $FilePath) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $quarantineSubDir = Join-Path $QuarantineDir "deleted_$timestamp"
    $relativePath = $FilePath.Replace("$StaticDir\", "")
    $quarantinePath = Join-Path $quarantineSubDir $relativePath
    $quarantineParent = Split-Path $quarantinePath -Parent
    
    New-Item -ItemType Directory -Force -Path $quarantineParent | Out-Null
    Move-Item $FilePath $quarantinePath -Force
    
    # Log del motivo
    $logFile = Join-Path $quarantineSubDir "deletion_log.txt"
    Add-Content -Path $logFile -Value "$(Get-Date): $relativePath - $Reason"
    
    return $quarantinePath
  }
  return $null
}

# Función para normalizar nombre de archivo
function Normalize-Filename {
  param([string]$Filename)
  # Convertir a minúsculas
  $normalized = $Filename.ToLower()
  # Reemplazar espacios y caracteres especiales con guiones
  $normalized = $normalized -replace '[^\w\-\.]', '-'
  # Limpiar múltiples guiones
  $normalized = $normalized -replace '-+', '-'
  # Remover guiones al inicio y final
  $normalized = $normalized.Trim('-')
  return $normalized
}

# Función para determinar directorio objetivo
function Get-TargetDirectory {
  param([string]$FilePath, [string]$FileType)
  
  $pathLower = $FilePath.ToLower()
  
  # Determinar país/idioma
  $country = "common"
  if ($pathLower -match '\bcl\b|chile') { $country = "cl" }
  elseif ($pathLower -match '\bus\b|usa|united') { $country = "us" }
  
  # Mapeo de tipos a directorios
  switch ($FileType) {
    "CSS" { return "taller\$country\css" }
    "JS" { return "taller\$country\js" }
    "IMG" { return "taller\$country\img" }
    "FONT" { return "taller\$country\fonts" }
    "VIDEO" { return "taller\$country\media" }
    "AUDIO" { return "taller\$country\media" }
    default { return "taller\$country\media" }
  }
}

# PASO 1: Cargar datos de auditoría
Write-Host "PASO 1: Cargando datos de auditoria..." -ForegroundColor Green

$auditCsv = Join-Path $ReportsDir "audit_static.csv"
if (-not (Test-Path $auditCsv)) {
  Write-Error "No se encontró audit_static.csv. Ejecuta primero audit_static.py"
  exit 1
}

$auditData = Import-Csv $auditCsv
Write-Host "   ✅ Cargados $($auditData.Count) archivos" -ForegroundColor Green

# PASO 2: Identificar archivos para borrar
Write-Host "`n🗑️ PASO 2: Identificando archivos para borrar..." -ForegroundColor Red

$toDelete = @()
$toMove = @()

foreach ($file in $auditData) {
  $filePath = Join-Path $StaticDir $file.path
  $fileName = $file.name
  $fileType = $file.type
  $isDuplicate = $file.is_duplicate -eq "True"
  $hasIssues = $file.has_issues -eq "True"
  
  # Reglas de borrado para producción
  $shouldDelete = $false
  $deleteReason = ""
  
  # 1. Archivos .map (source maps)
  if ($fileName -match '\.map$') {
    $shouldDelete = $true
    $deleteReason = "Source map (no necesario en producción)"
  }
  
  # 2. Archivos de diseño (.psd, .ai, .fig)
  elseif ($fileName -match '\.(psd|ai|fig)$') {
    $shouldDelete = $true
    $deleteReason = "Archivo de diseño (no necesario en producción)"
  }
  
  # 3. Archivos comprimidos (.zip, .rar)
  elseif ($fileName -match '\.(zip|rar|7z)$') {
    $shouldDelete = $true
    $deleteReason = "Archivo comprimido (no necesario en producción)"
  }
  
  # 4. Archivos no-minificados cuando existe el .min
  elseif ($fileType -in @("CSS", "JS") -and $fileName -notmatch '\.min\.') {
    $minFile = $fileName -replace '\.(css|js)$', '.min.$1'
    $minPath = Join-Path (Split-Path $filePath -Parent) $minFile
    if (Test-Path $minPath) {
      $shouldDelete = $true
      $deleteReason = "Archivo no-minificado (existe versión minificada)"
    }
  }
  
  # 5. Duplicados por hash (mantener solo uno)
  elseif ($isDuplicate) {
    # Mantener el primero, borrar los demás
    $hash = $file.sha1
    $firstOccurrence = $auditData | Where-Object { $_.sha1 -eq $hash } | Select-Object -First 1
    if ($file.path -ne $firstOccurrence.path) {
      $shouldDelete = $true
      $deleteReason = "Duplicado por hash (mantener: $($firstOccurrence.path))"
    }
  }
  
  # 6. Archivos experimentales o temporales
  elseif ($fileName -match '(experimental|temp|tmp|test|debug|old|backup|copy|v\d+)$') {
    $shouldDelete = $true
    $deleteReason = "Archivo experimental/temporal"
  }
  
  if ($shouldDelete) {
    $toDelete += @{
      Path = $filePath
      Reason = $deleteReason
      OriginalPath = $file.path
    }
  } else {
    # Archivos para mover/reorganizar
    $toMove += @{
      Path = $filePath
      OriginalPath = $file.path
      Type = $fileType
      HasIssues = $hasIssues
    }
  }
}

Write-Host "   📋 Archivos para borrar: $($toDelete.Count)" -ForegroundColor Red
Write-Host "   📁 Archivos para mover: $($toMove.Count)" -ForegroundColor Blue

# Mostrar resumen de borrados
if ($toDelete.Count -gt 0) {
  Write-Host "`n   🗑️ ARCHIVOS PARA BORRAR:" -ForegroundColor Red
  foreach ($item in $toDelete | Select-Object -First 10) {
    Write-Host "      - $($item.OriginalPath) ($($item.Reason))" -ForegroundColor Gray
  }
  if ($toDelete.Count -gt 10) {
    Write-Host "      ... y $($toDelete.Count - 10) más" -ForegroundColor Gray
  }
}

# PASO 3: Aplicar borrados
if ($toDelete.Count -gt 0) {
  Write-Host "`n🗑️ PASO 3: Aplicando borrados..." -ForegroundColor Red
  
  if ($DryRun) {
    Write-Host "   [DRY RUN] Se borrarían $($toDelete.Count) archivos" -ForegroundColor Yellow
  } else {
    $deleted = 0
    foreach ($item in $toDelete) {
      if (Test-Path $item.Path) {
        $quarantinePath = Move-ToQuarantine -FilePath $item.Path -Reason $item.Reason
        if ($quarantinePath) {
          $deleted++
          Write-Host "   ✅ Borrado: $($item.OriginalPath)" -ForegroundColor Green
        }
      }
    }
    Write-Host "   📊 Total borrados: $deleted" -ForegroundColor Green
  }
}

# PASO 4: Reorganizar archivos restantes
if ($toMove.Count -gt 0) {
  Write-Host "`n📁 PASO 4: Reorganizando archivos..." -ForegroundColor Blue
  
  $moved = 0
  $errors = 0
  
  foreach ($item in $toMove) {
    $originalPath = $item.Path
    $fileName = Split-Path $originalPath -Leaf
    $normalizedName = Normalize-Filename -Filename $fileName
    $targetDir = Get-TargetDirectory -FilePath $item.OriginalPath -FileType $item.Type
    $targetPath = Join-Path $StaticDir $targetDir $normalizedName
    
    # Evitar colisiones
    $counter = 1
    $originalTarget = $targetPath
    while (Test-Path $targetPath) {
      $stem = [System.IO.Path]::GetFileNameWithoutExtension($originalTarget)
      $ext = [System.IO.Path]::GetExtension($originalTarget)
      $targetPath = Join-Path (Split-Path $originalTarget -Parent) "$stem-$counter$ext"
      $counter++
    }
    
    if ($DryRun) {
      Write-Host "   [DRY RUN] $($item.OriginalPath) → $($targetPath.Replace("$StaticDir\", ""))" -ForegroundColor Yellow
    } else {
      try {
        # Crear backup
        $backupPath = Backup-File -FilePath $originalPath
        
        # Crear directorio objetivo
        $targetParent = Split-Path $targetPath -Parent
        New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
        
        # Mover archivo
        Move-Item $originalPath $targetPath -Force
        $moved++
        
        $status = if ($item.HasIssues) { "⚠️" } else { "✅" }
        Write-Host "   $status $($item.OriginalPath) → $($targetPath.Replace("$StaticDir\", ""))" -ForegroundColor Green
        
      } catch {
        $errors++
        Write-Host "   ❌ Error moviendo $($item.OriginalPath): $($_.Exception.Message)" -ForegroundColor Red
      }
    }
  }
  
  if (-not $DryRun) {
    Write-Host "   📊 Total movidos: $moved" -ForegroundColor Green
    Write-Host "   ❌ Errores: $errors" -ForegroundColor $(if ($errors -gt 0) { 'Red' } else { 'Green' })
  }
}

# PASO 5: Generar reporte final
Write-Host "`n📊 PASO 5: Generando reporte final..." -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportFile = Join-Path $ReportsDir "cleanup_report_$timestamp.txt"

$report = @"
LIMPIEZA DE ARCHIVOS ESTÁTICOS - eGarage
========================================
Fecha: $(Get-Date)
Modo: $(if ($DryRun) { 'DRY RUN' } else { 'APLICAR CAMBIOS' })

ESTADÍSTICAS:
- Archivos analizados: $($auditData.Count)
- Archivos borrados: $($toDelete.Count)
- Archivos reorganizados: $($toMove.Count)

ARCHIVOS BORRADOS:
"@

foreach ($item in $toDelete) {
  $report += "`n- $($item.OriginalPath) ($($item.Reason))"
}

$report += "`n`nESTRUCTURA FINAL:"
$report += "`n- taller/common/css/ (archivos CSS compartidos)"
$report += "`n- taller/common/js/ (archivos JS compartidos)"
$report += "`n- taller/common/img/ (imágenes compartidas)"
$report += "`n- taller/common/fonts/ (fuentes compartidas)"
$report += "`n- taller/common/media/ (videos/audio compartidos)"
$report += "`n- taller/cl/ (archivos específicos de Chile)"
$report += "`n- taller/us/ (archivos específicos de USA)"
$report += "`n- vendor/ (librerías de terceros)"

if (-not $DryRun) {
  $report += "`n`nBACKUPS CREADOS:"
  $report += "`n- $BackupDir"
  $report += "`n`nCUARENTENA:"
  $report += "`n- $QuarantineDir"
}

Set-Content -Path $reportFile -Value $report -Encoding UTF8

Write-Host "   ✅ Reporte guardado en: $reportFile" -ForegroundColor Green

# PASO 6: Recomendaciones finales
Write-Host "`n🎯 RECOMENDACIONES FINALES:" -ForegroundColor Yellow
Write-Host "   1. Ejecutar: python manage.py collectstatic" -ForegroundColor Gray
Write-Host "   2. Verificar que STATIC_ROOT esté configurado correctamente" -ForegroundColor Gray
Write-Host "   3. Probar la aplicación en modo DEBUG=False" -ForegroundColor Gray
Write-Host "   4. Verificar que WhiteNoise sirva los archivos correctamente" -ForegroundColor Gray

if ($DryRun) {
  Write-Host "`n💡 Para aplicar los cambios, ejecuta:" -ForegroundColor Cyan
  Write-Host "   .\apply_static_cleanup.ps1 -Root `"$Root`"" -ForegroundColor White
} else {
  Write-Host "`n✅ LIMPIEZA COMPLETADA EXITOSAMENTE" -ForegroundColor Green
}

Write-Host "`n===============================================" -ForegroundColor Cyan
