# Script para actualizar el servidor con el fix de ocultar cuadro usuario en móvil + Fix CSRF
# Fecha: 2025-01-27
# VERSIÓN: 2.1 - Código mejorado con MutationObserver + Fix CSRF token helper

Write-Host "🚀 ACTUALIZANDO SERVIDOR - OCULTAR CUADRO USUARIO EN MÓVIL" -ForegroundColor Cyan
Write-Host ""

$archivo = "templates/us/en/dashboard/centro_operaciones_espacial.html"
$servidor = "atlantareciclajes@ssh.pythonanywhere.com"
$destino = "/home/atlantareciclajes/apps/egarage/current/templates/us/en/dashboard/"

# Verificar que el archivo existe
if (-not (Test-Path $archivo)) {
    Write-Host "❌ Error: No se encuentra el archivo $archivo" -ForegroundColor Red
    exit 1
}

Write-Host "📤 Copiando archivo al servidor..." -ForegroundColor Yellow
Write-Host "   Archivo: $archivo" -ForegroundColor Gray
Write-Host "   Destino: $servidor`:$destino" -ForegroundColor Gray
Write-Host ""

# Copiar archivo vía SCP
scp $archivo "$servidor`:$destino"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Archivo copiado exitosamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Próximos pasos en el servidor:" -ForegroundColor Cyan
    Write-Host "   1. Conectarse: ssh $servidor" -ForegroundColor White
    Write-Host "   2. Ejecutar:" -ForegroundColor White
    Write-Host "      cd /home/atlantareciclajes/apps/egarage/current" -ForegroundColor Gray
    Write-Host "      touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   O desde el Dashboard de PythonAnywhere:" -ForegroundColor White
    Write-Host "   - Ir a Web → Click en 'Reload'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔍 Verificación:" -ForegroundColor Cyan
    Write-Host "   - Abrir: https://www.egarage.cl/us/centro-operaciones/" -ForegroundColor Gray
    Write-Host "   - Verificar en móvil que NO aparece el cuadro con información del usuario" -ForegroundColor Gray
    Write-Host "   - Verificar en PC que el cuadro SÍ aparece (si existe)" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ Error al copiar el archivo" -ForegroundColor Red
    Write-Host "   Verifica:" -ForegroundColor Yellow
    Write-Host "   - Que tienes acceso SSH configurado" -ForegroundColor Gray
    Write-Host "   - Que la ruta del servidor es correcta" -ForegroundColor Gray
    Write-Host "   - Que tienes permisos para escribir en el servidor" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "✅ Proceso completado" -ForegroundColor Green

