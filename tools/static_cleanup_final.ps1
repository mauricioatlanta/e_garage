# static_cleanup_final.ps1
# Script final simplificado para limpieza de archivos estáticos
param(
  [string]$Root = "E:\projecto\e_garage",
  [switch]$DryRun = $false
)

Write-Host "LIMPIEZA DE ARCHIVOS ESTATICOS - eGarage" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Directorio base: $Root" -ForegroundColor Gray
Write-Host "Modo: $(if ($DryRun) { 'DRY RUN' } else { 'APLICAR CAMBIOS' })" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Red' })
Write-Host ""

# Configuración
$StaticDir = Join-Path $Root "static"
$ReportsDir = Join-Path $Root "tools\reports"
$QuarantineDir = Join-Path $Root "tools\quarantine"
$BackupDir = Join-Path $Root "tools\backup\static_cleanup"

# Crear directorios necesarios
New-Item -ItemType Directory -Force -Path $QuarantineDir | Out-Null
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# PASO 1: Cargar datos de auditoría
Write-Host "PASO 1: Cargando datos de auditoria..." -ForegroundColor Green

$auditCsv = Join-Path $ReportsDir "audit_static.csv"
if (-not (Test-Path $auditCsv)) {
  Write-Error "No se encontro audit_static.csv. Ejecuta primero audit_static.py"
  exit 1
}

$auditData = Import-Csv $auditCsv
Write-Host "   Cargados $($auditData.Count) archivos" -ForegroundColor Green

