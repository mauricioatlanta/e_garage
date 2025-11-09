# generate_clean_static_zip.ps1
# Genera un ZIP con la estructura canónica de archivos estáticos
param(
  [string]$Root = "E:\projecto\e_garage",
  [string]$StaticDir = "E:\projecto\e_garage\static",
  [string]$OutputZip = "E:\projecto\e_garage\tools\reports\static_clean_canonical.zip"
)

Write-Host "📦 GENERANDO ZIP CON ESTRUCTURA CANÓNICA" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Crear directorio temporal
$tempDir = Join-Path $env:TEMP "egarage_static_clean_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

try {
  # Estructura canónica
  $canonicalStructure = @{
    "taller/common/css" = @()
    "taller/common/js" = @()
    "taller/common/img" = @()
    "taller/common/fonts" = @()
    "taller/common/media" = @()
    "taller/cl/css" = @()
    "taller/cl/js" = @()
    "taller/cl/img" = @()
    "taller/us/css" = @()
    "taller/us/js" = @()
    "taller/us/img" = @()
    "vendor/jquery" = @()
    "vendor/select2" = @()
    "vendor/autocomplete_light" = @()
  }

  # Cargar datos de auditoría
  $auditCsv = Join-Path $Root "tools\reports\audit_static.csv"
  if (-not (Test-Path $auditCsv)) {
    Write-Error "No se encontró audit_static.csv"
    exit 1
  }

  $auditData = Import-Csv $auditCsv
  Write-Host "📊 Procesando $($auditData.Count) archivos..." -ForegroundColor Green

  # Función para normalizar nombre
  function Normalize-Filename {
    param([string]$Filename)
    $normalized = $Filename.ToLower()
    $normalized = $normalized -replace '[^\w\-\.]', '-'
    $normalized = $normalized -replace '-+', '-'
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

    # Archivos de terceros
    if ($pathLower -match 'jquery') { return "vendor/jquery" }
    elseif ($pathLower -match 'select2') { return "vendor/select2" }
    elseif ($pathLower -match 'autocomplete') { return "vendor/autocomplete_light" }

    # Mapeo de tipos
    switch ($FileType) {
      "CSS" { return "taller/$country/css" }
      "JS" { return "taller/$country/js" }
      "IMG" { return "taller/$country/img" }
      "FONT" { return "taller/$country/fonts" }
      "VIDEO" { return "taller/$country/media" }
      "AUDIO" { return "taller/$country/media" }
      default { return "taller/$country/media" }
    }
  }

  # Procesar archivos
  $processed = 0
  $skipped = 0

  foreach ($file in $auditData) {
    $originalPath = Join-Path $StaticDir $file.path
    $fileName = $file.name
    $fileType = $file.type
    $isDuplicate = $file.is_duplicate -eq "True"

    # Saltar archivos que se borrarían en producción
    $shouldSkip = $false
    if ($fileName -match '\.(map|psd|ai|fig|zip|rar|7z)$') { $shouldSkip = $true }
    elseif ($fileType -in @("CSS", "JS") -and $fileName -notmatch '\.min\.') {
      $minFile = $fileName -replace '\.(css|js)$', '.min.$1'
      $minPath = Join-Path (Split-Path $originalPath -Parent) $minFile
      if (Test-Path $minPath) { $shouldSkip = $true }
    }
    elseif ($fileName -match '(experimental|temp|tmp|test|debug|old|backup|copy|v\d+)$') { $shouldSkip = $true }
    elseif ($isDuplicate) {
      # Mantener solo el primero de cada grupo de duplicados
      $hash = $file.sha1
      $firstOccurrence = $auditData | Where-Object { $_.sha1 -eq $hash } | Select-Object -First 1
      if ($file.path -ne $firstOccurrence.path) { $shouldSkip = $true }
    }

    if ($shouldSkip) {
      $skipped++
      continue
    }

    if (Test-Path $originalPath) {
      # Determinar directorio objetivo
      $targetDir = Get-TargetDirectory -FilePath $file.path -FileType $fileType
      $normalizedName = Normalize-Filename -Filename $fileName
      $targetPath = Join-Path $tempDir $targetDir $normalizedName

      # Crear directorio objetivo
      $targetParent = Split-Path $targetPath -Parent
      New-Item -ItemType Directory -Force -Path $targetParent | Out-Null

      # Copiar archivo
      Copy-Item $originalPath $targetPath -Force
      $processed++

      # Agregar a estructura
      if ($canonicalStructure.ContainsKey($targetDir)) {
        $canonicalStructure[$targetDir] += $normalizedName
      }
    }
  }

  Write-Host "✅ Procesados: $processed archivos" -ForegroundColor Green
  Write-Host "⏭️ Omitidos: $skipped archivos" -ForegroundColor Yellow

  # Crear archivo de estructura
  $structureFile = Join-Path $tempDir "ESTRUCTURA_CANONICA.txt"
  $structure = @"
ESTRUCTURA CANÓNICA DE ARCHIVOS ESTÁTICOS - eGarage
==================================================
Generado: $(Get-Date)

ESTRUCTURA DE DIRECTORIOS:
"@

  foreach ($dir in $canonicalStructure.Keys | Sort-Object) {
    $files = $canonicalStructure[$dir]
    if ($files.Count -gt 0) {
      $structure += "`n`n📁 $dir/ ($($files.Count) archivos)"
      foreach ($file in $files | Sort-Object) {
        $structure += "`n   - $file"
      }
    }
  }

  $structure += @"

CONVENCIONES APLICADAS:
- Nombres en kebab-case (minúsculas, guiones)
- Sin espacios, mayúsculas o acentos
- Organización por tipo: css/, js/, img/, fonts/, media/
- Separación por país: common/, cl/, us/
- Librerías de terceros en vendor/
- Eliminación de duplicados
- Eliminación de archivos no necesarios en producción

ARCHIVOS ELIMINADOS:
- Source maps (*.map)
- Archivos de diseño (*.psd, *.ai, *.fig)
- Archivos comprimidos (*.zip, *.rar, *.7z)
- Versiones no-minificadas cuando existe .min
- Archivos experimentales/temporales
- Duplicados por hash

TOTAL ARCHIVOS: $processed
"@

  Set-Content -Path $structureFile -Value $structure -Encoding UTF8

  # Crear ZIP
  Write-Host "📦 Creando ZIP..." -ForegroundColor Blue
  if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }
  Compress-Archive -Path "$tempDir\*" -DestinationPath $OutputZip -Force

  Write-Host "✅ ZIP creado exitosamente: $OutputZip" -ForegroundColor Green

  # Mostrar resumen
  Write-Host "`n📊 RESUMEN:" -ForegroundColor Cyan
  Write-Host "   Archivos incluidos: $processed" -ForegroundColor Green
  Write-Host "   Archivos omitidos: $skipped" -ForegroundColor Yellow
  Write-Host "   Tamaño del ZIP: $([math]::Round((Get-Item $OutputZip).Length / 1MB, 2)) MB" -ForegroundColor Blue

  Write-Host "`n🎯 PRÓXIMOS PASOS:" -ForegroundColor Yellow
  Write-Host "   1. Extraer el ZIP en tu directorio static/" -ForegroundColor Gray
  Write-Host "   2. Ejecutar: python manage.py collectstatic" -ForegroundColor Gray
  Write-Host "   3. Verificar funcionamiento en DEBUG=False" -ForegroundColor Gray

} finally {
  # Limpiar directorio temporal
  if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
  }
}

Write-Host "`n=========================================" -ForegroundColor Cyan
