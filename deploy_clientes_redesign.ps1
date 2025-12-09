# 🚀 Script de Despliegue - Rediseño de Clientes
# Ejecutar desde: E:\projecto\e_garage

param(
    [switch]$Local,
    [switch]$Server,
    [switch]$Both
)

$ErrorActionPreference = "Stop"

# Colores para output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

# Banner
Write-Host "`n" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🎨 DEPLOY - REDISEÑO FUTURISTA DE PÁGINA DE CLIENTES 🎨   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n"

# Verificar directorio
if (!(Test-Path ".\manage.py")) {
    Write-Error "❌ No estás en el directorio correcto. Ejecuta desde: E:\projecto\e_garage"
    exit 1
}

Write-Success "✅ Directorio correcto verificado"

# Archivo a desplegar
$archivo = ".\templates\taller\common\clientes\lista_clientes.html"

if (!(Test-Path $archivo)) {
    Write-Error "❌ Archivo no encontrado: $archivo"
    exit 1
}

Write-Success "✅ Archivo encontrado: $archivo"

# ========================================
# PASO 1: BACKUP
# ========================================
Write-Info "`n📦 PASO 1: Creando backup..."

$backupDir = ".\backups\clientes_redesign_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item $archivo "$backupDir\lista_clientes_backup.html" -Force

Write-Success "✅ Backup creado en: $backupDir"

# ========================================
# PASO 2: VERIFICAR CAMBIOS
# ========================================
Write-Info "`n🔍 PASO 2: Verificando cambios..."

# Verificar que el archivo tenga las nuevas clases CSS
$contenido = Get-Content $archivo -Raw

$clasesRequeridas = @(
    "client-card-futuristic",
    "btn-futuristic",
    "btn-futuristic-icon",
    "btn-futuristic-text",
    "client-card-info"
)

$todasPresentes = $true
foreach ($clase in $clasesRequeridas) {
    if ($contenido -match $clase) {
        Write-Success "  ✅ Clase encontrada: $clase"
    } else {
        Write-Error "  ❌ Clase NO encontrada: $clase"
        $todasPresentes = $false
    }
}

if (!$todasPresentes) {
    Write-Error "`n❌ El archivo no tiene todos los cambios necesarios. Verifica el archivo."
    exit 1
}

Write-Success "✅ Todas las clases CSS están presentes"

# ========================================
# PASO 3: PRUEBA LOCAL (Opcional)
# ========================================
if ($Local -or $Both) {
    Write-Info "`n🖥️  PASO 3: Preparando prueba local..."
    
    Write-Info "Verificando servidor de desarrollo..."
    
    $pythonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*runserver*" }
    
    if ($pythonProcess) {
        Write-Success "✅ Servidor de desarrollo está corriendo"
        Write-Info "   Abre en navegador: http://localhost:8000/us/clientes/"
        Write-Info "                       http://localhost:8000/cl/clientes/"
    } else {
        Write-Warning "⚠️  Servidor de desarrollo NO está corriendo"
        Write-Info "Iniciando servidor de desarrollo..."
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python manage.py runserver"
        Start-Sleep -Seconds 3
        
        Write-Success "✅ Servidor iniciado en nueva ventana"
        Write-Info "   Abre en navegador: http://localhost:8000/us/clientes/"
    }
    
    Write-Info "`n📱 Prueba en diferentes resoluciones:"
    Write-Info "   1. Abre Chrome DevTools (F12)"
    Write-Info "   2. Activa modo responsive (Ctrl+Shift+M)"
    Write-Info "   3. Prueba: iPhone SE, iPhone 12 Pro, iPad, Desktop"
    
    $continuar = Read-Host "`n¿Has probado localmente y todo funciona? (s/n)"
    if ($continuar -ne "s" -and $continuar -ne "S") {
        Write-Warning "⚠️  Despliegue cancelado por el usuario"
        exit 0
    }
}

