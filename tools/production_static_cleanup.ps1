# production_static_cleanup.ps1
# Limpieza quirúrgica para producción (DEBUG=False + WhiteNoise)
param(
  [string]$Root = "E:\projecto\e_garage",
  [switch]$DryRun = $false
)

Write-Host "LIMPIEZA QUIRURGICA PARA PRODUCCION" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Root: $Root" -ForegroundColor Gray
Write-Host "DryRun: $DryRun" -ForegroundColor Gray

$staticDir = Join-Path $Root "static"
$backupDir = Join-Path $Root "tools\backup\static_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Crear backup
if (-not $DryRun) {
  New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
  Write-Host "Backup creado en: $backupDir" -ForegroundColor Green
}

# 1) BORRAR archivos vacíos y de test/coverage/config
Write-Host "`n1. BORRANDO archivos vacíos y de test/coverage/config..." -ForegroundColor Red

$trash = @(
  "\js\fondo_interactivo.d41d8cd9.js",
  "\js\particles.json",
  "\videos\fondo_futurista.mp4",
  "\js\coverage_html_cb_497bf287.5d92da3d.js",
  "\js\playwright.config.92b72f4a.js",
  "\js\postcss.config.854b3875.js",
  "\js\setupTests.1a77571e.js",
  "\js\reportWebVitals.240e2381.js",
  "\js\test_busqueda_repuestos_frontend.spec.cdadc038.js",
  "\js\test_busqueda_servicios_frontend.spec.ce63f330.js",
  "\js\test_formulario_documento_completo.spec.0d6a0b0e.js"
) | ForEach-Object { Join-Path $staticDir $_ }

foreach ($file in $trash) {
  if (Test-Path $file) {
    if ($DryRun) {
      Write-Host "  [DRY RUN] BORRAR: $file" -ForegroundColor Yellow
    } else {
      Write-Host "  BORRANDO: $file" -ForegroundColor Red
      Remove-Item $file -Force
    }
  }
}

# 2) BORRAR carpeta de fuentes de build
Write-Host "`n2. BORRANDO carpeta de fuentes de build..." -ForegroundColor Red
$src = Join-Path $staticDir "src"
if (Test-Path $src) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] BORRAR CARPETA: $src" -ForegroundColor Yellow
  } else {
    Write-Host "  BORRANDO CARPETA: $src" -ForegroundColor Red
    Remove-Item $src -Force -Recurse
  }
}

# 3) Consolidar vendor
Write-Host "`n3. CONSOLIDANDO vendor..." -ForegroundColor Blue

# 3.1 jQuery UI: dejar solo una (prefiere dist\js)
$jqui_keep = Join-Path $staticDir "vendor\dist\js\jquery-ui.min.4e1155b3.js"
$jqui_alt  = Join-Path $staticDir "vendor\js\js\jquery-ui.min.c6b0df13.js"
if ((Test-Path $jqui_keep) -and (Test-Path $jqui_alt)) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] BORRAR DUPLICADO: $jqui_alt" -ForegroundColor Yellow
  } else {
    Write-Host "  BORRANDO DUPLICADO: $jqui_alt" -ForegroundColor Red
    Remove-Item $jqui_alt -Force
  }
}

# 3.2 Select2: eliminar duplicados CSS "css\css" y "select2_custom" en vendor
$cssCssDir = Join-Path $staticDir "vendor\css\css"
if (Test-Path $cssCssDir) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] BORRAR CARPETA: $cssCssDir" -ForegroundColor Yellow
  } else {
    Write-Host "  BORRANDO CARPETA: $cssCssDir" -ForegroundColor Red
    Remove-Item $cssCssDir -Force -Recurse
  }
}

$sel2dup = Join-Path $staticDir "vendor\select2\dist\select2_custom.e65898ee.css"
if (Test-Path $sel2dup) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] BORRAR DUPLICADO: $sel2dup" -ForegroundColor Yellow
  } else {
    Write-Host "  BORRANDO DUPLICADO: $sel2dup" -ForegroundColor Red
    Remove-Item $sel2dup -Force
  }
}

