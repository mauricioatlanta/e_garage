# 🚀 Script para Subir Archivo de Clientes al Servidor PythonAnywhere
# Ejecutar desde: E:\projecto\e_garage

param(
    [string]$Password = ""
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🎨 SUBIR REDISEÑO DE CLIENTES A PYTHONANYWHERE 🎨          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Configuración
$localFile = ".\templates\taller\common\clientes\lista_clientes.html"
$remoteUser = "atlantareciclajes"
$remoteHost = "ssh.pythonanywhere.com"
$remotePath = "/home/atlantareciclajes/e_garage/templates/taller/common/clientes/lista_clientes.html"
$wsgiFile = "/var/www/atlantareciclajes_pythonanywhere_com_wsgi.py"

# Verificar que el archivo existe
if (!(Test-Path $localFile)) {
    Write-Host "❌ Error: No se encuentra el archivo local: $localFile" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Archivo local encontrado: $localFile`n" -ForegroundColor Green

# Verificar que tiene el rediseño
$contenido = Get-Content $localFile -Raw
if ($contenido -match "client-card-futuristic" -and $contenido -match "btn-futuristic") {
    Write-Host "✅ El archivo tiene el rediseño futurista`n" -ForegroundColor Green
} else {
    Write-Host "❌ ADVERTENCIA: El archivo NO parece tener el rediseño completo" -ForegroundColor Yellow
    $continuar = Read-Host "¿Continuar de todos modos? (s/n)"
    if ($continuar -ne "s") { exit 0 }
}

# Mostrar opciones
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "OPCIONES DE SUBIDA:`n" -ForegroundColor Yellow
Write-Host "1. 🌐 Copiar contenido (pegarlo manualmente en web)" -ForegroundColor White
Write-Host "2. 📤 Usar SCP (requiere SSH configurado)" -ForegroundColor White
Write-Host "3. 📋 Generar script de actualización`n" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════`n" -ForegroundColor Yellow

$opcion = Read-Host "Selecciona opción (1/2/3)"

switch ($opcion) {
    "1" {
        Write-Host "`n📋 OPCIÓN 1: Copiar y Pegar Manual`n" -ForegroundColor Cyan
        
        # Copiar contenido al portapapeles
        $contenido | Set-Clipboard
        
        Write-Host "✅ Contenido copiado al portapapeles!" -ForegroundColor Green
        Write-Host "`nPASOS A SEGUIR:`n" -ForegroundColor Yellow
        Write-Host "1. Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/files/" -ForegroundColor White
        Write-Host "2. Navega a: home/atlantareciclajes/e_garage/templates/taller/common/clientes/" -ForegroundColor White
        Write-Host "3. Click en: lista_clientes.html" -ForegroundColor White
        Write-Host "4. Selecciona TODO el contenido (Ctrl+A)" -ForegroundColor White
        Write-Host "5. Pega el nuevo contenido (Ctrl+V)" -ForegroundColor White
        Write-Host "6. Click en 'Save' (arriba a la derecha)" -ForegroundColor White
        Write-Host "7. Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/webapps/" -ForegroundColor White
        Write-Host "8. Click en el botón verde 'Reload'" -ForegroundColor White
        Write-Host "`n✅ ¡Archivo listo para pegar!`n" -ForegroundColor Green
    }
    
    "2" {
        Write-Host "`n📤 OPCIÓN 2: Usar SCP`n" -ForegroundColor Cyan
        
        if ($Password -eq "") {
            $Password = Read-Host "Ingresa tu contraseña de PythonAnywhere" -AsSecureString
            $PasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password))
        } else {
            $PasswordPlain = $Password
        }
        
        Write-Host "Subiendo archivo con SCP..." -ForegroundColor Yellow
        
        # Usar pscp si está disponible (PuTTY)
        if (Get-Command pscp -ErrorAction SilentlyContinue) {
            pscp -pw $PasswordPlain $localFile "${remoteUser}@${remoteHost}:${remotePath}"
        }
        # O usar scp nativo de Windows
        elseif (Get-Command scp -ErrorAction SilentlyContinue) {
            scp $localFile "${remoteUser}@${remoteHost}:${remotePath}"
        }
        else {
            Write-Host "❌ SCP no está instalado. Usa la opción 1 o 3." -ForegroundColor Red
            exit 1
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Archivo subido exitosamente!" -ForegroundColor Green
            
            # Recargar aplicación
            Write-Host "`nRecargando aplicación..." -ForegroundColor Yellow
            ssh "${remoteUser}@${remoteHost}" "touch $wsgiFile"
            
            Write-Host "✅ Aplicación recargada!" -ForegroundColor Green
        } else {
            Write-Host "❌ Error al subir archivo" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "`n📋 OPCIÓN 3: Generar Script de Actualización`n" -ForegroundColor Cyan
        
        # Crear archivo de actualización
        $updateScript = @"
#!/bin/bash
# Script de actualización para PythonAnywhere
# Generado: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

echo "🚀 Actualizando archivo de clientes..."

cd /home/atlantareciclajes/e_garage

# Backup del archivo actual
cp templates/taller/common/clientes/lista_clientes.html templates/taller/common/clientes/lista_clientes.html.backup_`$(date +%Y%m%d_%H%M%S)

# Actualizar contenido
cat > templates/taller/common/clientes/lista_clientes.html << 'ENDOFFILE'
$contenido
ENDOFFILE

echo "✅ Archivo actualizado"

# Recargar aplicación
touch $wsgiFile

echo "✅ Aplicación recargada"
echo ""
echo "🎉 ¡Actualización completada!"
echo ""
echo "Verifica en: https://atlantareciclajes.pythonanywhere.com/us/clientes/"
"@
        
        $scriptFile = "update_clientes_server.sh"
        $updateScript | Out-File -FilePath $scriptFile -Encoding UTF8 -NoNewline
        
        Write-Host "✅ Script creado: $scriptFile" -ForegroundColor Green
        Write-Host "`nPASOS A SEGUIR:`n" -ForegroundColor Yellow
        Write-Host "1. Sube este archivo al servidor usando FileZilla/WinSCP" -ForegroundColor White
        Write-Host "2. O copia el contenido manualmente" -ForegroundColor White
        Write-Host "3. En el servidor ejecuta:" -ForegroundColor White
        Write-Host "   chmod +x update_clientes_server.sh" -ForegroundColor Cyan
        Write-Host "   ./update_clientes_server.sh`n" -ForegroundColor Cyan
    }
    
    default {
        Write-Host "❌ Opción inválida" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ PROCESO COMPLETADO ✅                     ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

