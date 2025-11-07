# quarantine_delete_static.ps1
param(
  [string]$Root      = "E:\projecto\e_garage",
  [string]$ReportCsv = "E:\projecto\e_garage\tools\reports\static_audit.csv",
  [string]$ReportJson= "E:\projecto\e_garage\tools\reports\static_audit.json"
)

# Cargar plan
$planItems = @()
if (Test-Path $ReportJson) {
  $plan = Get-Content $ReportJson | ConvertFrom-Json
  $planItems = $plan.plan
} elseif (Test-Path $ReportCsv) {
  $planItems = Import-Csv $ReportCsv
} else {
  Write-Error "No existe plan (JSON ni CSV)."
  exit 1
}

# Filtrar elementos con acción delete
$toDelete = @()
foreach ($row in $planItems) {
  if ($row.suggested_action -eq "delete") {
    $toDelete += $row
  }
}

if ($toDelete.Count -eq 0) {
  Write-Host "No hay archivos con acción 'delete'." -ForegroundColor Yellow
  exit 0
}

# Carpeta de cuarentena
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$quarantineDir = Join-Path $Root "tools\quarantine\static_deletes_$ts"
$zipPath = Join-Path $Root "tools\quarantine\static_deletes_$ts.zip"
New-Item -ItemType Directory -Force -Path $quarantineDir | Out-Null

# Mover archivos a cuarentena (sin borrarlos)
foreach ($row in $toDelete) {
  $src = $row.src
  if (-not $src) { $src = $row."src" } # compatibilidad CSV
  if (Test-Path $src) {
    $rel = $src.Replace("$Root\", "")
    $dest = Join-Path $quarantineDir $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
    Move-Item $src $dest -Force
  }
}

# Comprimir cuarentena
if (-not (Test-Path (Split-Path $zipPath -Parent))) {
  New-Item -ItemType Directory -Force -Path (Split-Path $zipPath -Parent) | Out-Null
}
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $quarantineDir\* -DestinationPath $zipPath
Write-Host "Archivos enviados a cuarentena: $zipPath" -ForegroundColor Green
