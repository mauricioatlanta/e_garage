# Script para subir iconos PWA al servidor
# Reemplaza SERVIDOR_IP con tu IP o dominio del servidor

$SERVIDOR = "TU_SERVIDOR_IP_O_DOMINIO"
$USUARIO = "atlantareciclajes"
$RUTA_SERVIDOR = "/home/atlantareciclajes/apps/egarage/current"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SUBIR ICONOS PWA AL SERVIDOR" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que SCP está disponible
try {
    $scpTest = Get-Command scp -ErrorAction Stop
    Write-Host "[OK] SCP encontrado" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] SCP no está disponible" -ForegroundColor Red
    Write-Host "Instala OpenSSH Client desde: Configuracion -> Apps -> Caracteristicas opcionales" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Servidor: $SERVIDOR" -ForegroundColor Yellow
Write-Host "Usuario: $USUARIO" -ForegroundColor Yellow
Write-Host ""

# Lista de archivos a subir
$archivos = @(
    @{Local="static\images\egarage_icon_192x192.png"; Remoto="$RUTA_SERVIDOR/static/images/"},
    @{Local="static\images\egarage_icon_512x512.png"; Remoto="$RUTA_SERVIDOR/static/images/"},
    @{Local="static\images\egarage_icon_1024x1024.png"; Remoto="$RUTA_SERVIDOR/static/images/"},
    @{Local="static\images\egarage_default_logo.svg"; Remoto="$RUTA_SERVIDOR/static/images/"},
    @{Local="static\images\egarage_default_logo.png"; Remoto="$RUTA_SERVIDOR/static/images/"},
    @{Local="static\manifest.json"; Remoto="$RUTA_SERVIDOR/static/"},
    @{Local="static\service-worker.js"; Remoto="$RUTA_SERVIDOR/static/"},
    @{Local="templates\base.html"; Remoto="$RUTA_SERVIDOR/templates/"},
    @{Local="templates\taller\common\base.html"; Remoto="$RUTA_SERVIDOR/templates/taller/common/"}
)

Write-Host "Archivos a subir:" -ForegroundColor Yellow
$archivos | ForEach-Object {
    if (Test-Path $_.Local) {
        Write-Host "  [OK] $($_.Local)" -ForegroundColor Green
    } else {
        Write-Host "  [FALTA] $($_.Local)" -ForegroundColor Red
    }
}

Write-Host ""
$respuesta = Read-Host "¿Continuar con la subida? (s/n)"

if ($respuesta -ne "s" -and $respuesta -ne "S") {
    Write-Host "Cancelado por el usuario" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Subiendo archivos..." -ForegroundColor Cyan
Write-Host ""

foreach ($archivo in $archivos) {
    if (Test-Path $archivo.Local) {
        Write-Host "Subiendo: $($archivo.Local)..." -ForegroundColor Yellow
        
        $destino = "${USUARIO}@${SERVIDOR}:$($archivo.Remoto)"
        
        try {
            scp $archivo.Local $destino
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] Subido correctamente" -ForegroundColor Green
            } else {
                Write-Host "  [ERROR] Falló la subida" -ForegroundColor Red
            }
        } catch {
            Write-Host "  [ERROR] $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Write-Host ""
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PROXIMOS PASOS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Conectate al servidor y ejecuta:" -ForegroundColor Yellow
Write-Host ""
Write-Host "cd ~/apps/egarage/current" -ForegroundColor White
Write-Host "python manage.py collectstatic --no-input" -ForegroundColor White
Write-Host "# Reinicia tu aplicacion desde el panel de control" -ForegroundColor White
Write-Host ""
Write-Host "Luego en el celular:" -ForegroundColor Yellow
Write-Host "1. chrome://serviceworker-internals/ -> Unregister" -ForegroundColor White
Write-Host "2. Cerrar Chrome completamente" -ForegroundColor White
Write-Host "3. Reabrir y visitar tu sitio" -ForegroundColor White
Write-Host "4. Menu -> 'Agregar a pantalla de inicio'" -ForegroundColor White
Write-Host ""


