# run_complete_static_cleanup.ps1
# Script maestro para ejecutar todo el proceso de limpieza de archivos estáticos
param(
  [string]$Root = "E:\projecto\e_garage",
  [switch]$DryRun = $false,
  [switch]$SkipBackup = $false,
  [switch]$GenerateZip = $false
)

Write-Host "PROCESO COMPLETO DE LIMPIEZA DE ARCHIVOS ESTATICOS" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Directorio base: $Root" -ForegroundColor Gray
Write-Host "Modo: $(if ($DryRun) { 'DRY RUN' } else { 'APLICAR CAMBIOS' })" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Red' })
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path (Join-Path $Root "manage.py"))) {
  Write-Error "No se encontró manage.py en $Root. Verifica la ruta."
  exit 1
}

# Crear directorios necesarios
$reportsDir = Join-Path $Root "tools\reports"
New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null

# PASO 1: Auditoría inicial
Write-Host "PASO 1: Ejecutando auditoria inicial..." -ForegroundColor Green
try {
  & python tools/clean/audit_static.py --base "$Root\static" --out "$reportsDir\audit_static.csv"
  if ($LASTEXITCODE -ne 0) {
    throw "Error en auditoría"
  }
  Write-Host "   ✅ Auditoría completada" -ForegroundColor Green
} catch {
  Write-Error "Error ejecutando auditoría: $_"
  exit 1
}

# PASO 2: Generar plan de reorganización
Write-Host "`n📋 PASO 2: Generando plan de reorganización..." -ForegroundColor Green
try {
  & python tools/clean/suggest_moves.py --base "$Root\static" --manifest "$reportsDir\manifest.json"
  if ($LASTEXITCODE -ne 0) {
    throw "Error generando plan"
  }
  Write-Host "   ✅ Plan generado" -ForegroundColor Green
} catch {
  Write-Error "Error generando plan: $_"
  exit 1
}

# PASO 3: Backup (si no se omite)
if (-not $SkipBackup -and -not $DryRun) {
  Write-Host "`n💾 PASO 3: Creando backup..." -ForegroundColor Green
  $backupDir = Join-Path $Root "tools\backup\static_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

  try {
    Copy-Item "$Root\static\*" $backupDir -Recurse -Force
    Write-Host "   ✅ Backup creado en: $backupDir" -ForegroundColor Green
  } catch {
    Write-Warning "Error creando backup: $_"
  }
}

# PASO 4: Aplicar limpieza
Write-Host "`n🧹 PASO 4: Aplicando limpieza..." -ForegroundColor Green
try {
  $cleanupParams = @("-Root", $Root)
  if ($DryRun) { $cleanupParams += "-DryRun" }

  & .\tools\apply_static_cleanup.ps1 @cleanupParams
  if ($LASTEXITCODE -ne 0) {
    throw "Error en limpieza"
  }
  Write-Host "   ✅ Limpieza completada" -ForegroundColor Green
} catch {
  Write-Error "Error en limpieza: $_"
  exit 1
}

# PASO 5: Actualizar referencias (dry run primero)
Write-Host "`n🔗 PASO 5: Actualizando referencias..." -ForegroundColor Green
try {
  # Dry run primero
  & python tools/clean/update_template_refs.py --templates "$Root\templates" --static "$Root\static" --manifest "$reportsDir\manifest.json" --dry
  if ($LASTEXITCODE -ne 0) {
    throw "Error en dry run de referencias"
  }

  if (-not $DryRun) {
    # Aplicar cambios
    & python tools/clean/update_template_refs.py --templates "$Root\templates" --static "$Root\static" --manifest "$reportsDir\manifest.json"
    if ($LASTEXITCODE -ne 0) {
      throw "Error actualizando referencias"
    }
  }
  Write-Host "   ✅ Referencias actualizadas" -ForegroundColor Green
} catch {
  Write-Warning "Error actualizando referencias: $_"
}

# PASO 6: Validación
Write-Host "`n🔍 PASO 6: Validando resultados..." -ForegroundColor Green
try {
  & .\tools\validate_static_cleanup.ps1 -Root $Root
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Validación completada con advertencias"
  } else {
    Write-Host "   ✅ Validación exitosa" -ForegroundColor Green
  }
} catch {
  Write-Warning "Error en validación: $_"
}

# PASO 7: Generar ZIP (opcional)
if ($GenerateZip) {
  Write-Host "`n📦 PASO 7: Generando ZIP con estructura canónica..." -ForegroundColor Green
  try {
    & .\tools\generate_clean_static_zip.ps1 -Root $Root
    if ($LASTEXITCODE -ne 0) {
      throw "Error generando ZIP"
    }
    Write-Host "   ✅ ZIP generado" -ForegroundColor Green
  } catch {
    Write-Warning "Error generando ZIP: $_"
  }
}

# PASO 8: Collectstatic (si no es dry run)
if (-not $DryRun) {
  Write-Host "`n⚡ PASO 8: Ejecutando collectstatic..." -ForegroundColor Green
  try {
    & python manage.py collectstatic --noinput
    if ($LASTEXITCODE -ne 0) {
      throw "Error en collectstatic"
    }
    Write-Host "   ✅ Collectstatic completado" -ForegroundColor Green
  } catch {
    Write-Warning "Error en collectstatic: $_"
  }
}

# RESUMEN FINAL
Write-Host "`n🎉 PROCESO COMPLETADO" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green

Write-Host "📊 Archivos procesados:" -ForegroundColor Cyan
Write-Host "   - Auditoría: $reportsDir\audit_static.csv" -ForegroundColor Gray
Write-Host "   - Plan: $reportsDir\manifest.json" -ForegroundColor Gray
Write-Host "   - Validación: $reportsDir\validation_report_*.txt" -ForegroundColor Gray

if ($GenerateZip) {
  Write-Host "   - ZIP canónico: $reportsDir\static_clean_canonical.zip" -ForegroundColor Gray
}

Write-Host "`n🎯 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "   1. Revisar reportes en tools\reports\" -ForegroundColor Gray
Write-Host "   2. Probar la aplicación en modo DEBUG=False" -ForegroundColor Gray
Write-Host "   3. Verificar que WhiteNoise sirva los archivos correctamente" -ForegroundColor Gray
Write-Host "   4. Hacer commit de los cambios" -ForegroundColor Gray

if ($DryRun) {
  Write-Host "`nPara aplicar los cambios reales, ejecuta:" -ForegroundColor Cyan
  Write-Host "   .\tools\run_complete_static_cleanup.ps1 -Root `"$Root`"" -ForegroundColor White
} else {
  Write-Host "`nLIMPIEZA COMPLETADA EXITOSAMENTE" -ForegroundColor Green
}

Write-Host "`n=====================================================" -ForegroundColor Cyan