# PASO 2: Identificar archivos para borrar
Write-Host "`nPASO 2: Identificando archivos para borrar..." -ForegroundColor Red

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
    $deleteReason = "Source map (no necesario en produccion)"
  }
  
  # 2. Archivos de diseño (.psd, .ai, .fig)
  elseif ($fileName -match '\.(psd|ai|fig)$') {
    $shouldDelete = $true
    $deleteReason = "Archivo de diseno (no necesario en produccion)"
  }
  
  # 3. Archivos comprimidos (.zip, .rar)
  elseif ($fileName -match '\.(zip|rar|7z)$') {
    $shouldDelete = $true
    $deleteReason = "Archivo comprimido (no necesario en produccion)"
  }
  
  # 4. Archivos no-minificados cuando existe el .min
  elseif ($fileType -in @("CSS", "JS") -and $fileName -notmatch '\.min\.') {
    $minFile = $fileName -replace '\.(css|js)$', '.min.$1'
    $minPath = Join-Path (Split-Path $filePath -Parent) $minFile
    if (Test-Path $minPath) {
      $shouldDelete = $true
      $deleteReason = "Archivo no-minificado (existe version minificada)"
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
  
  # 7. Excluir archivos críticos de DAL
  elseif ($file.path -match 'autocomplete_light_custom.*\.(init|autocomplete\.init)\.') {
    # NO mover estos archivos - son críticos para DAL
    $shouldDelete = $false
  }
  
  # 8. Excluir archivos de video de fondo (ya movidos a ubicación correcta)
  elseif ($fileName -match '(bg_particles\.webm|bg_intro_6s\.mp4)$') {
    # NO mover estos archivos - ya están en ubicación correcta
    $shouldDelete = $false
  }
  
  # 9. Excluir script de inicialización de video de fondo
  elseif ($fileName -match 'eg\.bg\.init\.min\.js$') {
    # NO mover este archivo - ya está en ubicación correcta
    $shouldDelete = $false
  }
  
  if ($shouldDelete) {
    $toDelete += @{
      Path = $filePath
      Reason = $deleteReason
      OriginalPath = $file.path
    }
  } else {
    # Excluir archivos críticos del proceso de reorganización
    if ($file.path -match 'autocomplete_light_custom.*\.(init|autocomplete\.init)\.') {
      # NO mover estos archivos - mantener en ubicación actual
      Write-Host "   MANTENER: $($file.path) (archivo crítico de DAL)" -ForegroundColor Cyan
    } elseif ($fileName -match '(bg_particles\.webm|bg_intro_6s\.mp4|eg\.bg\.init\.min\.js)$') {
      # NO mover archivos de video de fondo y script - ya están en ubicación correcta
      Write-Host "   MANTENER: $($file.path) (archivo de video de fondo/script)" -ForegroundColor Cyan
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
}

Write-Host "   Archivos para borrar: $($toDelete.Count)" -ForegroundColor Red
Write-Host "   Archivos para mover: $($toMove.Count)" -ForegroundColor Blue

# Mostrar resumen de borrados
if ($toDelete.Count -gt 0) {
  Write-Host "`n   ARCHIVOS PARA BORRAR:" -ForegroundColor Red
  foreach ($item in $toDelete | Select-Object -First 10) {
    Write-Host "      - $($item.OriginalPath) ($($item.Reason))" -ForegroundColor Gray
  }
  if ($toDelete.Count -gt 10) {
    Write-Host "      ... y $($toDelete.Count - 10) mas" -ForegroundColor Gray
  }
}

# PASO 3: Aplicar borrados
if ($toDelete.Count -gt 0) {
  Write-Host "`nPASO 3: Aplicando borrados..." -ForegroundColor Red
  
  if ($DryRun) {
    Write-Host "   [DRY RUN] Se borrarian $($toDelete.Count) archivos" -ForegroundColor Yellow
  } else {
    $deleted = 0
    foreach ($item in $toDelete) {
      if (Test-Path $item.Path) {
        # Crear cuarentena
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $quarantineSubDir = Join-Path $QuarantineDir "deleted_$timestamp"
        $relativePath = $item.Path.Replace("$StaticDir\", "")
        $quarantinePath = Join-Path $quarantineSubDir $relativePath
        $quarantineParent = Split-Path $quarantinePath -Parent
        
        New-Item -ItemType Directory -Force -Path $quarantineParent | Out-Null
        Move-Item $item.Path $quarantinePath -Force
        
        # Log del motivo
        $logFile = Join-Path $quarantineSubDir "deletion_log.txt"
        Add-Content -Path $logFile -Value "$(Get-Date): $relativePath - $($item.Reason)"
        
        $deleted++
        Write-Host "   Borrado: $($item.OriginalPath)" -ForegroundColor Green
      }
    }
    Write-Host "   Total borrados: $deleted" -ForegroundColor Green
  }
}

# PASO 4: Reorganizar archivos restantes
if ($toMove.Count -gt 0) {
  Write-Host "`nPASO 4: Reorganizando archivos..." -ForegroundColor Blue
  
  $moved = 0
  $errors = 0
  
  foreach ($item in $toMove) {
    $originalPath = $item.Path
    $fileName = Split-Path $originalPath -Leaf
    
    # Normalizar nombre de archivo
    $normalizedName = $fileName.ToLower()
    $normalizedName = $normalizedName -replace '[^\w\-\.]', '-'
    $normalizedName = $normalizedName -replace '-+', '-'
    $normalizedName = $normalizedName.Trim('-')
    
    # Determinar directorio objetivo
    $pathLower = $item.OriginalPath.ToLower()
    $country = "common"
    if ($pathLower -match '\bcl\b|chile') { $country = "cl" }
    elseif ($pathLower -match '\bus\b|usa|united') { $country = "us" }
    
    $targetDir = switch ($item.Type) {
      "CSS" { "taller\$country\css" }
      "JS" { "taller\$country\js" }
      "IMG" { "taller\$country\img" }
      "FONT" { "taller\$country\fonts" }
      "VIDEO" { "taller\$country\media" }
      "AUDIO" { "taller\$country\media" }
      default { "taller\$country\media" }
    }
    
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
      $relativeTarget = $targetPath.Replace("$StaticDir\", "")
      Write-Host "   [DRY RUN] $($item.OriginalPath) -> $relativeTarget" -ForegroundColor Yellow
    } else {
      try {
        # Crear backup
        $relativePath = $originalPath.Replace("$StaticDir\", "")
        $backupPath = Join-Path $BackupDir $relativePath
        $backupParent = Split-Path $backupPath -Parent
        New-Item -ItemType Directory -Force -Path $backupParent | Out-Null
        Copy-Item $originalPath $backupPath -Force
        
        # Crear directorio objetivo
        $targetParent = Split-Path $targetPath -Parent
        New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
        
        # Mover archivo
        Move-Item $originalPath $targetPath -Force
        $moved++
        
        $status = if ($item.HasIssues) { "WARNING" } else { "OK" }
        $relativeTarget = $targetPath.Replace("$StaticDir\", "")
        Write-Host "   $status $($item.OriginalPath) -> $relativeTarget" -ForegroundColor Green
        
      } catch {
        $errors++
        Write-Host "   ERROR moviendo $($item.OriginalPath): $($_.Exception.Message)" -ForegroundColor Red
      }
    }
  }
  
  if (-not $DryRun) {
    Write-Host "   Total movidos: $moved" -ForegroundColor Green
    Write-Host "   Errores: $errors" -ForegroundColor $(if ($errors -gt 0) { 'Red' } else { 'Green' })
  }
}

# PASO 5: Generar reporte final
Write-Host "`nPASO 5: Generando reporte final..." -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportFile = Join-Path $ReportsDir "cleanup_report_$timestamp.txt"

$report = @"
LIMPIEZA DE ARCHIVOS ESTATICOS - eGarage
========================================
Fecha: $(Get-Date)
Modo: $(if ($DryRun) { 'DRY RUN' } else { 'APLICAR CAMBIOS' })

ESTADISTICAS:
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
$report += "`n- taller/common/img/ (imagenes compartidas)"
$report += "`n- taller/common/fonts/ (fuentes compartidas)"
$report += "`n- taller/common/media/ (videos/audio compartidos)"
$report += "`n- taller/cl/ (archivos especificos de Chile)"
$report += "`n- taller/us/ (archivos especificos de USA)"
$report += "`n- vendor/ (librerias de terceros)"

if (-not $DryRun) {
  $report += "`n`nBACKUPS CREADOS:"
  $report += "`n- $BackupDir"
  $report += "`n`nCUARENTENA:"
  $report += "`n- $QuarantineDir"
}

Set-Content -Path $reportFile -Value $report -Encoding UTF8

Write-Host "   Reporte guardado en: $reportFile" -ForegroundColor Green

# PASO 6: Recomendaciones finales
Write-Host "`nRECOMENDACIONES FINALES:" -ForegroundColor Yellow
Write-Host "   1. Ejecutar: python manage.py collectstatic" -ForegroundColor Gray
Write-Host "   2. Verificar que STATIC_ROOT este configurado correctamente" -ForegroundColor Gray
Write-Host "   3. Probar la aplicacion en modo DEBUG=False" -ForegroundColor Gray
Write-Host "   4. Verificar que WhiteNoise sirva los archivos correctamente" -ForegroundColor Gray

if ($DryRun) {
  Write-Host "`nPara aplicar los cambios, ejecuta:" -ForegroundColor Cyan
  Write-Host "   .\tools\static_cleanup_final.ps1 -Root `"$Root`"" -ForegroundColor White
} else {
  Write-Host "`nLIMPIEZA COMPLETADA EXITOSAMENTE" -ForegroundColor Green
}

Write-Host "`n===============================================" -ForegroundColor Cyan
