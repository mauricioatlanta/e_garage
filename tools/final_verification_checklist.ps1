# final_verification_checklist.ps1
# Checklist de verificación final para la limpieza de static files

param(
  [string]$Root = "E:\projecto\e_garage"
)

Write-Host "CHECKLIST DE VERIFICACION FINAL" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host "Root: $Root" -ForegroundColor Gray
Write-Host ""

$staticDir = Join-Path $Root "static"
$templatesDir = Join-Path $Root "templates"
$allGood = $true

# 1. Verificar que el JS canónico existe
Write-Host "1. Verificando JS canónico..." -ForegroundColor Blue
$canonicalJs = Join-Path $staticDir "taller\common\js\documentos_form.js"
if (Test-Path $canonicalJs) {
  Write-Host "   ✅ documentos_form.js existe" -ForegroundColor Green
} else {
  Write-Host "   ❌ documentos_form.js NO existe" -ForegroundColor Red
  $allGood = $false
}

# 2. Verificar que no hay variantes antiguas
Write-Host "`n2. Verificando ausencia de variantes antiguas..." -ForegroundColor Blue
$oldVariants = @(
  "documentos_form_final*.js",
  "documentos_form_numbers*.js",
  "documentos_form_patch*.js",
  "documentos_form_v*.js",
  "documento_form_futurista*.js",
  "documento_form_advanced*.js",
  "formulario_documento*.js"
)

$foundOld = $false
foreach ($pattern in $oldVariants) {
  $files = Get-ChildItem -Recurse -Path $staticDir -Filter $pattern -ErrorAction SilentlyContinue
  if ($files) {
    Write-Host "   ❌ Encontrado: $($files[0].Name)" -ForegroundColor Red
    $foundOld = $true
    $allGood = $false
  }
}

if (-not $foundOld) {
  Write-Host "   ✅ No hay variantes antiguas" -ForegroundColor Green
}

# 3. Verificar que no hay archivos de test/coverage
Write-Host "`n3. Verificando ausencia de archivos de test/coverage..." -ForegroundColor Blue
$testPatterns = @(
  "*test*.js",
  "*coverage*.js",
  "*playwright*.js",
  "*postcss*.js",
  "*setupTests*.js",
  "*reportWebVitals*.js"
)

$foundTest = $false
foreach ($pattern in $testPatterns) {
  $files = Get-ChildItem -Recurse -Path $staticDir -Filter $pattern -ErrorAction SilentlyContinue
  if ($files) {
    Write-Host "   ❌ Encontrado: $($files[0].Name)" -ForegroundColor Red
    $foundTest = $true
    $allGood = $false
  }
}

if (-not $foundTest) {
  Write-Host "   ✅ No hay archivos de test/coverage" -ForegroundColor Green
}

# 4. Verificar que no hay archivos de configuración de build
Write-Host "`n4. Verificando ausencia de archivos de configuración..." -ForegroundColor Blue
$configPatterns = @(
  "*config*.js",
  "*config*.css"
)

$foundConfig = $false
foreach ($pattern in $configPatterns) {
  $files = Get-ChildItem -Recurse -Path $staticDir -Filter $pattern -ErrorAction SilentlyContinue
  if ($files) {
    Write-Host "   ❌ Encontrado: $($files[0].Name)" -ForegroundColor Red
    $foundConfig = $true
    $allGood = $false
  }
}

if (-not $foundConfig) {
  Write-Host "   ✅ No hay archivos de configuración" -ForegroundColor Green
}

# 5. Verificar estructura de directorios
Write-Host "`n5. Verificando estructura de directorios..." -ForegroundColor Blue
$requiredDirs = @(
  "vendor\jquery",
  "vendor\dist\js",
  "vendor\dist\css",
  "taller\common\css",
  "taller\common\js",
  "taller\js",
  "taller\media\bg",
  "autocomplete_light_custom"
)

foreach ($dir in $requiredDirs) {
  $dirPath = Join-Path $staticDir $dir
  if (Test-Path $dirPath) {
    Write-Host "   ✅ $dir" -ForegroundColor Green
  } else {
    Write-Host "   ❌ $dir NO existe" -ForegroundColor Red
    $allGood = $false
  }
}

# 6. Verificar archivos clave
Write-Host "`n6. Verificando archivos clave..." -ForegroundColor Blue
$keyFiles = @(
  "vendor\jquery\jquery-3.6.0.min.js",
  "vendor\dist\js\jquery-ui.min.js",
  "vendor\dist\js\select2.min.js",
  "vendor\dist\css\select2.min.css",
  "autocomplete_light_custom\autocomplete.init.js",
  "taller\common\css\app.min.css",
  "taller\common\js\documentos_form.js"
)

foreach ($file in $keyFiles) {
  $filePath = Join-Path $staticDir $file
  if (Test-Path $filePath) {
    Write-Host "   ✅ $file" -ForegroundColor Green
  } else {
    Write-Host "   ❌ $file NO existe" -ForegroundColor Red
    $allGood = $false
  }
}

# 7. Verificar referencias en templates
Write-Host "`n7. Verificando referencias en templates..." -ForegroundColor Blue
$templateRefs = Get-ChildItem -Recurse -Include *.html -Path $templatesDir | Select-String -Pattern "taller/common/js/documentos_form.js"
if ($templateRefs) {
  Write-Host "   ✅ Referencias al JS canónico encontradas" -ForegroundColor Green
} else {
  Write-Host "   ⚠️  No se encontraron referencias al JS canónico" -ForegroundColor Yellow
}

# 8. Verificar que no hay referencias a archivos antiguos
Write-Host "`n8. Verificando ausencia de referencias antiguas..." -ForegroundColor Blue
$oldRefs = Get-ChildItem -Recurse -Include *.html -Path $templatesDir | Select-String -Pattern "documento_form_futurista|documentos_form_final|documentos_form_patch|documentos_form_numbers|formulario_documento|documentos_form_v"
if ($oldRefs) {
  Write-Host "   ❌ Referencias a archivos antiguos encontradas:" -ForegroundColor Red
  $oldRefs | ForEach-Object {
    # Verificar que el archivo realmente existe y tiene contenido
    $filePath = Join-Path $templatesDir $_.Filename
    if (Test-Path $filePath) {
      $lineCount = (Get-Content $filePath).Count
      if ($_.LineNumber -le $lineCount) {
        Write-Host "     $($_.Filename):$($_.LineNumber) - $($_.Line.Trim())" -ForegroundColor Red
        $allGood = $false
      }
    }
  }
} else {
  Write-Host "   ✅ No hay referencias a archivos antiguos" -ForegroundColor Green
}

# Resumen final
Write-Host "`nRESUMEN FINAL" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan

if ($allGood) {
  Write-Host "🎉 ¡VERIFICACION EXITOSA!" -ForegroundColor Green
  Write-Host "La limpieza de static files está completa y correcta." -ForegroundColor Green
  Write-Host "`nPróximos pasos:" -ForegroundColor Cyan
  Write-Host "1. Actualizar templates para usar {% include 'taller/common/document_form_scripts.html' %}" -ForegroundColor White
  Write-Host "2. Configurar WhiteNoise con CompressedManifestStaticFilesStorage" -ForegroundColor White
  Write-Host "3. Probar funcionalidad en el navegador" -ForegroundColor White
} else {
  Write-Host "❌ VERIFICACION FALLIDA" -ForegroundColor Red
  Write-Host "Hay problemas que deben ser corregidos antes de continuar." -ForegroundColor Red
}

Write-Host "`nArchivos estáticos listos para producción: $($allGood)" -ForegroundColor $(if ($allGood) { "Green" } else { "Red" })