# 3.3 Ruta vendor/vendor rara
$weird = Join-Path $staticDir "vendor\vendor\js\es.b337e3e6.js"
if (Test-Path $weird) {
  $dest = Join-Path $staticDir "vendor\js\es.b337e3e6.js"
  if ($DryRun) {
    Write-Host "  [DRY RUN] MOVER: $weird -> $dest" -ForegroundColor Yellow
  } else {
    Write-Host "  MOVIENDO: $weird -> $dest" -ForegroundColor Blue
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    Move-Item $weird $dest -Force
    Remove-Item (Join-Path $staticDir "vendor\vendor") -Force -Recurse
  }
}

# 4) Autocomplete Light (deja uno solo)
Write-Host "`n4. UNIFICANDO Autocomplete Light..." -ForegroundColor Blue
$autoA = Join-Path $staticDir "autocomplete_light_custom\autocomplete.init.ce7877f2.js"
$autoB = Join-Path $staticDir "autocomplete_light_custom\init.ce7877f2.js"
if ((Test-Path $autoA) -and (Test-Path $autoB)) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] BORRAR DUPLICADO: $autoB" -ForegroundColor Yellow
    Write-Host "  [DRY RUN] RENOMBRAR: $autoA -> autocomplete.init.js" -ForegroundColor Yellow
  } else {
    Write-Host "  BORRANDO DUPLICADO: $autoB" -ForegroundColor Red
    Remove-Item $autoB -Force
    Write-Host "  RENOMBRANDO: $autoA -> autocomplete.init.js" -ForegroundColor Blue
    Rename-Item $autoA (Join-Path (Split-Path $autoA) "autocomplete.init.js") -Force
  }
}

# 5) CSS: un bundle canónico
Write-Host "`n5. CONSOLIDANDO CSS..." -ForegroundColor Blue
$css_dir = Join-Path $staticDir "taller\common\css"
New-Item -ItemType Directory -Force $css_dir | Out-Null

# Elige uno de los existentes como base
$css_src = Join-Path $staticDir "css\style.c6dfc145.css"
if (Test-Path $css_src) {
  $css_dest = Join-Path $css_dir "app.min.css"
  if ($DryRun) {
    Write-Host "  [DRY RUN] COPIAR: $css_src -> $css_dest" -ForegroundColor Yellow
  } else {
    Write-Host "  COPIANDO: $css_src -> $css_dest" -ForegroundColor Blue
    Copy-Item $css_src $css_dest -Force
  }
}

# 6) JS documentos: dejar 1 canónico (documentos_form.js)
Write-Host "`n6. UNIFICANDO JS del formulario de documentos..." -ForegroundColor Blue
$js_dir = Join-Path $staticDir "taller\common\js"
New-Item -ItemType Directory -Force $js_dir | Out-Null

$js_final = Join-Path $staticDir "taller\common\js\documentos_form_final.9b337ae4.js"
if (Test-Path $js_final) {
  $js_dest = Join-Path $js_dir "documentos_form.js"
  if ($DryRun) {
    Write-Host "  [DRY RUN] COPIAR: $js_final -> $js_dest" -ForegroundColor Yellow
  } else {
    Write-Host "  COPIANDO: $js_final -> $js_dest" -ForegroundColor Blue
    Copy-Item $js_final $js_dest -Force
  }
}

# Borra variantes
$variants = @(
  "documentos_form_enhanced.*.js",
  "documentos_form_new.*.js",
  "documentos_form_numbers.*.js",
  "documentos_form_patch.*.js",
  "documentos_form_v8.*.js",
  "documento_form_advanced.*.js",
  "documento_form_futurista.*.js",
  "formulario_documento.*.js"
)

foreach ($pat in $variants) {
  $files = @()
  $files += Get-ChildItem $js_dir -Filter $pat -ErrorAction SilentlyContinue
  $files += Get-ChildItem (Join-Path $staticDir "taller\common\js") -Filter $pat -ErrorAction SilentlyContinue
  
  foreach ($file in $files) {
    if ($DryRun) {
      Write-Host "  [DRY RUN] BORRAR VARIANTE: $($file.FullName)" -ForegroundColor Yellow
    } else {
      Write-Host "  BORRANDO VARIANTE: $($file.FullName)" -ForegroundColor Red
      Remove-Item $file.FullName -Force
    }
  }
}

