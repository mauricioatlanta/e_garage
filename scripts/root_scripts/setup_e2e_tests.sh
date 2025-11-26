#!/bin/bash

# 🚀 Script de configuración para tests E2E con Playwright
# Ejecuta: bash setup_e2e_tests.sh

echo "🔧 Configurando tests E2E con Playwright..."

# Verificar si Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado. Por favor instala Node.js primero."
    echo "   Descarga desde: https://nodejs.org/"
    exit 1
fi

# Verificar si npm está instalado
if ! command -v npm &> /dev/null; then
    echo "❌ npm no está instalado. Por favor instala npm primero."
    exit 1
fi

echo "✅ Node.js y npm encontrados"

# Instalar dependencias
echo "📦 Instalando dependencias de Playwright..."
npm install

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores de Playwright..."
npx playwright install

echo "✅ Configuración completada!"
echo ""
echo "🎯 Comandos disponibles:"
echo "   npm test              - Ejecutar todos los tests"
echo "   npm run test:ui       - Ejecutar con interfaz visual"
echo "   npm run test:headed   - Ejecutar viendo el navegador"
echo "   npm run test:debug    - Ejecutar en modo debug"
echo ""
echo "📋 Asegúrate de que:"
echo "   - El servidor Django esté corriendo en http://127.0.0.1:8000"
echo "   - Tengas un usuario autenticado"
echo "   - Existan servicios con 'oil' en el nombre para el test"
echo ""
echo "🚀 ¡Listo para ejecutar tests E2E!"
