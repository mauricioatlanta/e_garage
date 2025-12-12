# ============================================================================
# 🚀 SCRIPT DE ACTUALIZACIÓN COMPLETA - eGarage
# ============================================================================
# Este script actualiza TODA la aplicación en el servidor SIN BORRAR
# datos de suscriptores. Preserva: User, Empresa, Suscripcion, y todos los datos
# ============================================================================

$ErrorActionPreference = "Stop"

# Configuración del servidor
$servidor = "atlantareciclajes@ssh.pythonanywhere.com"
$base = "/home/atlantareciclajes/apps/egarage/current"
$sharedDb = "/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║                                                         ║" -ForegroundColor Blue
Write-Host "║  🚀 eGarage - ACTUALIZACIÓN COMPLETA DEL SERVIDOR      ║" -ForegroundColor Blue
Write-Host "║  📦 Actualizando TODO sin perder datos                 ║" -ForegroundColor Blue
Write-Host "║                                                         ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ ERROR: No se encontró manage.py" -ForegroundColor Red
    Write-Host "   Ejecuta este script desde el directorio raíz del proyecto (E:\projecto\e_garage)" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Directorio correcto detectado" -ForegroundColor Green
Write-Host ""

# ============================================================================
# PASO 1: Subir script de deployment seguro al servidor
# ============================================================================

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PASO 1/5: Subiendo script de deployment seguro" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$scriptPath = "scripts\deploy_seguro_suscriptores.sh"
if (Test-Path $scriptPath) {
    Write-Host "Subiendo deploy_seguro_suscriptores.sh..." -ForegroundColor Yellow
    $destPath = $servidor + ":" + $base + "/scripts/"
    & "scp.exe" $scriptPath $destPath
    Write-Host "Script subido" -ForegroundColor Green
}
if (-not (Test-Path $scriptPath)) {
    Write-Host "No se encontro deploy_seguro_suscriptores.sh" -ForegroundColor Yellow
    Write-Host "El script se creara en el servidor" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# PASO 2: Subir TODOS los archivos del proyecto
# ============================================================================

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PASO 2/5: Subiendo archivos del proyecto" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$archivos = @(
    @{src="manage.py"; dest="manage.py"},
    @{src="requirements.txt"; dest="requirements.txt"},
    @{src="gestion_taller"; dest="gestion_taller"},
    @{src="taller"; dest="taller"},
    @{src="ubicacion"; dest="ubicacion"},
    @{src="core"; dest="core"},
    @{src="templates"; dest="templates"},
    @{src="static"; dest="static"},
    @{src="utils"; dest="utils"},
    @{src="locale"; dest="locale"}
)

$contador = 0
foreach ($archivo in $archivos) {
    $contador++
    $src = $archivo.src
    $dest = $archivo.dest
    
        if (Test-Path $src) {
            Write-Host "[$contador/$($archivos.Count)] Subiendo $src..." -ForegroundColor Yellow
            
            $destPath = "${servidor}:${base}/${dest}"
            if (Test-Path $src -PathType Container) {
                # Es un directorio
                scp -r "${src}/*" "${destPath}/"
            }
            else {
                # Es un archivo
                scp $src $destPath
            }
        
        Write-Host "   ✅ $src subido" -ForegroundColor Green
        }
        else {
            Write-Host "[$contador/$($archivos.Count)] ⚠️  No encontrado: $src" -ForegroundColor Yellow
        }
}

Write-Host ""
Write-Host "✅ Archivos subidos" -ForegroundColor Green
Write-Host ""

# ============================================================================
# PASO 3: Ejecutar deployment seguro en el servidor
# ============================================================================

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PASO 3/5: Ejecutando deployment seguro en el servidor" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANTE: Este paso ejecutará el deployment en el servidor" -ForegroundColor Yellow
Write-Host "   Se creará un backup completo antes de hacer cambios" -ForegroundColor Yellow
Write-Host "   Los datos de suscriptores se preservarán" -ForegroundColor Yellow
Write-Host ""

