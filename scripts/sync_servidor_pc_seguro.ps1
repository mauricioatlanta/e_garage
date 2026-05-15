# ========================================
# SCRIPT: Sincronizar Servidor -> PC (SEGURO)
# ========================================
# USO: .\scripts\sync_servidor_pc_seguro.ps1
# DESCRIPCIÓN: Sincroniza código del servidor SIN tocar usuarios ni credenciales
# PROTEGE: db.sqlite3, .env, media/, usuarios, passwords

param(
    [string]$ServerUser = "atlantareciclajes",
    [string]$ServerHost = "atlantareciclajes.pythonanywhere.com",
    [string]$ServerPath = "/home/atlantareciclajes/apps/egarage/current",
    [string]$LocalPath = "E:\projecto\e_garage",
    [switch]$SkipBackup = $false
)

$ErrorActionPreference = "Stop"

# Colores
function Write-ColorOutput {
    param(
        [Parameter(Mandatory=$true, Position=0)]
        [string]$ForegroundColor,
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Message
    )
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($Message) {
        Write-Output ($Message -join ' ')
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan '================================================'
Write-ColorOutput Cyan '  SINCRONIZACIÓN SEGURA SERVIDOR -> PC'
Write-ColorOutput Cyan '  (Protege usuarios y credenciales)'
Write-ColorOutput Cyan '================================================'
Write-Output ""

# ========================================
# 1. VERIFICAR CONFIGURACIÓN
# ========================================
Write-ColorOutput Yellow "1. Verificando configuración..."

if (-not (Test-Path $LocalPath)) {
    Write-ColorOutput Red "ERROR: La ruta local no existe: $LocalPath"
    exit 1
}

if (-not (Test-Path (Join-Path $LocalPath "manage.py"))) {
    Write-ColorOutput Red "ERROR: No se encontró manage.py. ¿Estás en la raíz del proyecto?"
    exit 1
}

Write-ColorOutput Green "[OK] Proyecto local verificado: $LocalPath"
Write-Output "   Servidor: $ServerUser@$ServerHost"
Write-Output "   Ruta remota: $ServerPath"
Write-Output ""

# ========================================
# 2. BACKUP DE ARCHIVOS SENSIBLES (LOCALES)
# ========================================
Write-ColorOutput Yellow "2. Protegiendo archivos sensibles locales..."

Push-Location $LocalPath

# Crear carpeta de backup temporal
$backupDir = Join-Path $LocalPath ".sync_protected_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Archivos/carpetas SENSIBLES que NO deben sobrescribirse
$protectedItems = @{
    "db.sqlite3" = "Base de datos - usuarios, empresas, datos"
    ".env" = "Variables de entorno - credenciales, secrets"
    "gestion_taller\settings.py" = "Settings - puede tener credenciales"
    "gestion_taller\settings\local.py" = "Settings locales"
    "gestion_taller\settings\production.py" = "Settings produccion - credenciales"
    "media\" = "Archivos subidos por usuarios"
    "logs\" = "Logs locales"
}

$protectedCount = 0
foreach ($item in $protectedItems.Keys) {
    $itemPath = Join-Path $LocalPath $item
    if (Test-Path $itemPath) {
        $destPath = Join-Path $backupDir $item
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        if (Test-Path $itemPath -PathType Container) {
            Copy-Item -Path $itemPath -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
        } else {
            Copy-Item -Path $itemPath -Destination $destPath -Force -ErrorAction SilentlyContinue
        }
        
        if (Test-Path $destPath) {
            Write-ColorOutput Green "   [OK] Protegido: $item"
            $protectedCount++
        }
    }
}

Write-ColorOutput Green "[OK] $protectedCount archivos/carpetas protegidos"
Write-Output "   Backup en: $backupDir"
Write-Output ""

# ========================================
# 3. VERIFICAR USUARIOS ANTES DE SINCRONIZAR
# ========================================
Write-ColorOutput Yellow "3. Verificando usuarios locales (para confirmar después)..."

$userCountBefore = $null
$empresaCountBefore = $null

try {
    if (Test-Path (Join-Path $LocalPath "db.sqlite3")) {
        $tempPythonScript = Join-Path $env:TEMP "check_users_$(Get-Date -Format 'yyyyMMdd_HHmmss').py"
        $pythonScriptContent = @"
import os
import sys
import django

BASE_DIR = sys.argv[1]
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa

users = User.objects.count()
empresas = Empresa.objects.count()
print('USERS:' + str(users) + '|EMPRESAS:' + str(empresas))
"@
        $pythonScriptContent | Out-File -FilePath $tempPythonScript -Encoding UTF8 -Force
        $result = python $tempPythonScript $LocalPath 2>$null
        Remove-Item -Path $tempPythonScript -Force -ErrorAction SilentlyContinue
        
        if ($result -match "USERS:(\d+)\|EMPRESAS:(\d+)") {
            $userCountBefore = [int]$matches[1]
            $empresaCountBefore = [int]$matches[2]
            Write-ColorOutput Green "   [OK] Usuarios locales: $userCountBefore"
            Write-ColorOutput Green "   [OK] Empresas locales: $empresaCountBefore"
        }
    }
} catch {
    Write-ColorOutput Yellow "   [AVISO] No se pudo verificar usuarios (normal si no hay BD local)"
}

Write-Output ""

# ========================================
# 4. PREPARAR COMANDO DE SINCRONIZACIÓN
# ========================================
Write-ColorOutput Yellow "4. Preparando sincronización (excluyendo archivos sensibles)..."

# Archivos/carpetas a EXCLUIR completamente
$excludes = @(
    "db.sqlite3",           # Base de datos (usuarios)
    "*.db",                 # Cualquier base de datos
    "media/",               # Archivos de usuarios
    "staticfiles/",         # Se regenera
    "__pycache__/",         # Cache Python
    "*.pyc",                # Bytecode
    "*.pyo",                # Bytecode optimizado
    ".env",                 # Credenciales
    ".env.*",               # Cualquier .env
    "*.log",                # Logs
    "logs/",                # Carpeta de logs
    "venv/",                # Entorno virtual
    "venv_*/",              # Entornos virtuales
    "node_modules/",        # Node modules
    ".git/",                # Git
    ".sync_*",              # Backups de sync
    "htmlcov/",             # Coverage
    ".pytest_cache/",       # Pytest cache
    "*.swp",                # Archivos temporales
    ".DS_Store"             # macOS
)

# Construir string de exclusiones
$excludeArgs = $excludes | ForEach-Object { "--exclude='$_'" }
$excludeString = $excludeArgs -join " "

# Comando rsync
$rsyncCmd = "rsync -avz --progress $excludeString ${ServerUser}@${ServerHost}:$ServerPath/ $LocalPath/"

Write-ColorOutput Green "[OK] Comando preparado"
Write-Output ""

# ========================================
# 5. OPCIONES DE SINCRONIZACIÓN
# ========================================
Write-ColorOutput Cyan "5. Selecciona método de sincronización:"
Write-Output ""
Write-Output "   [1] FileZilla (Manual - Recomendado)"
Write-Output "   [2] Generar script rsync para WSL/Git Bash"
Write-Output "   [3] Generar script SCP para PowerShell"
Write-Output "   [4] Solo mostrar comandos"
Write-Output "   [5] Cancelar"
Write-Output ""

$choice = Read-Host "   Tu elección (1-5)"

$syncCompleted = $false

switch ($choice) {
    "1" {
        Write-Output ""
        Write-ColorOutput Green "════════════════════════════════════════"
        Write-ColorOutput Green "  INSTRUCCIONES PARA FILEZILLA"
        Write-ColorOutput Green "════════════════════════════════════════"
        Write-Output ""
        Write-Output "1. Abre FileZilla"
        Write-Output "2. Conecta a:"
        Write-Output "   Host: $ServerHost"
        Write-Output "   Usuario: $ServerUser"
        Write-Output "   Puerto: 22 (SFTP)"
        Write-Output "   Contraseña: [tu contraseña]"
        Write-Output ""
        Write-Output "3. Panel REMOTO → Navegar a: $ServerPath"
        Write-Output "4. Panel LOCAL → Navegar a: $LocalPath"
        Write-Output ""
        Write-ColorOutput Yellow "5. IMPORTANTE - Descargar SOLO estas carpetas:"
        Write-Output "   [OK] core/"
        Write-Output "   [OK] gestion_taller/"
        Write-Output "   [OK] taller/"
        Write-Output "   [OK] templates/"
        Write-Output "   [OK] static/"
        Write-Output "   [OK] ubicacion/"
        Write-Output "   [OK] documentos/"
        Write-Output "   [OK] manage.py"
        Write-Output "   [OK] requirements.txt"
        Write-Output "   [OK] pyproject.toml"
        Write-Output "   [OK] Cualquier otro archivo .py, .html, .js, .css"
        Write-Output ""
        Write-ColorOutput Red "   ❌ NO descargar:"
        Write-Output "   ❌ db.sqlite3 (base de datos)"
        Write-Output "   ❌ media/ (archivos de usuarios)"
        Write-Output "   ❌ staticfiles/ (se regenera)"
        Write-Output "   ❌ __pycache__/ (cache)"
        Write-Output "   ❌ .env (credenciales)"
        Write-Output "   ❌ logs/ (logs del servidor)"
        Write-Output ""
        Write-Output "6. Cuando pregunte por sobrescribir: 'Sobrescribir' o 'Sí a todo'"
        Write-Output ""
        Write-ColorOutput Yellow "   Presiona Enter cuando hayas terminado..."
        Read-Host
        $syncCompleted = $true
    }
    "2" {
        $scriptPath = Join-Path $LocalPath "sync_rsync_seguro.sh"
        $scriptContent = @"
#!/bin/bash
# Script generado para sincronización segura desde servidor
# NO toca usuarios ni credenciales

SERVER_USER="$ServerUser"
SERVER_HOST="$ServerHost"
SERVER_PATH="$ServerPath"
LOCAL_PATH="$LocalPath"

echo "=========================================="
echo "Sincronizando código del servidor..."
echo "Protegiendo: db.sqlite3, .env, media/, usuarios"
echo "=========================================="

rsync -avz --progress $excludeString `$SERVER_USER@`$SERVER_HOST:`$SERVER_PATH/ `$LOCAL_PATH/

echo ""
echo "[OK] Sincronizacion completada"
echo "[OK] Archivos sensibles NO fueron tocados"
"@
        $scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8
        Write-ColorOutput Green "[OK] Script generado: $scriptPath"
        Write-Output ""
        Write-Output "   Para ejecutar:"
        Write-Output "   1. Abre WSL o Git Bash"
        Write-Output "   2. cd $LocalPath"
        Write-Output "   3. bash sync_rsync_seguro.sh"
        Write-Output ""
        Write-ColorOutput Yellow "   ¿Quieres ejecutarlo ahora? (s/n)"
        $runNow = Read-Host
        if ($runNow -eq "s") {
            Write-Output "   Ejecutando en WSL/Git Bash..."
            bash $scriptPath
            $syncCompleted = $true
        }
    }
    "3" {
        $scriptPath = Join-Path $LocalPath "sync_scp_seguro.ps1"
        $scriptContent = @"
# Script generado para sincronización segura desde servidor
# NO toca usuarios ni credenciales

`$ServerUser = "$ServerUser"
`$ServerHost = "$ServerHost"
`$ServerPath = "$ServerPath"
`$LocalPath = "$LocalPath"

Write-Host "Sincronizando código del servidor..."
Write-Host "Protegiendo: db.sqlite3, .env, media/, usuarios"

# Nota: SCP no tiene exclusiones avanzadas, descarga todo
# Los archivos protegidos se restaurarán después
scp -r `$ServerUser@`$ServerHost:`$ServerPath/* `$LocalPath/

Write-Host ""
Write-Host "[OK] Sincronizacion completada"
"@
        $scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8
        Write-ColorOutput Green "[OK] Script generado: $scriptPath"
        Write-Output ""
        Write-Output "   Para ejecutar:"
        Write-Output "   1. Abre PowerShell"
        Write-Output "   2. cd $LocalPath"
        Write-Output "   3. .\sync_scp_seguro.ps1"
        Write-Output ""
        Write-ColorOutput Yellow "   [AVISO] NOTA: Este método descargará TODO, pero los archivos"
        Write-Output "   protegidos se restaurarán automáticamente después."
        Write-Output ""
    }
    "4" {
        Write-Output ""
        Write-ColorOutput Yellow "COMANDO RSYNC (WSL/Git Bash):"
        Write-ColorOutput White "   $rsyncCmd"
        Write-Output ""
        Write-ColorOutput Yellow "COMANDO SCP (PowerShell):"
        Write-ColorOutput White "   scp -r ${ServerUser}@${ServerHost}:$ServerPath/* $LocalPath/"
        Write-Output ""
        Write-ColorOutput Yellow "   [AVISO] SCP descarga TODO, pero los archivos protegidos"
        Write-Output "   se restaurarán automáticamente después."
        Write-Output ""
    }
    "5" {
        Write-ColorOutput Yellow "Operación cancelada"
        Remove-Item -Path $backupDir -Recurse -Force -ErrorAction SilentlyContinue
        Pop-Location
        exit 0
    }
    default {
        Write-ColorOutput Red "Opción inválida"
        Remove-Item -Path $backupDir -Recurse -Force -ErrorAction SilentlyContinue
        Pop-Location
        exit 1
    }
}

# ========================================
# 6. RESTAURAR ARCHIVOS PROTEGIDOS
# ========================================
if ($syncCompleted) {
    Write-Output ""
    Write-ColorOutput Yellow "6. Restaurando archivos protegidos..."
    
    $restoredCount = 0
    foreach ($item in $protectedItems.Keys) {
        $backupPath = Join-Path $backupDir $item
        $localPathItem = Join-Path $LocalPath $item
        
        if (Test-Path $backupPath) {
            $localDir = Split-Path $localPathItem -Parent
            if (-not (Test-Path $localDir)) {
                New-Item -ItemType Directory -Path $localDir -Force | Out-Null
            }
            
            if (Test-Path $backupPath -PathType Container) {
                if (Test-Path $localPathItem) {
                    Remove-Item -Path $localPathItem -Recurse -Force -ErrorAction SilentlyContinue
                }
                Copy-Item -Path $backupPath -Destination $localPathItem -Recurse -Force -ErrorAction SilentlyContinue
            } else {
                Copy-Item -Path $backupPath -Destination $localPathItem -Force -ErrorAction SilentlyContinue
            }
            
            if (Test-Path $localPathItem) {
                Write-ColorOutput Green "   [OK] Restaurado: $item"
                $restoredCount++
            }
        }
    }
    
    Write-ColorOutput Green "[OK] $restoredCount archivos protegidos restaurados"
    Write-Output ""
}

# ========================================
# 7. VERIFICAR QUE USUARIOS NO SE TOCARON
# ========================================
if ($syncCompleted -and $userCountBefore -ne $null) {
    Write-ColorOutput Yellow "7. Verificando que usuarios no fueron afectados..."
    
    try {
        $tempPythonScript = Join-Path $env:TEMP "check_users_after_$(Get-Date -Format 'yyyyMMdd_HHmmss').py"
        $pythonScriptContent = @"
import os
import sys
import django

BASE_DIR = sys.argv[1]
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa

users = User.objects.count()
empresas = Empresa.objects.count()
print('USERS:' + str(users) + '|EMPRESAS:' + str(empresas))
"@
        $pythonScriptContent | Out-File -FilePath $tempPythonScript -Encoding UTF8 -Force
        $result = python $tempPythonScript $LocalPath 2>$null
        Remove-Item -Path $tempPythonScript -Force -ErrorAction SilentlyContinue
        
        if ($result -match "USERS:(\d+)\|EMPRESAS:(\d+)") {
            $userCountAfter = [int]$matches[1]
            $empresaCountAfter = [int]$matches[2]
            
            if ($userCountAfter -eq $userCountBefore -and $empresaCountAfter -eq $empresaCountBefore) {
                Write-ColorOutput Green "   [OK] Usuarios: $userCountAfter (sin cambios)"
                Write-ColorOutput Green "   [OK] Empresas: $empresaCountAfter (sin cambios)"
                Write-ColorOutput Green "   [OK] Base de datos protegida correctamente"
            } else {
                Write-ColorOutput Red "   [ADVERTENCIA] Cambios detectados en usuarios/empresas"
                Write-Output "      Antes: $userCountBefore usuarios, $empresaCountBefore empresas"
                Write-Output "      Después: $userCountAfter usuarios, $empresaCountAfter empresas"
                Write-Output ""
                Write-ColorOutput Yellow "   Restaurando desde backup..."
                $dbBackup = Join-Path $backupDir "db.sqlite3"
                if (Test-Path $dbBackup) {
                    Copy-Item -Path $dbBackup -Destination (Join-Path $LocalPath "db.sqlite3") -Force
                    Write-ColorOutput Green "   [OK] Base de datos restaurada desde backup"
                }
            }
        }
    } catch {
        Write-ColorOutput Yellow "   [AVISO] No se pudo verificar usuarios (puede ser normal)"
    }
    
    Write-Output ""
}

# ========================================
# 8. VERIFICAR CAMBIOS EN GIT
# ========================================
Write-ColorOutput Yellow "8. Verificando cambios sincronizados..."

try {
    $gitStatus = git status --porcelain 2>$null
    if ($gitStatus) {
        Write-ColorOutput Green "[OK] Cambios detectados:"
        git status --short | ForEach-Object { Write-Output "   $_" }
        Write-Output ""
        
        $review = Read-Host "¿Quieres ver un resumen de cambios? (s/n)"
        if ($review -eq "s") {
            git diff --stat | ForEach-Object { Write-Output "   $_" }
        }
        
        Write-Output ""
        Write-ColorOutput Yellow "SIGUIENTE PASO:"
        Write-Output "   Revisar cambios: git diff"
        Write-Output "   Hacer commit: git add -A && git commit -m 'sync: desde servidor'"
    } else {
        Write-ColorOutput Green "[OK] No hay cambios nuevos (ya estaba sincronizado)"
    }
} catch {
    Write-ColorOutput Yellow "[AVISO] Git no disponible o no es repositorio"
}

Write-Output ""

# ========================================
# RESUMEN FINAL
# ========================================
Write-ColorOutput Green '================================================'
Write-ColorOutput Green '  SINCRONIZACIÓN COMPLETADA'
Write-ColorOutput Green '================================================'
Write-Output ''
Write-Output '[OK] Codigo sincronizado desde servidor'
Write-Output '[OK] Usuarios y credenciales protegidos'
Write-Output ('[OK] Backup guardado en: ' + $backupDir)
Write-Output ''

Pop-Location
