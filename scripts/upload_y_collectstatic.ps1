# ========================================
# SCRIPT: Subir Archivos Y Ejecutar collectstatic
# ========================================
# USO: .\scripts\upload_y_collectstatic.ps1
# DESCRIPCIÓN: Sube archivos y ejecuta collectstatic en el servidor

param(
    [string]$ServerUser = "atlantareciclajes",
    [string]$ServerHost = "atlantareciclajes.pythonanywhere.com",
    [string]$ServerPath = "/home/atlantareciclajes/apps/egarage/current",
    [string]$LocalPath = "E:\projecto\e_garage"
)

$ErrorActionPreference = "Stop"

# Colores
function Write-ColorOutput {
    param(
        [Parameter(Mandatory=$true, Position=0)]
        [string]$ForegroundColor,
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Message
    )
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($Message) {
        Write-Output ($Message -join ' ')
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan '================================================'
Write-ColorOutput Cyan '  SUBIR ARCHIVOS Y EJECUTAR collectstatic'
Write-ColorOutput Cyan '================================================'
Write-Output ""

# ========================================
# 1. ARCHIVOS A SUBIR
# ========================================
Write-ColorOutput Yellow "1. Preparando archivos para subir..."

$archivos = @(
    @{
        Local = "taller\vehiculos\views_fbv.py"
        Remoto = "$ServerPath/taller/vehiculos/views_fbv.py"
        Nombre = "views_fbv.py"
    },
    @{
        Local = "static\js\formulario_jerarquico.js"
        Remoto = "$ServerPath/static/js/formulario_jerarquico.js"
        Nombre = "formulario_jerarquico.js"
    },
    @{
        Local = "templates\cl\es\vehiculos\crear.html"
        Remoto = "$ServerPath/templates/cl/es/vehiculos/crear.html"
        Nombre = "crear.html"
    }
)

$archivosOk = $true
foreach ($archivo in $archivos) {
    $rutaLocal = Join-Path $LocalPath $archivo.Local
    if (-not (Test-Path $rutaLocal)) {
        Write-ColorOutput Red "   [ERROR] No encontrado: $rutaLocal"
        $archivosOk = $false
    } else {
        $info = Get-Item $rutaLocal
        Write-ColorOutput Green "   [OK] $($archivo.Nombre) - $($info.Length) bytes"
    }
}

if (-not $archivosOk) {
    Write-ColorOutput Red "ERROR: Algunos archivos no se encontraron"
    exit 1
}

Write-Output ""

# ========================================
# 2. OPCIONES DE SUBIDA
# ========================================
Write-ColorOutput Cyan "2. Selecciona método:"
Write-Output ""
Write-Output "   [1] SCP + SSH (Sube archivos y ejecuta collectstatic)"
Write-Output "   [2] FileZilla (Manual - luego ejecuta collectstatic manualmente)"
Write-Output "   [3] Solo mostrar comandos"
Write-Output "   [4] Cancelar"
Write-Output ""

$choice = Read-Host "   Tu elección (1-4)"

switch ($choice) {
    "1" {
        Write-Output ""
        Write-ColorOutput Yellow "Subiendo archivos con SCP..."
        Write-Output ""
        Write-ColorOutput Yellow "NOTA: Se te pedirá la contraseña del servidor"
        Write-Output ""
        
        $archivosSubidos = @()
        
        foreach ($archivo in $archivos) {
            $localFile = Join-Path $LocalPath $archivo.Local
            Write-ColorOutput Cyan "Subiendo $($archivo.Nombre)..."
            
            try {
                & scp $localFile "${ServerUser}@${ServerHost}:$($archivo.Remoto)"
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput Green "   [OK] $($archivo.Nombre) subido"
                    $archivosSubidos += $archivo.Nombre
                } else {
                    Write-ColorOutput Red "   [ERROR] Error al subir $($archivo.Nombre)"
                }
            } catch {
                Write-ColorOutput Red "   [ERROR] Error al ejecutar SCP: $_"
            }
        }
        
        Write-Output ""
        Write-ColorOutput Yellow "Ejecutando collectstatic en el servidor..."
        Write-Output ""
        Write-ColorOutput Yellow "NOTA: Se te pedirá la contraseña nuevamente"
        Write-Output ""
        
        # Comando SSH para ejecutar collectstatic
        $collectstaticCmd = "cd $ServerPath && python3.10 manage.py collectstatic --noinput"
        
        Write-ColorOutput Cyan "Comando a ejecutar:"
        Write-ColorOutput White "   $collectstaticCmd"
        Write-Output ""
        
        try {
            & ssh "${ServerUser}@${ServerHost}" $collectstaticCmd
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "   [OK] collectstatic ejecutado correctamente"
            } else {
                Write-ColorOutput Red "   [ERROR] Error al ejecutar collectstatic"
                Write-ColorOutput Yellow "   Ejecuta manualmente: ssh $ServerUser@$ServerHost '$collectstaticCmd'"
            }
        } catch {
            Write-ColorOutput Red "   [ERROR] Error al ejecutar SSH: $_"
            Write-ColorOutput Yellow "   Ejecuta manualmente: ssh $ServerUser@$ServerHost '$collectstaticCmd'"
        }
        
        Write-Output ""
        Write-ColorOutput Yellow "Recargando aplicación..."
        Write-Output ""
        Write-ColorOutput Yellow "Ve a: https://www.pythonanywhere.com/user/$ServerUser/webapps/"
        Write-ColorOutput Yellow "Y haz click en 'Reload' en tu aplicación"
        Write-Output ""
    }
    "2" {
        Write-Output ""
        Write-ColorOutput Green "════════════════════════════════════════"
        Write-ColorOutput Green "  INSTRUCCIONES PARA FILEZILLA"
        Write-ColorOutput Green "════════════════════════════════════════"
        Write-Output ""
        Write-Output "1. Abre FileZilla y conecta a:"
        Write-Output "   Host: $ServerHost"
        Write-Output "   Usuario: $ServerUser"
        Write-Output "   Puerto: 22 (SFTP)"
        Write-Output ""
        Write-ColorOutput Yellow "2. Sube estos archivos:"
        Write-Output ""
        foreach ($archivo in $archivos) {
            Write-Output "   📄 $($archivo.Nombre)"
            Write-Output "      Local: $LocalPath\$($archivo.Local)"
            Write-Output "      Remoto: $($archivo.Remoto)"
            Write-Output ""
        }
        Write-Output "3. Arrastra cada archivo del panel LOCAL al REMOTO"
        Write-Output "4. Cuando pregunte por sobrescribir: 'Sí'"
        Write-Output ""
        Write-ColorOutput Yellow "5. DESPUÉS de subir, ejecuta collectstatic:"
        Write-Output ""
        Write-ColorOutput White "   ssh $ServerUser@$ServerHost"
        Write-ColorOutput White "   cd $ServerPath"
        Write-ColorOutput White "   python3.10 manage.py collectstatic --noinput"
        Write-Output ""
        Write-ColorOutput Yellow "6. Recarga la aplicación en PythonAnywhere"
        Write-Output ""
        Write-ColorOutput Yellow "   Presiona Enter cuando hayas terminado..."
        Read-Host
    }
    "3" {
        Write-Output ""
        Write-ColorOutput Yellow "COMANDOS PARA COPIAR Y PEGAR:"
        Write-Output ""
        Write-ColorOutput White "# 1. Subir archivos"
        foreach ($archivo in $archivos) {
            $localFile = Join-Path $LocalPath $archivo.Local
            Write-Output "scp `"$localFile`" ${ServerUser}@${ServerHost}:$($archivo.Remoto)"
        }
        Write-Output ""
        Write-ColorOutput White "# 2. Ejecutar collectstatic"
        Write-Output "ssh ${ServerUser}@${ServerHost} 'cd $ServerPath && python3.10 manage.py collectstatic --noinput'"
        Write-Output ""
        Write-ColorOutput White "# 3. Recargar aplicación (desde dashboard o):"
        Write-Output "ssh ${ServerUser}@${ServerHost} 'touch /var/www/${ServerUser}_pythonanywhere_com_wsgi.py'"
        Write-Output ""
    }
    "4" {
        Write-ColorOutput Yellow "Operación cancelada"
        exit 0
    }
    default {
        Write-ColorOutput Red "Opción inválida"
        exit 1
    }
}

# ========================================
# RESUMEN FINAL
# ========================================
Write-ColorOutput Green '================================================'
Write-ColorOutput Green '  PROCESO COMPLETADO'
Write-ColorOutput Green '================================================'
Write-Output ''
Write-ColorOutput Yellow '📋 SIGUIENTE PASO:'
Write-Output ''
Write-Output '1. Recargar aplicación en PythonAnywhere:'
Write-Output '   https://www.pythonanywhere.com/user/$ServerUser/webapps/'
Write-Output '   → Click en "Reload"'
Write-Output ''
Write-Output '2. Limpiar caché del navegador:'
Write-Output '   Ctrl+Shift+Delete → Imágenes y archivos en caché → Borrar'
Write-Output ''
Write-Output '3. Verificar en el navegador:'
Write-Output '   https://www.egarage.cl/cl/es/vehiculos/crear/'
Write-Output '   → Presiona Ctrl+F5'
Write-Output '   → Abre consola (F12) y verifica que no hay errores'
Write-Output ''
Write-ColorOutput Yellow '📖 Para más detalles:'
Write-Output '   docs/DIAGNOSTICO_ARCHIVOS_NO_ACTUALIZAN.md'
Write-Output ''




