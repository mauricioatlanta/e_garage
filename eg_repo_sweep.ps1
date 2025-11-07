Param(
  [string]$Root = ".",
  [string]$OutCsv = ".\egarge_loose_files_audit.csv",
  [switch]$AggressiveDelete # borra más generado (coverage, caches, etc.)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Rel {
  param([string]$Path)
  $full = [System.IO.Path]::GetFullPath($Path)
  $root = [System.IO.Path]::GetFullPath($Root)
  if ($full.ToLower().StartsWith($root.ToLower())) { return $full.Substring($root.Length).TrimStart('\','/') }
  return $Path
}

# directorios a ignorar (no barrer)
$IgnoreDirs = @(
  '\.git\','\backups\','\venv\','\env\','\node_modules\','\__pycache__\',
  '\.pytest_cache\','\.mypy_cache\','\.idea\','\.vscode\','\media\'
)

$files = Get-ChildItem -Path $Root -File -Recurse -Force | Where-Object {
  $p = $_.FullName
  -not ($IgnoreDirs | ForEach-Object { $p -match [regex]::Escape($_) } | Where-Object { $_ }) 
}

# mapa hash → lista de archivos (para duplicados exactos)
$hashGroups = @{}
foreach ($f in $files) {
  try {
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName).Hash
    if (-not $hashGroups.ContainsKey($h)) { $hashGroups[$h] = @() }
    $hashGroups[$h] += $f
  } catch { }
}

# elegir canónico: preferir rutas dentro de carpetas canónicas
function IsPreferredPath($path) {
  $p = $path.ToLower()
  return ($p -like "*\templates\*" -or $p -like "*\static\*" -or $p -like "*\docs\*" -or $p -like "*\data\*")
}

$canonical = @{} # fullpath -> $true
foreach ($kv in $hashGroups.GetEnumerator()) {
  $group = $kv.Value
  if ($group.Count -le 1) { continue }
  $best = $group | Sort-Object @{Expression={- (IsPreferredPath $_.FullName)}}, @{Expression={$_.FullName.Length}}, LastWriteTime | Select-Object -First 1
  $canonical[$best.FullName] = $true
}

function Guess-TargetFolder {
  param([string]$RelPath)
  $ext = [System.IO.Path]::GetExtension($RelPath).ToLowerInvariant()
  switch ($ext) {
    ".html" { return "templates\_loose_import" }
    ".htm"  { return "templates\_loose_import" }
    ".css"  { return "static\_loose_import" }
    ".js"   { return "static\_loose_import" }
    ".png"  { return "static\_loose_import\img" }
    ".jpg"  { return "static\_loose_import\img" }
    ".jpeg" { return "static\_loose_import\img" }
    ".gif"  { return "static\_loose_import\img" }
    ".webp" { return "static\_loose_import\img" }
    ".svg"  { return "static\_loose_import\img" }
    ".pdf"  { return "docs\_loose_import" }
    ".md"   { return "docs\_loose_import" }
    ".txt"  { return "docs\_loose_import" }
    ".sql"  { return "data\_loose_import" }
    ".csv"  { return "data\_loose_import" }
    ".xlsx" { return "data\_loose_import" }
    ".json" { return "data\_loose_import" }
    ".py"   { return "taller\_loose_import\py" }
    default { return "_loose_import\misc" }
  }
}

function IsGeneratedJunk($name) {
  $n = $name.ToLower()
  if ($n -eq "db.sqlite3") { return $true }
  if ($n -eq "coverage.xml") { return $true }
  if ($n -like "*.pyc" -or $n -eq ".ds_store") { return $true }
  return $false
}

function IsRootConfigKeep($rel) {
  $r = $rel.ToLower()
  return @(
    ".gitignore",".gitattributes",".pre-commit-config.yaml",".env.example",
    "pyproject.toml","pytest.ini"
  ) -contains $r
}

$rows = New-Object System.Collections.Generic.List[object]

foreach ($f in $files) {
  $rel = Resolve-Rel $f.FullName
  $rel = $rel -replace '/', '\'

  # Duplicados exactos
  $isDuplicate = $false
  $isCanonical = $false
  $h = $null
  try { $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName).Hash } catch {}
  if ($h -and $hashGroups[$h].Count -gt 1) {
    $isDuplicate = $true
    if ($canonical.ContainsKey($f.FullName)) { $isCanonical = $true }
  }

  $suggested = "keep"
  $reason    = "ok"

  if ($isDuplicate -and -not $isCanonical) {
    $suggested = "delete"
    $reason    = "duplicate (same hash)"
  } elseif (IsGeneratedJunk $f.Name) {
    $suggested = "delete"
    $reason    = "generated/junk"
  } elseif ($rel -match "^(templates|static|docs|data|taller)\\") {
    # ya está en lugar razonable
    $suggested = "keep"
    $reason    = "canonical location"
  } elseif (IsRootConfigKeep $rel) {
    $suggested = "keep"
    $reason    = "root config"
  } else {
    # Sugerir mover por extensión
    $target = Guess-TargetFolder $rel
    if ($target) {
      $suggested = "move"
      $reason    = "misplaced -> $target"
    } else {
      $suggested = "review"
      $reason    = "needs manual review"
    }
  }

  # Más agresivo si se pide
  if ($AggressiveDelete) {
    $low = $rel.ToLower()
    if ($low -like "*\__pycache__\*" -or $low -like "*\.pytest_cache\*" -or $low -like "*\.mypy_cache\*") {
      $suggested = "delete"; $reason = "cache dir file"
    }
  }

  $rows.Add([pscustomobject]@{
    filename         = $rel
    suggested_action = $suggested
    reason           = $reason
  })
}

# Priorizar: delete > move > review > keep
$ordered = $rows | Sort-Object @{
  Expression = {
    switch ($_.suggested_action) {
      "delete" {0}; "move" {1}; "review" {2}; default {3}
    }
  }
}, filename

$ordered | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "Audit listo → $OutCsv"
Write-Host "Consejo: ejecútalo con tu tidy script:"
Write-Host ".\eg_loose_files_tidy_clean.ps1 -CsvPath $OutCsv -Root $Root  # dry-run"