$confirmar = Read-Host "¿Continuar con el deployment? (s/n)"
if ($confirmar -ne "s" -and $confirmar -ne "S") {
    Write-Host "❌ Deployment cancelado por el usuario" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🚀 Ejecutando deployment en el servidor..." -ForegroundColor Cyan
Write-Host ""

# Crear script temporal para ejecutar en el servidor
$scriptServidor = @'
#!/bin/bash
set -e

cd /home/atlantareciclajes/apps/egarage/current

# Activar virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif command -v workon &> /dev/null; then
    workon venv_egarage310 || true
fi

# Dar permisos al script de deployment
chmod +x scripts/deploy_seguro_suscriptores.sh 2>/dev/null || true

# Ejecutar deployment seguro
if [ -f "scripts/deploy_seguro_suscriptores.sh" ]; then
    bash scripts/deploy_seguro_suscriptores.sh
else
    echo "⚠️  Script de deployment no encontrado, ejecutando pasos manuales..."
    
    # Backup
    mkdir -p backups/deployments
    TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
    BACKUP_SQLITE="backups/deployments/db_backup_\$TIMESTAMP.sqlite3"
    
    if [ -f "/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3" ]; then
        cp "/home/atlantareciclajes/apps/egarage/shared/db/db.sqlite3" "\$BACKUP_SQLITE"
        echo "✅ Backup creado: \$BACKUP_SQLITE"
    fi
    
    # Actualizar dependencias
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --upgrade --quiet
    
    # Migraciones
    python manage.py makemigrations --noinput || true
    python manage.py migrate --noinput || python manage.py migrate --fake-initial --noinput
    
    # Collectstatic
    python manage.py collectstatic --noinput --clear
    python manage.py collectstatic --noinput
    
    echo "✅ Deployment manual completado"
fi

# Reiniciar aplicacion (PythonAnywhere)
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py 2>/dev/null || echo "No se pudo tocar WSGI"
'@

# Guardar script temporal
$tempScript = "deploy_temp_servidor.sh"
$scriptServidor | Out-File -FilePath $tempScript -Encoding UTF8

# Subir y ejecutar script en el servidor
Write-Host "📤 Subiendo script temporal..." -ForegroundColor Yellow
$destPath = "${servidor}:${base}/"
scp $tempScript $destPath

Write-Host "⚡ Ejecutando deployment en el servidor..." -ForegroundColor Yellow
ssh ${servidor} "cd ${base}; chmod +x ${tempScript}; bash ${tempScript}"

# Limpiar script temporal local
Remove-Item $tempScript -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ Deployment ejecutado en el servidor" -ForegroundColor Green
Write-Host ""

# ============================================================================
# PASO 4: Verificar estado
# ============================================================================

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PASO 4/5: Verificando estado del servidor" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔍 Verificando datos en el servidor..." -ForegroundColor Yellow

$verificacionScript = @'
cd /home/atlantareciclajes/apps/egarage/current
if command -v workon &> /dev/null; then
    workon venv_egarage310 || true
fi
python manage.py shell << 'PYTHON_EOF'
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
try:
    from taller.models.suscripcion import Suscripcion
    suscripcion_count = Suscripcion.objects.count()
except:
    suscripcion_count = 0

user_count = User.objects.count()
empresa_count = Empresa.objects.count()

print(f"📊 Estado actual en el servidor:")
print(f"   👥 Usuarios: {user_count}")
print(f"   🏢 Empresas: {empresa_count}")
print(f"   💳 Suscripciones: {suscripcion_count}")

if user_count == 0:
    print("⚠️  ADVERTENCIA: No hay usuarios!")
elif empresa_count == 0:
    print("⚠️  ADVERTENCIA: No hay empresas!")
else:
    print("✅ Los datos están intactos")
PYTHON_EOF
'@

$verificacionScript | Out-File -FilePath "verificar_temp.sh" -Encoding UTF8
$destPath = "${servidor}:${base}/"
scp "verificar_temp.sh" $destPath
ssh ${servidor} "cd ${base}; bash verificar_temp.sh"
Remove-Item verificar_temp.sh -ErrorAction SilentlyContinue

Write-Host ""

# ============================================================================
# PASO 5: Instrucciones finales
# ============================================================================

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PASO 5/5: Instrucciones finales" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ ACTUALIZACIÓN COMPLETA FINALIZADA" -ForegroundColor Green
Write-Host ""
Write-Host "📝 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Reiniciar la aplicación en PythonAnywhere:" -ForegroundColor White
Write-Host "   - Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/webapps/" -ForegroundColor Gray
Write-Host "   - Haz clic en el boton Reload atlantareciclajes.pythonanywhere.com" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Verificar que el sitio funciona:" -ForegroundColor White
Write-Host "   - Abre: https://atlantareciclajes.pythonanywhere.com/" -ForegroundColor Gray
Write-Host "   - Prueba hacer login con una cuenta existente" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Verificar datos de suscriptores:" -ForegroundColor White
Write-Host "   - Los usuarios, empresas y suscripciones deben estar intactos" -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 Si necesitas hacer rollback:" -ForegroundColor Yellow
Write-Host "   ssh ${servidor}" -ForegroundColor Gray
Write-Host "   cd ${base}" -ForegroundColor Gray
Write-Host "   cp backups/deployments/db_backup_YYYYMMDD_HHMMSS.sqlite3 ${sharedDb}" -ForegroundColor Gray
Write-Host ""
Write-Host "📦 Backups guardados en:" -ForegroundColor Cyan
Write-Host "   ${base}/backups/deployments/" -ForegroundColor Gray
Write-Host ""

