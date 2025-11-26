# Script para actualizar cambios al servidor
# Uso: .\actualizar_servidor.ps1

Write-Host "Actualizando cambios al servidor..." -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "Error: No estas en la raiz del proyecto Django" -ForegroundColor Red
    exit 1
}

# Verificar estado de Git
Write-Host "Verificando estado de Git..." -ForegroundColor Yellow
$gitStatus = git status --porcelain

if ($null -ne $gitStatus -and $gitStatus.Length -gt 0) {
    Write-Host "Cambios detectados:" -ForegroundColor Yellow
    git status --short
    
    $response = Read-Host "Deseas hacer commit de estos cambios? (s/n)"
    if ($response -eq "s" -or $response -eq "S") {
        $commitMsg = Read-Host "Mensaje de commit (o Enter para usar mensaje por defecto)"
        if ([string]::IsNullOrWhiteSpace($commitMsg)) {
            $commitMsg = "fix: actualizacion de templates y estilos"
        }
        
        git add .
        git commit -m $commitMsg
        Write-Host "Cambios commiteados" -ForegroundColor Green
    }
    else {
        Write-Host "Saltando commit. Asegurate de hacer commit manualmente." -ForegroundColor Yellow
    }
}
else {
    Write-Host "No hay cambios pendientes" -ForegroundColor Green
}

# Verificar rama actual
$currentBranch = git branch --show-current
Write-Host ""
Write-Host "Rama actual: $currentBranch" -ForegroundColor Cyan

# Push a Git
Write-Host ""
$response = Read-Host "Deseas hacer push a GitHub? (s/n)"
if ($response -eq "s" -or $response -eq "S") {
    Write-Host "Pusheando a GitHub..." -ForegroundColor Yellow
    git push origin $currentBranch
    
    if ($?) {
        Write-Host "Push exitoso" -ForegroundColor Green
        Write-Host ""
        Write-Host "Proximos pasos:" -ForegroundColor Cyan
        Write-Host "   1. Si usas Render.com: El deploy se ejecutara automaticamente (2-5 min)" -ForegroundColor White
        Write-Host "   2. Si usas PythonAnywhere:" -ForegroundColor White
        Write-Host "      - Ve a tu dashboard" -ForegroundColor White
        Write-Host "      - Abre la consola Bash" -ForegroundColor White
        Write-Host "      - Ejecuta: git pull origin $currentBranch" -ForegroundColor White
        Write-Host "      - Ejecuta: python manage.py collectstatic --noinput" -ForegroundColor White
        Write-Host "      - Haz clic en 'Reload' en el dashboard" -ForegroundColor White
        Write-Host "   3. Si usas servidor propio:" -ForegroundColor White
        Write-Host "      - Conectate por SSH y ejecuta git pull" -ForegroundColor White
        Write-Host "      - Reinicia el servicio" -ForegroundColor White
    }
    else {
        Write-Host "Error en el push. Verifica tu conexion y permisos." -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "Saltando push. Asegurate de hacer push manualmente." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Proceso completado" -ForegroundColor Green
