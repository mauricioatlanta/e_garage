param(
  [string]$OutDir = ".",                       # Carpeta donde dejar el ZIP (por defecto, la actual)
  [string]$NamePrefix = "egarage_release",     # Prefijo del nombre del ZIP
  [string]$SevenZipPath = "C:\Program Files\7-Zip\7z.exe" # Ruta a 7-Zip
)

$ErrorActionPreference = "Stop"

# 1) Verificaciones básicas
$ProjectRoot = (Get-Location).Path
if (!(Test-Path (Join-Path $ProjectRoot "manage.py"))) {
    throw "❌ manage.py no encontrado en $ProjectRoot. Ejecuta el script en la RAÍZ del proyecto."
}

if (!(Test-Path $SevenZipPath)) {
    # Intento alternativo (x86)
    $alt = "C:\Program Files (x86)\7-Zip\7z.exe"
    if (Test-Path $alt) {
        $SevenZipPath = $alt
    } else {
        throw "❌ 7z.exe no encontrado. Revisa la ruta: `$SevenZipPath`"
    }
}

# 2) Salida y nombre final
$OutDir = Resolve-Path $OutDir
if (!(Test-Path $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

$ts = Get-Date -Format "yyyy-MM-dd_HHmmss"
$ZipName = "${NamePrefix}_${ts}.zip"
$ZipPath = Join-Path $OutDir $ZipName

Write-Host "🔧 Creando release desde: $ProjectRoot"
Write-Host "📦 Salida: $ZipPath"
Write-Host "🧰 7-Zip: $SevenZipPath"
Write-Host ""

# 3) Empaquetado con exclusiones
#    -xr! => exclude recursive (directorios / patrones)
#    -x!  => exclude exacto (archivos)
& "$SevenZipPath" a -tzip "$ZipPath" ".\*" `
  -xr!.venv -xr!venv* `
  -xr!__pycache__ -x!*.pyc `
  -xr!.git -xr!.idea -xr!.vscode `
  -xr!node_modules `
  -xr!media `
  -xr!staticfiles -xr!static_root `
  -x!.DS_Store -xr!.pytest_cache -xr!dist -xr!build `
  -x!Thumbs.db -x!desktop.ini `
  -xr!.mypy_cache -xr!.ruff_cache -xr!.coverage -x!.coveragerc `
  -x!*.log -xr!logs `
  -x!*.tmp -xr!tmp -xr!temp

# 4) Resumen
if (Test-Path $ZipPath) {
    $sizeMB = [Math]::Round((Get-Item $ZipPath).Length / 1MB, 2)
    Write-Host "`n✅ Release creado: $ZipPath ($sizeMB MB)"
    Write-Host "   Sube este archivo a: /home/atlantareciclajes/apps/egarage/releases/"
} else {
    throw "❌ No se generó el ZIP. Revisa errores arriba."
}
