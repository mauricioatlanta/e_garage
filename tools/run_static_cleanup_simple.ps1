# run_static_cleanup_simple.ps1
# Script simplificado para limpieza de archivos estáticos
param(
  [string]$Root = "E:\projecto\e_garage",
  [switch]$DryRun = $false
)

Write-Host "PROCESO COMPLETO DE LIMPIEZA DE ARCHIVOS ESTATICOS" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Directorio base: $Root" -ForegroundColor Gray
Write-Host "Modo: $(if ($DryRun) { 'DRY RUN' } else { 'APLICAR CAMBIOS' })" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Red' })
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path (Join-Path $Root "manage.py"))) {
  Write-Error "No se encontro manage.py en $Root. Verifica la ruta."
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
    throw "Error en auditoria"
  }
  Write-Host "   Auditoria completada" -ForegroundColor Green
} catch {
  Write-Error "Error ejecutando auditoria: $_"
  exit 1
}

# PASO 2: Generar plan de reorganización
Write-Host "`nPASO 2: Generando plan de reorganizacion..." -ForegroundColor Green
try {
  & python tools/clean/suggest_moves.py --base "$Root\static" --manifest "$reportsDir\manifest.json"
  if ($LASTEXITCODE -ne 0) {
    throw "Error generando plan"
  }
  Write-Host "   Plan generado" -ForegroundColor Green
} catch {
  Write-Error "Error generando plan: $_"
  exit 1
}

# PASO 3: Aplicar limpieza
Write-Host "`nPASO 3: Aplicando limpieza..." -ForegroundColor Green
try {
  $cleanupParams = @("-Root", $Root)
  if ($DryRun) { $cleanupParams += "-DryRun" }

  & .\tools\apply_static_cleanup.ps1 @cleanupParams
  if ($LASTEXITCODE -ne 0) {
    throw "Error en limpieza"
  }
  Write-Host "   Limpieza completada" -ForegroundColor Green
} catch {
  Write-Error "Error en limpieza: $_"
  exit 1
}

# PASO 4: Validación
Write-Host "`nPASO 4: Validando resultados..." -ForegroundColor Green
try {
  & .\tools\validate_static_cleanup.ps1 -Root $Root
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "Validacion completada con advertencias"
  } else {
    Write-Host "   Validacion exitosa" -ForegroundColor Green
  }
} catch {
  Write-Warning "Error en validacion: $_"
}

# RESUMEN FINAL
Write-Host "`nPROCESO COMPLETADO" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green

Write-Host "Archivos procesados:" -ForegroundColor Cyan
Write-Host "   - Auditoria: $reportsDir\audit_static.csv" -ForegroundColor Gray
Write-Host "   - Plan: $reportsDir\manifest.json" -ForegroundColor Gray
Write-Host "   - Validacion: $reportsDir\validation_report_*.txt" -ForegroundColor Gray

Write-Host "`nPROXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "   1. Revisar reportes en tools\reports\" -ForegroundColor Gray
Write-Host "   2. Probar la aplicacion en modo DEBUG=False" -ForegroundColor Gray
Write-Host "   3. Verificar que WhiteNoise sirva los archivos correctamente" -ForegroundColor Gray
Write-Host "   4. Hacer commit de los cambios" -ForegroundColor Gray

if ($DryRun) {
  Write-Host "`nPara aplicar los cambios reales, ejecuta:" -ForegroundColor Cyan
  Write-Host "   .\tools\run_static_cleanup_simple.ps1 -Root `"$Root`"" -ForegroundColor White
} else {
  Write-Host "`nLIMPIEZA COMPLETADA EXITOSAMENTE" -ForegroundColor Green
}

Write-Host "`n=====================================================" -ForegroundColor Cyan
