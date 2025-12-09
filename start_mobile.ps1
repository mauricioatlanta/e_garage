# Script para iniciar eGarage con acceso movil
# Obtiene la IP automaticamente y configura el servidor

Write-Host "Iniciando eGarage para acceso movil..." -ForegroundColor Cyan
Write-Host ""

# Obtener IP local
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*" } | Select-Object -First 1).IPAddress

if (-not $ipAddress) {
    Write-Host "ERROR: No se pudo detectar la IP local automaticamente" -ForegroundColor Red
    Write-Host "Por favor, ejecuta 'ipconfig' y busca tu Direccion IPv4" -ForegroundColor Yellow
    pause
    exit
}

Write-Host "Tu IP local es: $ipAddress" -ForegroundColor Green
Write-Host "Accede desde tu celular: http://$ipAddress:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANTE: Asegurate de que tu celular este en la misma red Wi-Fi" -ForegroundColor Yellow
Write-Host ""

# Verificar si el puerto esta en uso
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "ADVERTENCIA: El puerto 8000 esta en uso" -ForegroundColor Yellow
    $response = Read-Host "Deseas continuar? (S/N)"
    if ($response -ne "S" -and $response -ne "s") {
        Write-Host "Operacion cancelada" -ForegroundColor Red
        pause
        exit
    }
}

# Verificar y configurar firewall
Write-Host "Verificando regla de firewall..." -ForegroundColor Cyan
$firewallRule = Get-NetFirewallRule -DisplayName "Django Development Server" -ErrorAction SilentlyContinue

if (-not $firewallRule) {
    Write-Host "Creando regla de firewall..." -ForegroundColor Yellow
    try {
        New-NetFirewallRule -DisplayName "Django Development Server" `
            -Direction Inbound `
            -LocalPort 8000 `
            -Protocol TCP `
            -Action Allow `
            -ErrorAction Stop | Out-Null
        Write-Host "OK: Regla de firewall creada" -ForegroundColor Green
    } catch {
        Write-Host "ADVERTENCIA: No se pudo crear la regla de firewall automaticamente" -ForegroundColor Yellow
        Write-Host "   Puede que necesites ejecutar PowerShell como Administrador" -ForegroundColor Yellow
        Write-Host "   O configurar el firewall manualmente para permitir el puerto 8000" -ForegroundColor Yellow
    }
} else {
    Write-Host "OK: Regla de firewall ya existe" -ForegroundColor Green
}

Write-Host ""

# Activar entorno virtual si existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path "venv\Scripts\activate.bat") {
    Write-Host "Entorno virtual encontrado (usando .bat)" -ForegroundColor Green
    & "venv\Scripts\activate.bat"
} else {
    Write-Host "No se encontro entorno virtual, continuando sin el..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Iniciando servidor Django..." -ForegroundColor Cyan
Write-Host "   Presiona Ctrl+C para detener el servidor" -ForegroundColor Gray
Write-Host ""

# Iniciar servidor
python manage.py runserver 0.0.0.0:8000