# ========================================
# PASO 4: GIT COMMIT Y PUSH
# ========================================
if ($Server -or $Both) {
    Write-Info "`n🌐 PASO 4: Desplegando al servidor..."
    
    # Verificar estado de Git
    Write-Info "Verificando estado de Git..."
    
    $gitStatus = git status --porcelain $archivo 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "⚠️  Git no está configurado o no estás en un repositorio"
        Write-Info "Saltando despliegue automático con Git"
        
        Write-Info "`n📋 PASOS MANUALES PARA SUBIR AL SERVIDOR:"
        Write-Info "   1. Conecta al servidor por SSH o FTP"
        Write-Info "   2. Sube el archivo: $archivo"
        Write-Info "   3. Ruta en servidor: /ruta/al/proyecto/templates/taller/common/clientes/"
        Write-Info "   4. Reinicia el servidor: sudo systemctl restart gunicorn"
        
        exit 0
    }
    
    if ($gitStatus) {
        Write-Info "Cambios detectados en Git:"
        Write-Host $gitStatus -ForegroundColor Yellow
        
        Write-Info "`nAgregando archivo al stage..."
        git add $archivo
        
        Write-Info "Creando commit..."
        $commitMsg = "🎨 Rediseño futurista de página de clientes - Mobile-first con botones cinematográficos"
        git commit -m $commitMsg
        
        Write-Success "✅ Commit creado: $commitMsg"
        
        Write-Info "`nSubiendo cambios al repositorio..."
        $pushResponse = Read-Host "¿Hacer push a origin main? (s/n)"
        
        if ($pushResponse -eq "s" -or $pushResponse -eq "S") {
            git push origin main
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "✅ Cambios subidos exitosamente a GitHub/GitLab"
            } else {
                Write-Error "❌ Error al hacer push. Verifica tu conexión y permisos."
                exit 1
            }
        } else {
            Write-Warning "⚠️  Push cancelado. Recuerda hacer 'git push origin main' manualmente"
        }
    } else {
        Write-Info "ℹ️  No hay cambios en Git (ya está commiteado)"
    }
    
    # ========================================
    # PASO 5: INSTRUCCIONES PARA SERVIDOR
    # ========================================
    Write-Info "`n🖥️  PASO 5: Acciones en el servidor..."
    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║           COMANDOS PARA EJECUTAR EN EL SERVIDOR              ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host "`n"
    
    Write-Host "1. Conectarse al servidor:" -ForegroundColor Cyan
    Write-Host "   ssh usuario@tuservidor.com`n" -ForegroundColor White
    
    Write-Host "2. Ir al directorio del proyecto:" -ForegroundColor Cyan
    Write-Host "   cd /ruta/al/proyecto" -ForegroundColor White
    Write-Host "   cd /home/usuario/e_garage  # Ejemplo`n" -ForegroundColor Gray
    
    Write-Host "3. Hacer pull de los cambios:" -ForegroundColor Cyan
    Write-Host "   git pull origin main`n" -ForegroundColor White
    
    Write-Host "4. Activar virtualenv (si aplica):" -ForegroundColor Cyan
    Write-Host "   source venv/bin/activate`n" -ForegroundColor White
    
    Write-Host "5. Recolectar archivos estáticos:" -ForegroundColor Cyan
    Write-Host "   python manage.py collectstatic --noinput`n" -ForegroundColor White
    
    Write-Host "6. Reiniciar el servidor:" -ForegroundColor Cyan
    Write-Host "   sudo systemctl restart gunicorn" -ForegroundColor White
    Write-Host "   # O si usas otro: sudo systemctl restart apache2`n" -ForegroundColor Gray
    
    Write-Host "7. Verificar el estado:" -ForegroundColor Cyan
    Write-Host "   sudo systemctl status gunicorn`n" -ForegroundColor White
    
    # Copiar comandos al portapapeles
    $comandosServidor = @"
ssh usuario@tuservidor.com
cd /ruta/al/proyecto
git pull origin main
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
"@
    
    Set-Clipboard -Value $comandosServidor
    Write-Success "✅ Comandos copiados al portapapeles"
}

# ========================================
# PASO 6: VERIFICACIÓN FINAL
# ========================================
Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                     VERIFICACIÓN FINAL                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`n"

Write-Info "📱 Verifica en el navegador:"
Write-Info "   • Desktop: https://www.egarage.cl/us/clientes/"
Write-Info "   • Mobile: Abre en tu teléfono y verifica los botones"
Write-Info ""
Write-Info "✅ Checklist:"
Write-Info "   [ ] Cards tienen bordes cyan con glow"
Write-Info "   [ ] Botones muestran iconos y texto en móvil"
Write-Info "   [ ] Hover muestra efectos de neón"
Write-Info "   [ ] Animaciones funcionan suavemente"
Write-Info "   [ ] Texto es legible en móvil"
Write-Info ""

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              ✅ DESPLIEGUE COMPLETADO EXITOSAMENTE ✅           ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Info "`n📄 Backup guardado en: $backupDir"
Write-Info "🔄 Para rollback: Copy-Item '$backupDir\lista_clientes_backup.html' '$archivo' -Force"

Write-Host "`n🎉 ¡Rediseño completado! Tu página de clientes ahora es futurista y mobile-first! 🚀`n" -ForegroundColor Magenta

# Mostrar ayuda si no se pasaron parámetros
if (!$Local -and !$Server -and !$Both) {
    Write-Host "`nUso del script:" -ForegroundColor Yellow
    Write-Host "  .\deploy_clientes_redesign.ps1 -Local    # Solo prueba local" -ForegroundColor White
    Write-Host "  .\deploy_clientes_redesign.ps1 -Server   # Solo despliegue servidor" -ForegroundColor White
    Write-Host "  .\deploy_clientes_redesign.ps1 -Both     # Prueba local + servidor`n" -ForegroundColor White
}








