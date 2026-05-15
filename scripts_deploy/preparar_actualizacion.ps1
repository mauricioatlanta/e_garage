# ======================================================
# Script: PREPARAR ACTUALIZACION PARA PYTHONANYWHERE
# Para: atlantareciclajes @ PythonAnywhere
# ======================================================

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "PREPARANDO ACTUALIZACION PARA SERVIDOR" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Variables - Obtener ruta del proyecto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = (Resolve-Path (Join-Path $scriptPath "..")).Path
$DEPLOY_DIR = Join-Path $PROJECT_ROOT "deploy_atlantareciclajes"
$UPDATE_DIR = Join-Path $PROJECT_ROOT "egarage_update"
$ZIP_NAME = "egarage_update_atlantareciclajes.zip"
$ZIP_PATH = Join-Path $UPDATE_DIR $ZIP_NAME

# Verificar que estamos en el proyecto correcto
$managePyPath = Join-Path $PROJECT_ROOT "manage.py"
if (-not (Test-Path $managePyPath)) {
    Write-Host "ERROR: No se encontro manage.py" -ForegroundColor Red
    Write-Host "   Ejecuta este script desde la raiz del proyecto" -ForegroundColor Yellow
    Write-Host "   Ruta buscada: $managePyPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "Proyecto encontrado: $PROJECT_ROOT" -ForegroundColor Green
Write-Host ""

# Crear directorio de actualizacion si no existe
if (-not (Test-Path $UPDATE_DIR)) {
    New-Item -ItemType Directory -Path $UPDATE_DIR -Force | Out-Null
    Write-Host "Carpeta de actualizacion creada: $UPDATE_DIR" -ForegroundColor Green
}

# Verificar si existe deploy_atlantareciclajes
if (-not (Test-Path $DEPLOY_DIR)) {
    Write-Host "No se encontro la carpeta deploy_atlantareciclajes/" -ForegroundColor Yellow
    Write-Host "   Creando estructura de despliegue..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $DEPLOY_DIR -Force | Out-Null
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "COPIANDO ARCHIVOS PARA ACTUALIZACION..." -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Funcion para copiar directorio
function Copy-Directory {
    param(
        [string]$Source,
        [string]$Dest,
        [string]$Description
    )
    
    if (Test-Path $Source) {
        $destPath = Join-Path $DEPLOY_DIR $Dest
        $destParent = Split-Path $destPath -Parent
        if (-not (Test-Path $destParent)) {
            New-Item -ItemType Directory -Path $destParent -Force | Out-Null
        }
        Copy-Item -Path $Source -Destination $destPath -Recurse -Force
        Write-Host "   OK: $Description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "   ADVERTENCIA: $Description (no encontrado)" -ForegroundColor Yellow
        return $false
    }
}

# Funcion para copiar archivo
function Copy-File {
    param(
        [string]$Source,
        [string]$Dest,
        [string]$Description
    )
    
    if (Test-Path $Source) {
        $destPath = Join-Path $DEPLOY_DIR $Dest
        $destParent = Split-Path $destPath -Parent
        if (-not (Test-Path $destParent)) {
            New-Item -ItemType Directory -Path $destParent -Force | Out-Null
        }
        Copy-Item -Path $Source -Destination $destPath -Force
        Write-Host "   OK: $Description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "   ADVERTENCIA: $Description (no encontrado)" -ForegroundColor Yellow
        return $false
    }
}

$archivosCopiados = 0

# Taller - Asegurar que ia_urls.py e ia_views.py se copien
Write-Host "Copiando taller (incluyendo ia_urls.py e ia_views.py)..." -ForegroundColor Cyan
$tallerSource = Join-Path $PROJECT_ROOT "taller"
if (Test-Path $tallerSource) {
    Copy-Directory -Source $tallerSource -Dest "taller" -Description "Taller completo (incluye IA)"
    $archivosCopiados++
} else {
    Write-Host "   ADVERTENCIA: No se encontro carpeta taller/ en $tallerSource" -ForegroundColor Yellow
}

# Templates
Write-Host "Copiando templates..." -ForegroundColor Cyan
$templatesSource = Join-Path $PROJECT_ROOT "templates"
if (Test-Path $templatesSource) {
    if (Copy-Directory -Source $templatesSource -Dest "templates" -Description "Templates completos") {
        $archivosCopiados++
    }
}

# Static (CSS/JS)
Write-Host ""
Write-Host "Copiando static (CSS/JS)..." -ForegroundColor Cyan
$staticSource = Join-Path $PROJECT_ROOT "static"
if (Test-Path $staticSource) {
    if (Copy-Directory -Source $staticSource -Dest "static" -Description "Static completo (CSS/JS)") {
        $archivosCopiados++
    }
} else {
    Write-Host "   ADVERTENCIA: No se encontro carpeta static/ en $staticSource" -ForegroundColor Yellow
}

# Codigo Python - Taller
Write-Host ""
Write-Host "Copiando codigo Python (taller)..." -ForegroundColor Cyan

# Views Extra
if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "taller\views_extra") -Dest "taller\views_extra" -Description "Views extra") {
    $archivosCopiados++
}

# Models
if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "taller\models") -Dest "taller\models" -Description "Models") {
    $archivosCopiados++
}

# Forms
if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "taller\forms") -Dest "taller\forms" -Description "Forms") {
    $archivosCopiados++
}

# Middleware
if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "taller\middleware") -Dest "taller\middleware" -Description "Middleware") {
    $archivosCopiados++
}

# Context Processors
if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "taller\context_processors") -Dest "taller\context_processors" -Description "Context processors") {
    $archivosCopiados++
}

