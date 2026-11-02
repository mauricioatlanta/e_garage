# ============================================
# Script: Commit, Push y Pull en Servidor
# eGarage - Diciembre 2024
# Versión PowerShell para Windows
# ============================================

Write-Host "========================================" -ForegroundColor Green
Write-Host "🚀 Commit, Push y Pull - eGarage" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# ============================================
# PARTE 1: COMMIT Y PUSH (LOCAL)
# ============================================

Write-Host "📦 Paso 1: Verificando estado de Git..." -ForegroundColor Yellow
git status --short

Write-Host ""
$continuar = Read-Host "¿Deseas continuar con commit y push? (s/n)"

if ($continuar -ne "s" -and $continuar -ne "S") {
    Write-Host "❌ Operación cancelada" -ForegroundColor Red
    exit 1
}

# Verificar si hay cambios
$changes = git status --porcelain
if ([string]::IsNullOrWhiteSpace($changes)) {
    Write-Host "⚠️  No hay cambios para commitear" -ForegroundColor Yellow
} else {
    Write-Host "📝 Agregando archivos modificados..." -ForegroundColor Yellow
    git add -u
    
    Write-Host ""
    $agregarNuevos = Read-Host "¿Agregar también archivos nuevos? (s/n)"
    if ($agregarNuevos -eq "s" -or $agregarNuevos -eq "S") {
        git add .
    }
    
    Write-Host ""
    $commitMessage = Read-Host "Mensaje del commit"
    
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Actualización: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }
    
    Write-Host "💾 Haciendo commit..." -ForegroundColor Yellow
    git commit -m $commitMessage
}

# Verificar si hay commits sin push
$commitsAhead = git log origin/main..HEAD 2>$null
if ($commitsAhead) {
    Write-Host "📤 Haciendo push..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Push exitoso" -ForegroundColor Green
    } else {
        Write-Host "❌ Error en push" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ℹ️  No hay commits nuevos para pushear" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Commit y Push completados" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# ============================================
# PARTE 2: INSTRUCCIONES PARA EL SERVIDOR
# ============================================

Write-Host "📋 Instrucciones para actualizar el servidor:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Conectarse al servidor:" -ForegroundColor White
Write-Host "   ssh atlantareciclajes@ssh.pythonanywhere.com" -ForegroundColor Green
Write-Host ""
Write-Host "2. Ejecutar estos comandos en el servidor:" -ForegroundColor White
Write-Host ""
Write-Host "cd ~/egarage && \" -ForegroundColor Green
Write-Host "git pull origin main && \" -ForegroundColor Green
Write-Host "pip3.10 install --user -r requirements.txt && \" -ForegroundColor Green
Write-Host "python3.10 manage.py migrate && \" -ForegroundColor Green
Write-Host "python3.10 manage.py collectstatic --noinput && \" -ForegroundColor Green
Write-Host "touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor Green
Write-Host ""
Write-Host "3. Verificar que funciona:" -ForegroundColor White
Write-Host "   curl -I https://www.egarage.cl/" -ForegroundColor Green
Write-Host ""

# Guardar comandos en archivo
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$serverScript = "actualizar_servidor_$timestamp.sh"

$scriptContent = @"
#!/bin/bash
# Script para ejecutar en el servidor
# Generado automáticamente

set -e

echo "🚀 Actualizando servidor eGarage..."

# Ir al directorio del proyecto
cd ~/egarage || cd /home/atlantareciclajes/apps/egarage/current

# Pull
echo "📥 Haciendo pull..."
git pull origin main

# Dependencias
echo "📦 Instalando dependencias..."
pip3.10 install --user -r requirements.txt

# Migraciones
echo "🗄️  Ejecutando migraciones..."
python3.10 manage.py migrate

# Estáticos
echo "📁 Recopilando archivos estáticos..."
python3.10 manage.py collectstatic --noinput

# Reiniciar
echo "🔄 Reiniciando aplicación..."
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

echo "✅ Actualización completada!"
echo ""
echo "Verificar:"
echo "curl -I https://www.egarage.cl/"
"@

$scriptContent | Out-File -FilePath $serverScript -Encoding UTF8

Write-Host "📄 Script guardado en: $serverScript" -ForegroundColor Green
Write-Host "💡 Puedes copiar este archivo al servidor y ejecutarlo" -ForegroundColor Yellow
Write-Host ""