# 7) Medios: unificar en /taller/media
Write-Host "`n7. UNIFICANDO medios..." -ForegroundColor Blue
$media_dir = Join-Path $staticDir "taller\media\bg"
New-Item -ItemType Directory -Force $media_dir | Out-Null

$vidA = Join-Path $staticDir "videos\egarage_intro_6s.mp4"
$vidB = Join-Path $staticDir "taller\media\bg\bg_intro_6s.mp4"
if ((Test-Path $vidA) -and !(Test-Path $vidB)) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] MOVER: $vidA -> $vidB" -ForegroundColor Yellow
  } else {
    Write-Host "  MOVIENDO: $vidA -> $vidB" -ForegroundColor Blue
    Move-Item $vidA $vidB -Force
  }
}

$webmA = Join-Path $staticDir "videos\particles_background.webm"
$webmB = Join-Path $staticDir "taller\media\bg\bg_particles.webm"
if ((Test-Path $webmA) -and !(Test-Path $webmB)) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] MOVER: $webmA -> $webmB" -ForegroundColor Yellow
  } else {
    Write-Host "  MOVIENDO: $webmA -> $webmB" -ForegroundColor Blue
    Move-Item $webmA $webmB -Force
  }
}

# Borrar carpeta videos si está vacía
$videosDir = Join-Path $staticDir "videos"
if (Test-Path $videosDir) {
  $remaining = Get-ChildItem $videosDir -ErrorAction SilentlyContinue
  if ($remaining.Count -eq 0) {
    if ($DryRun) {
      Write-Host "  [DRY RUN] BORRAR CARPETA VACIA: $videosDir" -ForegroundColor Yellow
    } else {
      Write-Host "  BORRANDO CARPETA VACIA: $videosDir" -ForegroundColor Red
      Remove-Item $videosDir -Force -Recurse
    }
  }
}

# 8) Logos: si hay duplicados, deja uno solo
Write-Host "`n8. CONSOLIDANDO logos..." -ForegroundColor Blue
$logoA = Join-Path $staticDir "img\egarage_default_logo.eda79c86.png"
$logoB = Join-Path $staticDir "img\TallerPro_logo.eda79c86.png"
if (Test-Path $logoB) {
  if ($DryRun) {
    Write-Host "  [DRY RUN] BORRAR DUPLICADO: $logoB" -ForegroundColor Yellow
  } else {
    Write-Host "  BORRANDO DUPLICADO: $logoB" -ForegroundColor Red
    Remove-Item $logoB -Force
  }
}

# 9) Mover JS runtime a taller/js/
Write-Host "`n9. MOVIENDO JS runtime a taller/js/..." -ForegroundColor Blue
$tallerJsDir = Join-Path $staticDir "taller\js"
New-Item -ItemType Directory -Force $tallerJsDir | Out-Null

$runtime = @(
  "App.729c6e80.js",
  "es.a6403624.js",
  "index.de8d7d2b.js",
  "main.652ca6cb.js",
  "ubicacion.208e793d.js"
)

foreach ($f in $runtime) {
  $srcFile = Join-Path $staticDir "js\$f"
  if (Test-Path $srcFile) {
    $destFile = Join-Path $tallerJsDir $f
    if ($DryRun) {
      Write-Host "  [DRY RUN] MOVER: $srcFile -> $destFile" -ForegroundColor Yellow
    } else {
      Write-Host "  MOVIENDO: $srcFile -> $destFile" -ForegroundColor Blue
      Move-Item $srcFile $destFile -Force
    }
  }
}

Write-Host "`nLIMPIEZA COMPLETADA" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green

if (-not $DryRun) {
  Write-Host "Backup disponible en: $backupDir" -ForegroundColor Gray
  Write-Host "Estructura final en: $staticDir" -ForegroundColor Gray
  Write-Host "`nSiguiente paso: ejecutar 'python manage.py collectstatic'" -ForegroundColor Cyan
} else {
  Write-Host "Para aplicar la limpieza, ejecuta:" -ForegroundColor Cyan
  Write-Host "  .\tools\production_static_cleanup.ps1 -Root `"$Root`"" -ForegroundColor White
}
