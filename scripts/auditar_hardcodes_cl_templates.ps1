# Auditoria C: hardcodes /cl/... login y signup en templates
# Uso: .\scripts\auditar_hardcodes_cl_templates.ps1
# Regla: Si el archivo es CL (cl/es, landing_chile, etc.) -> OK.
#        Si es de otro pais (uy, ec, mx, us, etc.) -> BUG, corregir.

$ErrorActionPreference = "SilentlyContinue"
$patterns = @(
    "/cl/es/accounts/login/",
    "/cl/es/accounts/signup/",
    "/cl/accounts/login/",
    "/cl/accounts/signup/"
)

$dirs = @(
    ".\templates",
    ".\deploy_atlantareciclajes\templates"
)

$regex = ($patterns | ForEach-Object { [regex]::Escape($_) }) -join "|"
$results = @()

$base = (Get-Location).Path.TrimEnd('\') + "\"
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) { continue }
    Get-ChildItem -Path $dir -Filter "*.html" -Recurse | ForEach-Object {
        $fi = $_
        $content = Get-Content $fi.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $content) { return }
        $rel = $fi.FullName.Replace($base, "")
        $lineNum = 0
        $content -split "`n" | ForEach-Object {
            $lineNum++
            if ($_ -match $regex) {
                $results += [PSCustomObject]@{ Path = $rel; LineNum = $lineNum; Line = $_.Trim() }
            }
        }
    }
}

$results | Sort-Object Path, LineNum | ForEach-Object {
    "$($_.Path):$($_.LineNum): $($_.Line)"
}

# Resumen por archivo (para regla CL vs otro pais)
Write-Host ""
Write-Host "--- Archivos unicos ---"
$results | Select-Object -ExpandProperty Path -Unique | ForEach-Object {
    $f = $_
    if ($f -like "*\cl\es\*" -or $f -like "*landing_chile*") { $cl = "CL (OK)" }
    else { $cl = "revisar" }
    Write-Host "  $f  -> $cl"
}
