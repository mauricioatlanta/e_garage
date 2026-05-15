
# backup_and_move_static.ps1
param(
  [string]$Root      = "E:\projecto\e_garage",
  [string]$Static    = "E:\projecto\e_garage\static",
  [string]$ReportCsv = "E:\projecto\e_garage\tools\reports\static_audit.csv",
  [string]$ReportJson= "E:\projecto\e_garage\tools\reports\static_audit.json"
)

# Ensure report dir
$reportDir = Split-Path $ReportCsv -Parent
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }

# Load plan (prefer JSON; fallback to CSV)
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

# Filter move items
$toMove = @()
foreach ($row in $planItems) {
  if ($row.suggested_action -eq "move") {
    $toMove += $row
  }
}

if ($toMove.Count -eq 0) {
  Write-Host "No hay archivos con acción 'move'." -ForegroundColor Yellow
  exit 0
}

# Prepare backup
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $Root "tools\backups\static_moves_$ts"
$zipPath   = Join-Path $Root "tools\backups\static_moves_$ts.zip"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

# Copy files to backup
foreach ($row in $toMove) {
  $src = $row.src
  if (-not $src) { $src = $row."src" } # csv compatibility
  if (Test-Path $src) {
    $rel = $src.Replace("$Root\", "")
    $dest = Join-Path $backupDir $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
    Copy-Item $src $dest -Force
  }
}

# Zip backup
if (-not (Test-Path (Split-Path $zipPath -Parent))) {
  New-Item -ItemType Directory -Force -Path (Split-Path $zipPath -Parent) | Out-Null
}
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $backupDir\* -DestinationPath $zipPath
Write-Host "Backup ZIP creado: $zipPath" -ForegroundColor Green

# Execute move
$scriptPath = Join-Path $Root "tools\eg_static_audit.py"
py $scriptPath --root $Root --static-root $Static --report (Join-Path $Root "tools\reports\static_audit") --move
