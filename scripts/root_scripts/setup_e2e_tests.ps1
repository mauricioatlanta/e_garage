# 🚀 Script de configuración para tests E2E con Playwright (Windows)
# Ejecuta: .\setup_e2e_tests.ps1

Write-Host "🔧 Configurando tests E2E con Playwright..." -ForegroundColor Cyan

# Verificar si Node.js está instalado
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js encontrado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js no está instalado. Por favor instala Node.js primero." -ForegroundColor Red
    Write-Host "   Descarga desde: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Verificar si npm está instalado
try {
    $npmVersion = npm --version
    Write-Host "✅ npm encontrado: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm no está instalado. Por favor instala npm primero." -ForegroundColor Red
    exit 1
}

# Instalar dependencias
Write-Host "📦 Instalando dependencias de Playwright..." -ForegroundColor Yellow
npm install

# Instalar navegadores de Playwright
Write-Host "🌐 Instalando navegadores de Playwright..." -ForegroundColor Yellow
npx playwright install

Write-Host "✅ Configuración completada!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Comandos disponibles:" -ForegroundColor Cyan
Write-Host "   npm test              - Ejecutar todos los tests" -ForegroundColor White
Write-Host "   npm run test:ui       - Ejecutar con interfaz visual" -ForegroundColor White
Write-Host "   npm run test:headed   - Ejecutar viendo el navegador" -ForegroundColor White
Write-Host "   npm run test:debug    - Ejecutar en modo debug" -ForegroundColor White
Write-Host ""
Write-Host "📋 Asegúrate de que:" -ForegroundColor Cyan
Write-Host "   - El servidor Django esté corriendo en http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   - Tengas un usuario autenticado" -ForegroundColor White
Write-Host "   - Existan servicios con 'oil' en el nombre para el test" -ForegroundColor White
Write-Host ""
Write-Host "🚀 ¡Listo para ejecutar tests E2E!" -ForegroundColor Green
