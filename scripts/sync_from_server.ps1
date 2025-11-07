# ========================================
# SCRIPT: Sincronizar cambios del SERVIDOR -> PC
# ========================================
# USO: .\scripts\sync_from_server.ps1
# IMPORTANTE: Ejecutar ANTES de hacer cualquier deployment nuevo

param(
    [string]$ServerPath = "usuario@egarage.pythonanywhere.com:/home/usuario/apps/egarage/current",
    [string]$LocalPath = "E:\projecto\e_garage"
)

Write-Host "SINCRONIZANDO CAMBIOS DEL SERVIDOR A TU PC" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Yellow
Write-Host ""

# 1. Verificar que Git esta limpio
Write-Host "1. Verificando estado de Git..." -ForegroundColor Cyan
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "Tienes cambios sin commitear en tu PC:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $continue = Read-Host "Quieres hacer STASH de estos cambios antes de continuar? (s/n)"
    if ($continue -eq "s") {
        git stash save "Pre-sync from server $(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
        Write-Host "Cambios guardados en stash" -ForegroundColor Green
    }
}

# 2. Crear branch para los cambios del servidor
$branchName = "server-sync-$(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
Write-Host ""
Write-Host "2. Creando branch: $branchName" -ForegroundColor Cyan
git checkout -b $branchName

# 3. Descargar archivos del servidor usando rsync (o scp)
Write-Host ""
Write-Host "3. Descargando archivos del servidor..." -ForegroundColor Cyan
Write-Host "   Servidor: $ServerPath" -ForegroundColor Gray
Write-Host "   Destino: $LocalPath" -ForegroundColor Gray
Write-Host ""

# Archivos a sincronizar (IMPORTANTE: excluir archivos que no deben sincronizarse)
$rsyncCmd = "rsync -avz --progress --exclude='db.sqlite3' --exclude='media/' --exclude='staticfiles/' --exclude='__pycache__/' --exclude='*.pyc' --exclude='.env' --exclude='*.log' $ServerPath/ $LocalPath/"

Write-Host "COMANDO A EJECUTAR:" -ForegroundColor Yellow
Write-Host $rsyncCmd -ForegroundColor Gray
Write-Host ""
Write-Host "SI NO TIENES RSYNC, usa este comando SCP alternativo:" -ForegroundColor Yellow
Write-Host "scp -r $ServerPath/* $LocalPath/" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Ejecutar sincronizacion? (s/n)"
if ($continue -ne "s") {
    Write-Host "Sincronizacion cancelada" -ForegroundColor Red
    exit 1
}

# Nota: rsync puede no estar disponible en Windows, usar alternativa
Write-Host ""
Write-Host "EJECUTA MANUALMENTE en WSL, Git Bash o PowerShell con rsync:" -ForegroundColor Yellow
Write-Host $rsyncCmd -ForegroundColor White
Write-Host ""
Write-Host "O usa WinSCP/FileZilla para descargar la carpeta completa" -ForegroundColor Yellow

# 4. Ver diferencias
Write-Host ""
Write-Host "4. Revisando cambios descargados..." -ForegroundColor Cyan
$changes = git status --porcelain
if ($changes) {
    Write-Host "Archivos modificados en el servidor:" -ForegroundColor Green
    git status --short
    Write-Host ""
    Write-Host "5. Quieres ver el diff detallado? (s/n)" -ForegroundColor Cyan
    $showDiff = Read-Host
    if ($showDiff -eq "s") {
        git diff
    }
    
    # 5. Commit de los cambios del servidor
    Write-Host ""
    Write-Host "6. Commiteando cambios del servidor..." -ForegroundColor Cyan
    git add -A
    git commit -m "sync: Cambios rescatados del servidor ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
    
    Write-Host ""
    Write-Host "CAMBIOS DEL SERVIDOR GUARDADOS EN BRANCH: $branchName" -ForegroundColor Green
    Write-Host ""
    Write-Host "SIGUIENTE PASO:" -ForegroundColor Yellow
    Write-Host "   1. Revisa los cambios: git log -1 --stat" -ForegroundColor White
    Write-Host "   2. Haz merge a main: git checkout main; git merge $branchName" -ForegroundColor White
    Write-Host "   3. O descarta si no son utiles: git checkout main; git branch -D $branchName" -ForegroundColor White
} else {
    Write-Host "No hay cambios en el servidor (o no se sincronizo)" -ForegroundColor Green
    git checkout main
    git branch -D $branchName
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "SINCRONIZACION COMPLETADA" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
