# ========================================
# SCRIPT: Sincronizar 100% del SERVIDOR -> PC
# ========================================
# USO: .\scripts\sync_from_server_completo.ps1
# DESCRIPCIÓN: Descarga TODO el proyecto desde el servidor PythonAnywhere
# IMPORTANTE: Hace backup automático de cambios locales antes de sobrescribir

param(
    [string]$ServerUser = "atlantareciclajes",
    [string]$ServerHost = "atlantareciclajes.pythonanywhere.com",
    [string]$ServerPath = "/home/atlantareciclajes/apps/egarage/current",
    [string]$LocalPath = "E:\projecto\e_garage",
    [switch]$SkipBackup = $false
)

$ErrorActionPreference = "Stop"

# Colores
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Yellow "================================================"
Write-ColorOutput Yellow "  SINCRONIZACIÓN COMPLETA SERVIDOR -> PC"
Write-ColorOutput Yellow "================================================"
Write-Output ""

# ========================================
# 1. VERIFICAR CONFIGURACIÓN
# ========================================
Write-ColorOutput Cyan "1. Verificando configuración..."

Write-Output "   Servidor: $ServerUser@$ServerHost"
Write-Output "   Ruta remota: $ServerPath"
Write-Output "   Ruta local: $LocalPath"
Write-Output ""

# Verificar que la ruta local existe
if (-not (Test-Path $LocalPath)) {
    Write-ColorOutput Red "ERROR: La ruta local no existe: $LocalPath"
    exit 1
}

# Verificar que estamos en el directorio correcto
if (-not (Test-Path (Join-Path $LocalPath "manage.py"))) {
    Write-ColorOutput Yellow "ADVERTENCIA: No se encontró manage.py en la ruta local"
    Write-Output "   ¿Estás seguro de que esta es la ruta correcta del proyecto?"
    $continue = Read-Host "   Continuar de todas formas? (s/n)"
    if ($continue -ne "s") {
        exit 1
    }
}

Write-ColorOutput Green "✓ Configuración verificada"
Write-Output ""

# ========================================
# 2. BACKUP DE CAMBIOS LOCALES
# ========================================
if (-not $SkipBackup) {
    Write-ColorOutput Cyan "2. Haciendo backup de cambios locales..."
    
    # Verificar estado de Git
    Push-Location $LocalPath
    try {
        $gitStatus = git status --porcelain 2>$null
        if ($gitStatus) {
            Write-ColorOutput Yellow "   Tienes cambios sin commitear:"
            git status --short | ForEach-Object { Write-Output "   $_" }
            Write-Output ""
            
            $backupChoice = Read-Host "   ¿Qué quieres hacer? (1=Stash, 2=Commit, 3=Ignorar, 4=Cancelar)"
            switch ($backupChoice) {
                "1" {
                    $stashName = "backup-pre-sync-$(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
                    git stash save $stashName
                    Write-ColorOutput Green "   ✓ Cambios guardados en stash: $stashName"
                }
                "2" {
                    $commitMsg = Read-Host "   Mensaje del commit"
                    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
                        $commitMsg = "backup: Cambios locales antes de sync desde servidor"
                    }
                    git add -A
                    git commit -m $commitMsg
                    Write-ColorOutput Green "   ✓ Cambios commiteados"
                }
                "3" {
                    Write-ColorOutput Yellow "   ⚠ Continuando sin backup (los cambios locales se perderán)"
                }
                default {
                    Write-ColorOutput Red "   Operación cancelada"
                    exit 1
                }
            }
        } else {
            Write-ColorOutput Green "   ✓ No hay cambios locales sin commitear"
        }
    } catch {
        Write-ColorOutput Yellow "   ⚠ Git no disponible o no es un repositorio Git"
    }
    Pop-Location
    
    Write-Output ""
}

# ========================================
# 3. CREAR CARPETA DE BACKUP TEMPORAL
# ========================================
Write-ColorOutput Cyan "3. Creando backup temporal de archivos críticos..."
$backupDir = Join-Path $LocalPath ".sync_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Archivos críticos a respaldar
$criticalFiles = @(
    "manage.py",
    "db.sqlite3",
    "gestion_taller\settings.py",
    "gestion_taller\settings\*.py",
    ".env"
)