# Management Commands
if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "taller\management") -Dest "taller\management" -Description "Management commands") {
    $archivosCopiados++
}

# Backends
if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "taller\backends") -Dest "taller\backends" -Description "Backends") {
    $archivosCopiados++
}

# Archivos individuales de taller
if (Copy-File -Source (Join-Path $PROJECT_ROOT "taller\signals.py") -Dest "taller\signals.py" -Description "signals.py") {
    $archivosCopiados++
}

if (Copy-File -Source (Join-Path $PROJECT_ROOT "taller\apps.py") -Dest "taller\apps.py" -Description "apps.py") {
    $archivosCopiados++
}

if (Copy-File -Source (Join-Path $PROJECT_ROOT "taller\urls.py") -Dest "taller\urls.py" -Description "taller/urls.py") {
    $archivosCopiados++
}

# IA URLs y Views (CRÍTICO para evitar NameError)
if (Copy-File -Source (Join-Path $PROJECT_ROOT "taller\ia_urls.py") -Dest "taller\ia_urls.py" -Description "taller/ia_urls.py") {
    $archivosCopiados++
}

if (Copy-File -Source (Join-Path $PROJECT_ROOT "taller\ia_views.py") -Dest "taller\ia_views.py" -Description "taller/ia_views.py") {
    $archivosCopiados++
}

# Configuracion Django
Write-Host ""
Write-Host "Copiando configuracion..." -ForegroundColor Cyan

if (Copy-File -Source (Join-Path $PROJECT_ROOT "gestion_taller\urls.py") -Dest "gestion_taller\urls.py" -Description "gestion_taller/urls.py") {
    $archivosCopiados++
}

# Otras apps
Write-Host ""
Write-Host "Copiando otras apps..." -ForegroundColor Cyan

if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "core") -Dest "core" -Description "Core") {
    $archivosCopiados++
}

if (Copy-Directory -Source (Join-Path $PROJECT_ROOT "ubicacion") -Dest "ubicacion" -Description "Ubicacion") {
    $archivosCopiados++
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "CREANDO ARCHIVO ZIP..." -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Eliminar ZIP anterior si existe
if (Test-Path $ZIP_PATH) {
    Remove-Item $ZIP_PATH -Force
    Write-Host "ZIP anterior eliminado" -ForegroundColor Yellow
}

# Crear ZIP
Write-Host "Comprimiendo archivos..." -ForegroundColor Cyan
try {
    # Usar Compress-Archive de PowerShell
    # IMPORTANTE: Comprimir la carpeta completa, no solo su contenido
    $tempZip = Join-Path $UPDATE_DIR "temp_$ZIP_NAME"
    if (Test-Path $tempZip) {
        Remove-Item $tempZip -Force
    }
    
    # Cambiar al directorio padre para incluir el nombre de la carpeta en el ZIP
    $parentDir = Split-Path $DEPLOY_DIR -Parent
    $folderName = Split-Path $DEPLOY_DIR -Leaf
    
    # Comprimir la carpeta completa (no solo su contenido)
    Compress-Archive -Path $DEPLOY_DIR -DestinationPath $tempZip -Force
    
    # Mover a la ubicacion final
    Move-Item -Path $tempZip -Destination $ZIP_PATH -Force
    
    $zipSize = (Get-Item $ZIP_PATH).Length / 1MB
    Write-Host "   OK: ZIP creado: $ZIP_NAME ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
    Write-Host "   Estructura: deploy_atlantareciclajes/ (carpeta incluida)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR al crear ZIP: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Alternativa: Comprime manualmente la carpeta:" -ForegroundColor Yellow
    Write-Host "      $DEPLOY_DIR" -ForegroundColor Yellow
    Write-Host "      Nombre: $ZIP_NAME" -ForegroundColor Yellow
    Write-Host "      IMPORTANTE: Incluir la carpeta deploy_atlantareciclajes en el ZIP" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "PREPARACION COMPLETADA" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "RESUMEN:" -ForegroundColor Cyan
Write-Host "   Archivos copiados: $archivosCopiados" -ForegroundColor White
Write-Host "   ZIP creado: $ZIP_NAME" -ForegroundColor White
Write-Host "   Ubicacion: $ZIP_PATH" -ForegroundColor White
Write-Host ""
Write-Host "SIGUIENTE PASO - SUBIR AL SERVIDOR:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   1. Abrir FileZilla" -ForegroundColor White
Write-Host "   2. Conectar a:" -ForegroundColor White
Write-Host "      Host: atlantareciclajes.pythonanywhere.com" -ForegroundColor Yellow
Write-Host "      Puerto: 22 (SFTP)" -ForegroundColor Yellow
Write-Host "      Usuario: atlantareciclajes" -ForegroundColor Yellow
Write-Host ""
Write-Host "   3. Navegar a: /home/atlantareciclajes/egarage_update/" -ForegroundColor White
Write-Host "      (Crear carpeta si no existe)" -ForegroundColor Yellow
Write-Host ""
Write-Host "   4. Subir archivo: $ZIP_NAME" -ForegroundColor White
Write-Host ""
Write-Host "   5. En PythonAnywhere Console, ejecutar:" -ForegroundColor White
Write-Host "      cd /home/atlantareciclajes/scripts_deploy/" -ForegroundColor Yellow
Write-Host "      ./1_backup_FIXED.sh" -ForegroundColor Yellow
Write-Host "      ./2_actualizar_ESTRUCTURA_COMPLETA.sh" -ForegroundColor Yellow
Write-Host ""
Write-Host "   6. Reload en Web panel de PythonAnywhere" -ForegroundColor White
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
