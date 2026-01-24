# Script de Deploy PowerShell - Registro Simplificado
# Uso: .\scripts\deploy_signup_simplificado.ps1 -Server "usuario@servidor.com" -ServerPath "/ruta/a/egarage"

param(
    [string]$Server = "usuario@servidor.com",
    [string]$ServerPath = "/ruta/a/egarage"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Deploy: Registro Simplificado" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "ERROR: No se encontró manage.py. Ejecuta este script desde la raíz del proyecto." -ForegroundColor Red
    exit 1
}

Write-Host "Paso 1: Verificando archivos locales..." -ForegroundColor Yellow

$Files = @(
    "taller/views_extra/signup_redirects.py",
    "taller/forms/custom_signup.py",
    "templates/account/signup.html",
    "taller/views_extra/custom_signup.py",
    "gestion_taller/urls.py",
    "gestion_taller/settings.py",
    "taller/urls_extra/brasil.py",
    "taller/urls_extra/colombia.py",
    "taller/urls_extra/ecuador.py",
    "taller/urls_extra/mexico.py",
    "taller/urls_extra/peru.py",
    "taller/urls_extra/venezuela.py"
)

$MissingFiles = @()
foreach ($file in $Files) {
    if (-not (Test-Path $file)) {
        $MissingFiles += $file
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "ERROR: Archivos faltantes:" -ForegroundColor Red
    foreach ($file in $MissingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    exit 1
}

Write-Host "✓ Todos los archivos encontrados" -ForegroundColor Green
Write-Host ""

Write-Host "Paso 2: Copiando archivos al servidor..." -ForegroundColor Yellow
foreach ($file in $Files) {
    Write-Host "  Copiando $file..." -NoNewline
    
    # Obtener directorio
    $dir = Split-Path $file -Parent
    $fileName = Split-Path $file -Leaf
    
    # Crear directorio en servidor si no existe (usando SSH)
    $createDirCmd = "ssh $Server 'mkdir -p ${ServerPath}/${dir}'"
    Invoke-Expression $createDirCmd 2>$null
    
    # Copiar archivo usando SCP
    $scpCmd = "scp `"$file`" ${Server}:${ServerPath}/${file}"
    Invoke-Expression $scpCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ✗ ERROR" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Paso 3: Configurando permisos en servidor..." -ForegroundColor Yellow
$chmodFiles = @(
    "taller/views_extra/signup_redirects.py",
    "taller/forms/custom_signup.py",
    "templates/account/signup.html",
    "taller/views_extra/custom_signup.py",
    "gestion_taller/urls.py",
    "gestion_taller/settings.py"
)

foreach ($file in $chmodFiles) {
    $chmodCmd = "ssh $Server 'chmod 644 ${ServerPath}/${file}'"
    Invoke-Expression $chmodCmd 2>$null
}

# Permisos para archivos de urls_extra
$chmodExtraCmd = "ssh $Server 'chmod 644 ${ServerPath}/taller/urls_extra/*.py'"
Invoke-Expression $chmodExtraCmd 2>$null

Write-Host "✓ Permisos configurados" -ForegroundColor Green

Write-Host ""
Write-Host "Paso 4: Verificando sintaxis Python en servidor..." -ForegroundColor Yellow
$checkCmd = "ssh $Server 'cd ${ServerPath} && python manage.py check --deploy'"
Invoke-Expression $checkCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Verificación de Django falló" -ForegroundColor Red
    Write-Host "Verifica manualmente los errores en el servidor" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Sintaxis correcta" -ForegroundColor Green

Write-Host ""
Write-Host "Paso 5: Reiniciando aplicación..." -ForegroundColor Yellow

# Intentar reiniciar gunicorn
$gunicornCheck = "ssh $Server 'systemctl is-active --quiet gunicorn' 2>&1"
$gunicornResult = Invoke-Expression $gunicornCheck 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Reiniciando gunicorn..." -NoNewline
    $restartCmd = "ssh $Server 'sudo systemctl restart gunicorn'"
    Invoke-Expression $restartCmd 2>&1
    Write-Host " ✓" -ForegroundColor Green
} else {
    # Intentar uwsgi
    $uwsgiCheck = "ssh $Server 'systemctl is-active --quiet uwsgi' 2>&1"
    $uwsgiResult = Invoke-Expression $uwsgiCheck 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Reiniciando uwsgi..." -NoNewline
        $restartCmd = "ssh $Server 'sudo systemctl restart uwsgi'"
        Invoke-Expression $restartCmd 2>&1
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host "⚠ No se detectó método de restart automático" -ForegroundColor Yellow
        Write-Host "Reinicia manualmente la aplicación Django" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deploy completado" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Verificar registro: https://tudominio.com/accounts/signup/?from=cl"
Write-Host "  2. Verificar redirect: https://tudominio.com/cl/accounts/signup/"
Write-Host "  3. Test registro completo con teléfono"
Write-Host ""