foreach ($file in $criticalFiles) {
    $fullPath = Join-Path $LocalPath $file
    if (Test-Path $fullPath) {
        $destPath = Join-Path $backupDir $file
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item -Path $fullPath -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-ColorOutput Green "✓ Backup temporal creado en: $backupDir"
Write-Output ""

# ========================================
# 4. PREPARAR COMANDOS DE SINCRONIZACIÓN
# ========================================
Write-ColorOutput Cyan "4. Preparando sincronización..."
Write-Output ""

# Archivos y carpetas a EXCLUIR de la sincronización
$excludes = @(
    "db.sqlite3",           # Base de datos local (no sobrescribir)
    "media/",               # Archivos subidos por usuarios
    "staticfiles/",         # Archivos estáticos compilados
    "__pycache__/",         # Cache de Python
    "*.pyc",                # Bytecode de Python
    "*.pyo",                # Bytecode optimizado
    ".env",                 # Variables de entorno locales
    "*.log",                # Logs locales
    "venv/",                # Entorno virtual local
    "node_modules/",        # Dependencias Node.js
    ".git/",                # Repositorio Git
    ".sync_backup_*",       # Backups de sincronización
    "htmlcov/",             # Coverage de tests
    ".pytest_cache/",       # Cache de pytest
    "*.swp",                # Archivos temporales
    "*.swo",                # Archivos temporales
    ".DS_Store"             # Archivos de macOS
)

# Construir string de exclusiones para rsync
$excludeArgs = $excludes | ForEach-Object { "--exclude='$_'" }
$excludeString = $excludeArgs -join " "

# Comando rsync (para WSL/Git Bash)
$rsyncCmd = "rsync -avz --progress $excludeString $ServerUser@$ServerHost`:$ServerPath/ $LocalPath/"

# Comando SCP alternativo (más simple pero menos eficiente)
$scpCmd = "scp -r $ServerUser@$ServerHost`:$ServerPath/* $LocalPath/"

Write-ColorOutput Yellow "OPCIONES DE SINCRONIZACIÓN:"
Write-Output ""
Write-Output "OPCIÓN A - FileZilla (Recomendado para Windows):"
Write-Output "   1. Abrir FileZilla"
Write-Output "   2. Conectar a:"
Write-Output "      Host: $ServerHost"
Write-Output "      Usuario: $ServerUser"
Write-Output "      Puerto: 22 (SFTP)"
Write-Output "   3. Navegar a: $ServerPath"
Write-Output "   4. Seleccionar TODAS las carpetas y archivos"
Write-Output "   5. Descargar a: $LocalPath"
Write-Output "   6. Sobrescribir archivos existentes"
Write-Output ""
Write-Output "OPCIÓN B - WSL/Git Bash con rsync:"
Write-ColorOutput White "   $rsyncCmd"
Write-Output ""
Write-Output "OPCIÓN C - PowerShell con SCP (si tienes OpenSSH):"
Write-ColorOutput White "   $scpCmd"
Write-Output ""

# ========================================
# 5. MENÚ DE OPCIONES
# ========================================
Write-ColorOutput Cyan "5. Selecciona método de sincronización:"
Write-Output ""
Write-Output "   [1] Usar FileZilla (manual - más seguro)"
Write-Output "   [2] Generar script para WSL/Git Bash (rsync)"
Write-Output "   [3] Generar script para PowerShell (SCP)"
Write-Output "   [4] Solo mostrar comandos (no ejecutar)"
Write-Output "   [5] Cancelar"
Write-Output ""

$choice = Read-Host "   Tu elección (1-5)"

switch ($choice) {
    "1" {
        Write-Output ""
        Write-ColorOutput Green "✓ INSTRUCCIONES PARA FILEZILLA:"
        Write-Output ""
        Write-Output "   1. Abre FileZilla"
        Write-Output "   2. Archivo → Gestor de sitios → Nuevo sitio"
        Write-Output "   3. Configura:"
        Write-Output "      - Protocolo: SFTP - SSH File Transfer Protocol"
        Write-Output "      - Host: $ServerHost"
        Write-Output "      - Puerto: 22"
        Write-Output "      - Tipo de acceso: Normal"
        Write-Output "      - Usuario: $ServerUser"
        Write-Output "      - Contraseña: [tu contraseña de PythonAnywhere]"
        Write-Output ""
        Write-Output "   4. Conectar"
        Write-Output "   5. En el panel REMOTO, navegar a: $ServerPath"
        Write-Output "   6. En el panel LOCAL, navegar a: $LocalPath"
        Write-Output "   7. Seleccionar TODOS los archivos y carpetas del servidor"
        Write-Output "   8. Arrastrar al panel local (o clic derecho → Descargar)"
        Write-Output "   9. Cuando pregunte por sobrescribir, elegir 'Sobrescribir'"
        Write-Output ""
        Write-Output "   ⚠ IMPORTANTE: NO descargar estas carpetas del servidor:"
        Write-Output "      - media/ (archivos de usuarios)"
        Write-Output "      - staticfiles/ (se regenera con collectstatic)"
        Write-Output "      - __pycache__/ (cache de Python)"
        Write-Output ""
        Write-ColorOutput Yellow "   Presiona Enter cuando hayas terminado la descarga..."
        Read-Host
    }
    "2" {
        $scriptPath = Join-Path $LocalPath "sync_rsync.sh"
        $scriptContent = @"
#!/bin/bash
# Script generado para sincronizar desde servidor
# Ejecutar en WSL o Git Bash

SERVER_USER="$ServerUser"
SERVER_HOST="$ServerHost"
SERVER_PATH="$ServerPath"
LOCAL_PATH="$LocalPath"

echo "Sincronizando desde servidor..."
rsync -avz --progress $excludeString `$SERVER_USER@`$SERVER_HOST:`$SERVER_PATH/ `$LOCAL_PATH/

echo ""
echo "✓ Sincronización completada"
"@
        $scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8
        Write-ColorOutput Green "✓ Script generado: $scriptPath"
        Write-Output ""
        Write-Output "   Para ejecutar:"
        Write-Output "   1. Abre WSL o Git Bash"
        Write-Output "   2. cd $LocalPath"
        Write-Output "   3. bash sync_rsync.sh"
        Write-Output ""
    }
    "3" {
        $scriptPath = Join-Path $LocalPath "sync_scp.ps1"
        $scriptContent = @"
# Script generado para sincronizar desde servidor
# Ejecutar en PowerShell

`$ServerUser = "$ServerUser"
`$ServerHost = "$ServerHost"
`$ServerPath = "$ServerPath"
`$LocalPath = "$LocalPath"

Write-Host "Sincronizando desde servidor..."
Write-Host "Esto puede tardar varios minutos..."

# Descargar archivos principales
scp -r `$ServerUser@`$ServerHost`:`$ServerPath/* `$LocalPath/

Write-Host ""
Write-Host "✓ Sincronización completada"
"@
        $scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8
        Write-ColorOutput Green "✓ Script generado: $scriptPath"
        Write-Output ""
        Write-Output "   Para ejecutar:"
        Write-Output "   1. Abre PowerShell"
        Write-Output "   2. cd $LocalPath"
        Write-Output "   3. .\sync_scp.ps1"
        Write-Output ""
    }
    "4" {
        Write-Output ""
        Write-ColorOutput Yellow "COMANDOS PARA COPIAR Y EJECUTAR:"
        Write-Output ""
        Write-Output "RSYNC (WSL/Git Bash):"
        Write-ColorOutput White "   $rsyncCmd"
        Write-Output ""
        Write-Output "SCP (PowerShell):"
        Write-ColorOutput White "   $scpCmd"
        Write-Output ""
    }
    "5" {
        Write-ColorOutput Yellow "Operación cancelada"
        Remove-Item -Path $backupDir -Recurse -Force -ErrorAction SilentlyContinue
        exit 0
    }
    default {
        Write-ColorOutput Red "Opción inválida"
        Remove-Item -Path $backupDir -Recurse -Force -ErrorAction SilentlyContinue
        exit 1
    }
}

# ========================================
# 6. VERIFICAR CAMBIOS DESPUÉS DE SINCRONIZACIÓN
# ========================================
Write-Output ""
Write-ColorOutput Cyan "6. Después de sincronizar, ejecuta este script nuevamente para verificar cambios"
Write-Output ""

# Verificar si hay cambios
Push-Location $LocalPath
try {
    $gitStatus = git status --porcelain 2>$null
    if ($gitStatus) {
        Write-ColorOutput Green "✓ Se detectaron cambios después de la sincronización:"
        git status --short | ForEach-Object { Write-Output "   $_" }
        Write-Output ""
        
        $review = Read-Host "¿Quieres revisar los cambios? (s/n)"
        if ($review -eq "s") {
            git diff --stat
        }
        
        Write-Output ""
        Write-ColorOutput Yellow "SIGUIENTE PASO:"
        Write-Output "   1. Revisa los cambios: git diff"
        Write-Output "   2. Si todo está bien, haz commit:"
        Write-Output "      git add -A"
        Write-Output "      git commit -m 'sync: Actualización completa desde servidor'"
        Write-Output "   3. Si algo está mal, restaura desde backup:"
        Write-Output "      Restaurar desde: $backupDir"
    } else {
        Write-ColorOutput Green "✓ No se detectaron cambios (o la sincronización aún no se completó)"
    }
} catch {
    Write-ColorOutput Yellow "⚠ No se pudo verificar cambios con Git"
}
Pop-Location

Write-Output ""
Write-ColorOutput Green "================================================"
Write-ColorOutput Green "  PROCESO COMPLETADO"
Write-ColorOutput Green "================================================"
Write-Output ""
Write-Output "Backup temporal guardado en: $backupDir"
Write-Output "Puedes eliminarlo después de verificar que todo está bien."
Write-Output ""




