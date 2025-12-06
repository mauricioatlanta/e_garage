# ========================================
# SCRIPT: Subir Módulo Vehículos Completo al Servidor
# ========================================
# USO: .\scripts\upload_vehiculos_completo.ps1
# DESCRIPCIÓN: Sube todos los archivos necesarios para corregir el módulo de vehículos

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
Write-ColorOutput Cyan '  SUBIR MÓDULO VEHÍCULOS COMPLETO AL SERVIDOR'
Write-ColorOutput Cyan '================================================'
Write-Output ""

# ========================================
# 1. VERIFICAR ARCHIVOS LOCALES
# ========================================
Write-ColorOutput Yellow "1. Verificando archivos locales..."

$archivos = @{
    "views_fbv.py" = "taller\vehiculos\views_fbv.py"
    "formulario_jerarquico.js" = "static\js\formulario_jerarquico.js"
    "crear.html" = "templates\cl\es\vehiculos\crear.html"
}

$archivosOk = $true
foreach ($nombre in $archivos.Keys) {
    $ruta = Join-Path $LocalPath $archivos[$nombre]
    if (-not (Test-Path $ruta)) {
        Write-ColorOutput Red "   [ERROR] No encontrado: $ruta"
        $archivosOk = $false
    } else {
        $info = Get-Item $ruta
        Write-ColorOutput Green "   [OK] $nombre - $($info.Length) bytes - $($info.LastWriteTime)"
    }
}

if (-not $archivosOk) {
    Write-ColorOutput Red "ERROR: Algunos archivos no se encontraron"
    exit 1
}

Write-Output ""

# ========================================
# 2. VERIFICAR CORRECCIÓN EN views_fbv.py
# ========================================
Write-ColorOutput Yellow "2. Verificando corrección en views_fbv.py..."

$viewsFile = Join-Path $LocalPath "taller\vehiculos\views_fbv.py"
$content = Get-Content $viewsFile -Raw

if ($content -match "qs = Modelo\.objects\.filter\(marca_id=marca_id, country=country\)") {
    Write-ColorOutput Green "   [OK] Filtro por país encontrado en ajax_modelos_por_marca_anio"
} elseif ($content -match "def ajax_modelos_por_marca_anio") {
    Write-ColorOutput Red "   [ADVERTENCIA] Función ajax_modelos_por_marca_anio encontrada pero sin filtro por país"
    Write-ColorOutput Yellow "   Verifica que tenga: qs = Modelo.objects.filter(marca_id=marca_id, country=country)"
} else {
    Write-ColorOutput Yellow "   [AVISO] No se pudo verificar la función ajax_modelos_por_marca_anio"
}

Write-Output ""

# ========================================
# 3. OPCIONES DE SUBIDA
# ========================================
Write-ColorOutput Cyan "3. Selecciona método de subida:"
Write-Output ""
Write-Output "   [1] SCP (PowerShell - Sube todos los archivos)"
Write-Output "   [2] FileZilla (Manual - Recomendado para control)"
Write-Output "   [3] Mostrar comandos SCP para copiar"
Write-Output "   [4] Cancelar"
Write-Output ""

$choice = Read-Host "   Tu elección (1-4)"

$archivosSubidos = @()

