# Script para actualizar iconos PWA de eGarage
# Ejecutar desde la raiz del proyecto

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ACTUALIZAR ICONOS PWA FUTURISTAS - eGARAGE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "[ERROR] No se encuentra manage.py" -ForegroundColor Red
    Write-Host "Asegurate de ejecutar este script desde la raiz del proyecto" -ForegroundColor Yellow
    exit 1
}

Write-Host "Paso 1: Verificando archivos de iconos..." -ForegroundColor Yellow
$iconFiles = @(
    "static\images\egarage_default_logo.svg",
    "static\images\egarage_icon_192x192.png",
    "static\images\egarage_icon_512x512.png",
    "static\images\egarage_default_logo.png"
)

$allFilesExist = $true
foreach ($file in $iconFiles) {
    if (Test-Path $file) {
        Write-Host "   [OK] $file" -ForegroundColor Green
    }
    else {
        Write-Host "   [FALTA] $file" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "[AVISO] Algunos archivos no existen. Generando iconos..." -ForegroundColor Yellow
    Write-Host ""
    
    # Intentar generar los iconos
    python generar_iconos_pwa.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Error al generar iconos" -ForegroundColor Red
        Write-Host "Instala las dependencias: pip install Pillow" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Paso 2: Recolectando archivos estaticos..." -ForegroundColor Yellow
python manage.py collectstatic --no-input

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Error al recolectar archivos estaticos" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[EXITO] Iconos actualizados correctamente!" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PROXIMOS PASOS PARA PROBAR EN EL CELULAR" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Si tienes la PWA instalada:" -ForegroundColor White
Write-Host "   - Desinstala la aplicacion actual del celular" -ForegroundColor Gray
Write-Host "   - Android: Configuracion -> Apps -> eGarage -> Desinstalar" -ForegroundColor Gray
Write-Host "   - iOS: Manten presionado el icono -> Eliminar" -ForegroundColor Gray
Write-Host ""
Write-Host "2. En el navegador del celular:" -ForegroundColor White
Write-Host "   - Abre Chrome o Safari" -ForegroundColor Gray
Write-Host "   - Ve a tu sitio web" -ForegroundColor Gray
Write-Host "   - Limpia el cache del navegador" -ForegroundColor Gray
Write-Host "   - Recarga la pagina (Ctrl+F5 o forzar recarga)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Reinstala la PWA:" -ForegroundColor White
Write-Host "   - Chrome: Menu -> 'Agregar a pantalla de inicio'" -ForegroundColor Gray
Write-Host "   - Safari: Compartir -> 'Agregar a pantalla de inicio'" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CARACTERISTICAS DEL NUEVO ICONO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "* Diseno futurista con engranaje tecnologico" -ForegroundColor Magenta
Write-Host "* Efectos de brillo neon (cyan y morado)" -ForegroundColor Magenta
Write-Host "* Vehiculo estilizado en el centro" -ForegroundColor Magenta
Write-Host "* Patron de circuitos de fondo" -ForegroundColor Magenta
Write-Host "* Elementos UI tipo HUD en las esquinas" -ForegroundColor Magenta
Write-Host "* Tipografia moderna 'eGARAGE'" -ForegroundColor Magenta
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para mas informacion, consulta: ACTUALIZAR_ICONOS_PWA.md" -ForegroundColor Yellow
Write-Host ""
