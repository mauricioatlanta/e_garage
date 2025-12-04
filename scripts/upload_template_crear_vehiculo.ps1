# ========================================
# SCRIPT: Subir Template crear.html al Servidor
# ========================================
# USO: .\scripts\upload_template_crear_vehiculo.ps1
# DESCRIPCIÓN: Sube el template crear.html al servidor PythonAnywhere

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
Write-ColorOutput Cyan '  SUBIR TEMPLATE crear.html AL SERVIDOR'
Write-ColorOutput Cyan '================================================'
Write-Output ""

# ========================================
# 1. VERIFICAR ARCHIVO LOCAL
# ========================================
Write-ColorOutput Yellow "1. Verificando archivo local..."

$localFile = Join-Path $LocalPath "templates\cl\es\vehiculos\crear.html"

if (-not (Test-Path $localFile)) {
    Write-ColorOutput Red "ERROR: No se encontró el archivo local:"
    Write-Output "   $localFile"
    exit 1
}

$fileInfo = Get-Item $localFile
Write-ColorOutput Green "[OK] Archivo local encontrado:"
Write-Output "   Ruta: $localFile"
Write-Output "   Tamaño: $($fileInfo.Length) bytes"
Write-Output "   Última modificación: $($fileInfo.LastWriteTime)"
Write-Output ""

# ========================================
# 2. PREPARAR RUTA REMOTA
# ========================================
Write-ColorOutput Yellow "2. Preparando ruta remota..."

$remoteFile = "$ServerPath/templates/cl/es/vehiculos/crear.html"
Write-Output "   Archivo remoto: $remoteFile"
Write-Output ""

# ========================================
# 3. OPCIONES DE SUBIDA
# ========================================
Write-ColorOutput Cyan "3. Selecciona método de subida:"
Write-Output ""
Write-Output "   [1] SCP (PowerShell - Requiere contraseña)"
Write-Output "   [2] FileZilla (Manual - Recomendado)"
Write-Output "   [3] Mostrar comando SCP para copiar"
Write-Output "   [4] Cancelar"
Write-Output ""

$choice = Read-Host "   Tu elección (1-4)"

switch ($choice) {
    "1" {
        Write-Output ""
        Write-ColorOutput Yellow "Subiendo archivo con SCP..."
        Write-Output ""
        Write-ColorOutput Yellow "NOTA: Se te pedirá la contraseña del servidor"
        Write-Output ""
        
        $scpCmd = "scp `"$localFile`" ${ServerUser}@${ServerHost}:${remoteFile}"
        Write-ColorOutput Gray "Comando: $scpCmd"
        Write-Output ""
        
        try {
            & scp $localFile "${ServerUser}@${ServerHost}:${remoteFile}"
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput Green "[OK] Archivo subido correctamente"
            } else {
                Write-ColorOutput Red "[ERROR] Error al subir el archivo"
                exit 1
            }
        } catch {
            Write-ColorOutput Red "[ERROR] Error al ejecutar SCP: $_"
            Write-Output ""
            Write-ColorOutput Yellow "Sugerencia: Usa FileZilla (opción 2) o verifica que tienes SCP instalado"
            exit 1
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
        Write-Output "3. Panel REMOTO → Navegar a:"
        Write-Output "   $ServerPath/templates/cl/es/vehiculos/"
        Write-Output ""
        Write-Output "4. Panel LOCAL → Navegar a:"
        Write-Output "   $LocalPath\templates\cl\es\vehiculos\"
        Write-Output ""
        Write-Output "5. Arrastra 'crear.html' del panel LOCAL al REMOTO"
        Write-Output ""
        Write-Output "6. Cuando pregunte por sobrescribir: 'Sí'"
        Write-Output ""
        Write-Output "7. Verifica permisos (click derecho → Permisos → 644)"
        Write-Output ""
        Write-ColorOutput Yellow "   Presiona Enter cuando hayas terminado..."
        Read-Host
    }
    "3" {
        Write-Output ""
        Write-ColorOutput Yellow "COMANDO SCP (copia y pega en PowerShell):"
        Write-Output ""
        Write-ColorOutput White "scp `"$localFile`" ${ServerUser}@${ServerHost}:${remoteFile}"
        Write-Output ""
        Write-ColorOutput Yellow "O desde WSL/Git Bash:"
        Write-Output ""
        Write-ColorOutput White "scp '$($localFile.Replace('\', '/'))' ${ServerUser}@${ServerHost}:${remoteFile}"
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
# 4. VERIFICACIÓN
# ========================================
Write-Output ""
Write-ColorOutput Yellow "4. Verificación..."
Write-Output ""
Write-ColorOutput Green "✅ Archivo local verificado:"
Write-Output "   Tamaño: $($fileInfo.Length) bytes"
Write-Output "   Fecha: $($fileInfo.LastWriteTime)"
Write-Output ""
Write-ColorOutput Yellow "📋 SIGUIENTE PASO:"
Write-Output "   1. Abre: https://www.egarage.cl/cl/es/vehiculos/crear/"
Write-Output "   2. Presiona Ctrl+F5 para forzar recarga"
Write-Output "   3. Verifica que los cambios se reflejen"
Write-Output ""

# ========================================
# RESUMEN FINAL
# ========================================
Write-ColorOutput Green '================================================'
Write-ColorOutput Green '  PROCESO COMPLETADO'
Write-ColorOutput Green '================================================'
Write-Output ''
Write-Output '✅ Archivo preparado para subir'
Write-Output '📤 Sigue las instrucciones arriba para completar la subida'
Write-Output '🌐 Verifica en: https://www.egarage.cl/cl/es/vehiculos/crear/'
Write-Output ''