switch ($choice) {
    "1" {
        Write-Output ""
        Write-ColorOutput Yellow "Subiendo archivos con SCP..."
        Write-Output ""
        Write-ColorOutput Yellow "NOTA: Se te pedirá la contraseña del servidor para cada archivo"
        Write-Output ""
        
        # Subir views_fbv.py
        $localFile = Join-Path $LocalPath "taller\vehiculos\views_fbv.py"
        $remoteFile = "$ServerPath/taller/vehiculos/views_fbv.py"
        Write-ColorOutput Cyan "Subiendo views_fbv.py..."
        try {
            & scp $localFile "${ServerUser}@${ServerHost}:${remoteFile}"
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "   [OK] views_fbv.py subido"
                $archivosSubidos += "views_fbv.py"
            } else {
                Write-ColorOutput Red "   [ERROR] Error al subir views_fbv.py"
            }
        } catch {
            Write-ColorOutput Red "   [ERROR] Error al ejecutar SCP: $_"
        }
        
        # Subir formulario_jerarquico.js
        $localFile = Join-Path $LocalPath "static\js\formulario_jerarquico.js"
        $remoteFile = "$ServerPath/static/js/formulario_jerarquico.js"
        Write-ColorOutput Cyan "Subiendo formulario_jerarquico.js..."
        try {
            & scp $localFile "${ServerUser}@${ServerHost}:${remoteFile}"
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "   [OK] formulario_jerarquico.js subido"
                $archivosSubidos += "formulario_jerarquico.js"
            } else {
                Write-ColorOutput Red "   [ERROR] Error al subir formulario_jerarquico.js"
            }
        } catch {
            Write-ColorOutput Red "   [ERROR] Error al ejecutar SCP: $_"
        }
        
        # Subir crear.html
        $localFile = Join-Path $LocalPath "templates\cl\es\vehiculos\crear.html"
        $remoteFile = "$ServerPath/templates/cl/es/vehiculos/crear.html"
        Write-ColorOutput Cyan "Subiendo crear.html..."
        try {
            & scp $localFile "${ServerUser}@${ServerHost}:${remoteFile}"
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "   [OK] crear.html subido"
                $archivosSubidos += "crear.html"
            } else {
                Write-ColorOutput Red "   [ERROR] Error al subir crear.html"
            }
        } catch {
            Write-ColorOutput Red "   [ERROR] Error al ejecutar SCP: $_"
        }
    }
    "2" {
        Write-Output ""
        Write-ColorOutput Green "════════════════════════════════════════"
        Write-ColorOutput Green "  INSTRUCCIONES PARA FILEZILLA"
        Write-ColorOutput Green "════════════════════════════════════════"
        Write-Output ""
        Write-Output "1. Abre FileZilla"
        Write-Output "2. Conecta a:"
        Write-Output "   Host: $ServerHost"
        Write-Output "   Usuario: $ServerUser"
        Write-Output "   Puerto: 22 (SFTP)"
        Write-Output "   Contraseña: [tu contraseña]"
        Write-Output ""
        Write-ColorOutput Yellow "3. Subir estos archivos:"
        Write-Output ""
        Write-Output "   📄 taller/vehiculos/views_fbv.py"
        Write-Output "      Local: $LocalPath\taller\vehiculos\views_fbv.py"
        Write-Output "      Remoto: $ServerPath/taller/vehiculos/views_fbv.py"
        Write-Output ""
        Write-Output "   📄 static/js/formulario_jerarquico.js"
        Write-Output "      Local: $LocalPath\static\js\formulario_jerarquico.js"
        Write-Output "      Remoto: $ServerPath/static/js/formulario_jerarquico.js"
        Write-Output ""
        Write-Output "   📄 templates/cl/es/vehiculos/crear.html"
        Write-Output "      Local: $LocalPath\templates\cl\es\vehiculos\crear.html"
        Write-Output "      Remoto: $ServerPath/templates/cl/es/vehiculos/crear.html"
        Write-Output ""
        Write-Output "4. Arrastra cada archivo del panel LOCAL al REMOTO"
        Write-Output "5. Cuando pregunte por sobrescribir: 'Sí'"
        Write-Output "6. Verifica permisos (click derecho → Permisos → 644)"
        Write-Output ""
        Write-ColorOutput Yellow "   Presiona Enter cuando hayas terminado..."
        Read-Host
        $archivosSubidos = @("views_fbv.py", "formulario_jerarquico.js", "crear.html")
    }
    "3" {
        Write-Output ""
        Write-ColorOutput Yellow "COMANDOS SCP (copia y pega en PowerShell):"
        Write-Output ""
        Write-ColorOutput White "# 1. Subir views_fbv.py"
        Write-Output "scp `"$LocalPath\taller\vehiculos\views_fbv.py`" ${ServerUser}@${ServerHost}:$ServerPath/taller/vehiculos/views_fbv.py"
        Write-Output ""
        Write-ColorOutput White "# 2. Subir formulario_jerarquico.js"
        Write-Output "scp `"$LocalPath\static\js\formulario_jerarquico.js`" ${ServerUser}@${ServerHost}:$ServerPath/static/js/formulario_jerarquico.js"
        Write-Output ""
        Write-ColorOutput White "# 3. Subir crear.html"
        Write-Output "scp `"$LocalPath\templates\cl\es\vehiculos\crear.html`" ${ServerUser}@${ServerHost}:$ServerPath/templates/cl/es/vehiculos/crear.html"
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
# 4. INSTRUCCIONES POST-SUBIDA
# ========================================
if ($archivosSubidos.Count -gt 0) {
    Write-Output ""
    Write-ColorOutput Green "════════════════════════════════════════"
    Write-ColorOutput Green "  ARCHIVOS SUBIDOS"
    Write-ColorOutput Green "════════════════════════════════════════"
    Write-Output ""
    foreach ($archivo in $archivosSubidos) {
        Write-ColorOutput Green "   ✅ $archivo"
    }
    Write-Output ""
    Write-ColorOutput Yellow "📋 SIGUIENTE PASO - Recargar aplicación:"
    Write-Output ""
    Write-Output "   1. Ve a: https://www.pythonanywhere.com/user/$ServerUser/webapps/"
    Write-Output "   2. Click en 'Reload' en tu aplicación"
    Write-Output ""
    Write-Output "   O desde SSH:"
    Write-Output "   touch /var/www/${ServerUser}_pythonanywhere_com_wsgi.py"
    Write-Output ""
    Write-ColorOutput Yellow "📋 Verificar en el navegador:"
    Write-Output ""
    Write-Output "   1. Abre: https://www.egarage.cl/cl/es/vehiculos/crear/"
    Write-Output "   2. Presiona Ctrl+F5 para forzar recarga"
    Write-Output "   3. Abre la consola (F12) y verifica que no haya errores"
    Write-Output "   4. Selecciona una marca y verifica que se carguen los modelos"
    Write-Output ""
}

# ========================================
# RESUMEN FINAL
# ========================================
Write-ColorOutput Green '================================================'
Write-ColorOutput Green '  PROCESO COMPLETADO'
Write-ColorOutput Green '================================================'
Write-Output ''
Write-Output '✅ Archivos preparados para subir'
Write-Output '📤 Sigue las instrucciones arriba para completar la subida'
Write-Output '🌐 Verifica en: https://www.egarage.cl/cl/es/vehiculos/crear/'
Write-Output ''
Write-ColorOutput Yellow '📖 Para más detalles, consulta:'
Write-Output '   docs/GUIA_ACTUALIZAR_VEHICULOS_COMPLETO.md'
Write-Output ''








