# Script para actualizar el template de cabecera en el servidor
# Uso: .\actualizar_template_cabecera.ps1

Write-Host "🚀 Actualizando template de cabecera en el servidor..." -ForegroundColor Cyan
Write-Host ""

# Archivos a actualizar
$archivos = @(
    "templates/us/en/dashboard/centro_operaciones_espacial.html",
    "templates/taller/us/en/dashboard/centro_operaciones_espacial.html",
    "taller/views_extra/dashboard_empresa.py",
    "taller/urls_extra/usa.py"
)

# Verificar que los archivos existen
Write-Host "📋 Verificando archivos..." -ForegroundColor Yellow
foreach ($archivo in $archivos) {
    if (Test-Path $archivo) {
        Write-Host "  ✅ $archivo" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $archivo NO ENCONTRADO" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Opción 1: Git (Recomendado)
Write-Host "¿Cómo deseas actualizar?" -ForegroundColor Cyan
Write-Host "  1. Git (commit + push) - Recomendado"
Write-Host "  2. SCP (copiar archivos directamente)"
Write-Host ""
$opcion = Read-Host "Selecciona opción (1 o 2)"

if ($opcion -eq "1") {
    # Opción Git
    Write-Host ""
    Write-Host "📤 Actualizando vía Git..." -ForegroundColor Yellow
    
    # Agregar archivos
    foreach ($archivo in $archivos) {
        git add $archivo
    }
    
    # Commit
    $commitMsg = Read-Host "Mensaje de commit (o Enter para usar mensaje por defecto)"
    if ([string]::IsNullOrWhiteSpace($commitMsg)) {
        $commitMsg = "fix: unificar cabecera de centro-operaciones con logo y lema correctos"
    }
    
    git commit -m $commitMsg
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Commit exitoso" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No se pudo hacer commit (puede que no haya cambios)" -ForegroundColor Yellow
    }
    
    # Push
    $currentBranch = git branch --show-current
    Write-Host ""
    $push = Read-Host "¿Deseas hacer push a GitHub? (s/n)"
    if ($push -eq "s" -or $push -eq "S") {
        git push origin $currentBranch
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Push exitoso" -ForegroundColor Green
            Write-Host ""
            Write-Host "📋 Próximos pasos en el servidor:" -ForegroundColor Cyan
            Write-Host "  1. Conectarse: ssh atlantareciclajes@ssh.pythonanywhere.com" -ForegroundColor White
            Write-Host "  2. Ejecutar:" -ForegroundColor White
            Write-Host "     cd /home/atlantareciclajes/apps/egarage/current" -ForegroundColor Gray
            Write-Host "     source ~/.virtualenvs/venv_egarage310/bin/activate" -ForegroundColor Gray
            Write-Host "     git pull origin main" -ForegroundColor Gray
            Write-Host "     python manage.py collectstatic --noinput" -ForegroundColor Gray
            Write-Host "     touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor Gray
        } else {
            Write-Host "❌ Error en el push" -ForegroundColor Red
            exit 1
        }
    }
    
} elseif ($opcion -eq "2") {
    # Opción SCP
    Write-Host ""
    Write-Host "📤 Copiando archivos vía SCP..." -ForegroundColor Yellow
    
    $servidor = "atlantareciclajes@ssh.pythonanywhere.com"
    $destinoBase = "/home/atlantareciclajes/apps/egarage/current"
    
    foreach ($archivo in $archivos) {
        $destino = "$destinoBase/$archivo"
        Write-Host "  Copiando $archivo..." -ForegroundColor Yellow
        scp $archivo "$servidor`:$destino"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ $archivo copiado" -ForegroundColor Green
        } else {
            Write-Host "    ❌ Error copiando $archivo" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "📋 Próximos pasos en el servidor:" -ForegroundColor Cyan
    Write-Host "  1. Conectarse: ssh $servidor" -ForegroundColor White
    Write-Host "  2. Ejecutar:" -ForegroundColor White
    Write-Host "     cd $destinoBase" -ForegroundColor Gray
    Write-Host "     source ~/.virtualenvs/venv_egarage310/bin/activate" -ForegroundColor Gray
    Write-Host "     python manage.py collectstatic --noinput" -ForegroundColor Gray
    Write-Host "     touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py" -ForegroundColor Gray
    
} else {
    Write-Host "❌ Opción inválida" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Proceso completado" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 Verificación:" -ForegroundColor Cyan
Write-Host "  Después de actualizar, verificar:" -ForegroundColor White
Write-Host "  - https://www.egarage.cl/us/es/centro-operaciones/" -ForegroundColor Gray
Write-Host "  - La cabecera debe mostrar logo, nombre y lema correctos" -ForegroundColor Gray

