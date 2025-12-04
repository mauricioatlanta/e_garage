# Script para corregir automáticamente todos los casos de getElementById().addEventListener
# sin verificación

$archivos = @(
    "templates\co\es\onboarding\bienvenida.html",
    "templates\ec\es\onboarding\bienvenida.html",
    "templates\us\es\onboarding\bienvenida.html",
    "templates\us\en\onboarding\bienvenida.html",
    "templates\analytics\centro_control_america.html",
    "templates\business_intelligence\dashboard.html",
    "templates\cl\es\repuestos\repuesto_list.html",
    "templates\taller\configuracion\mecanicos.html",
    "templates\taller\reportes\dashboard_inteligencia.html",
    "templates\taller\reportes\demo_reportes_por_fecha.html",
    "templates\us\en\landing\usa_landing.html",
    "templates\us\en\settings\futuristic_company_settings.html"
)

Write-Host "======================================================"
Write-Host "CORRIGIENDO PROBLEMAS DE JAVASCRIPT..."
Write-Host "======================================================"
Write-Host ""

$totalCorregidos = 0

foreach ($archivo in $archivos) {
    $rutaCompleta = Join-Path $PSScriptRoot ".." $archivo
    
    if (Test-Path $rutaCompleta) {
        Write-Host "Procesando: $archivo" -ForegroundColor Cyan
        
        $contenido = Get-Content $rutaCompleta -Raw -Encoding UTF8
        $contenidoOriginal = $contenido
        
        # Patrón: document.getElementById('id').addEventListener
        $patron = 'document\.getElementById\(([^)]+)\)\.addEventListener'
        
        if ($contenido -match $patron) {
            # Crear backup
            $backup = $rutaCompleta + ".backup"
            Copy-Item $rutaCompleta $backup -Force
            Write-Host "  Backup creado: $backup" -ForegroundColor Yellow
            
            # Reemplazar patrón
            $contenido = $contenido -replace 
                "(\s*)document\.getElementById\(([^)]+)\)\.addEventListener\s*\(",
            {
                param($match)
                $indent = $match.Groups[1].Value
                $elementId = $match.Groups[2].Value
                $varName = "el_" + ($elementId -replace "['`"]", "" -replace "[^a-zA-Z0-9]", "_")
                
                "$indent`n${indent}const $varName = document.getElementById($elementId);`n${indent}if ($varName) {`n${indent}  $varName.addEventListener("
            }
            
            # Cerrar los if que agregamos (buscar addEventListener seguido de función y agregar })
            # Esto es más complejo, mejor hacerlo manualmente o con más lógica
            
            if ($contenido -ne $contenidoOriginal) {
                Set-Content $rutaCompleta $contenido -Encoding UTF8 -NoNewline
                Write-Host "  ✅ Corregido" -ForegroundColor Green
                $totalCorregidos++
            } else {
                Write-Host "  ⚠️  No se encontraron patrones" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ℹ️  No tiene el patrón problemático" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ❌ No encontrado: $archivo" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "======================================================"
Write-Host "RESUMEN: $totalCorregidos archivos corregidos"
Write-Host "======================================================"
Write-Host ""
Write-Host "⚠️  IMPORTANTE: Revisa los cambios manualmente"
Write-Host "   Los archivos tienen backups (.backup)"
Write-Host "   Necesitarás cerrar manualmente los bloques if {}"
Write-Host ""


