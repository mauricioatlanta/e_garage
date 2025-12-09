# Script de Verificación de Mejoras - Template Cliente
# Fecha: Diciembre 4, 2025

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🎨 VERIFICACIÓN DE MEJORAS - TEMPLATE CLIENTE FUTURISTA   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar archivos modificados
Write-Host "📁 Verificando archivos modificados..." -ForegroundColor Yellow
Write-Host ""

$archivos = @(
    "templates\base.html",
    "templates\taller\common\clientes\cliente_form.html",
    "templates\taller\common\clientes\cliente_list.html",
    "templates\taller\common\clientes\lista_clientes.html",
    "templates\us\es\clientes\lista_clientes.html",
    "templates\us\en\clientes\lista_clientes.html",
    "templates\cl\es\clientes\lista_clientes.html",
    "templates\br\es\clientes\lista_clientes.html",
    "templates\mx\es\clientes\lista_clientes.html",
    "templates\ve\es\clientes\lista_clientes.html",
    "templates\pe\es\clientes\lista_clientes.html",
    "templates\co\es\clientes\lista_clientes.html",
    "templates\ec\es\clientes\lista_clientes.html",
    "templates\us\en\documentos\base_documento.html"
)

$encontrados = 0
$noEncontrados = 0

foreach ($archivo in $archivos) {
    if (Test-Path $archivo) {
        Write-Host "  ✅ $archivo" -ForegroundColor Green
        $encontrados++
    } else {
        Write-Host "  ❌ $archivo (NO ENCONTRADO)" -ForegroundColor Red
        $noEncontrados++
    }
}

Write-Host ""
Write-Host "📊 Resumen:" -ForegroundColor Cyan
Write-Host "  ✅ Archivos encontrados: $encontrados" -ForegroundColor Green
Write-Host "  ❌ Archivos no encontrados: $noEncontrados" -ForegroundColor Red
Write-Host ""

# Verificar fuente Orbitron en base.html
Write-Host "🔤 Verificando fuente Orbitron..." -ForegroundColor Yellow
$baseHtml = Get-Content "templates\base.html" -Raw
if ($baseHtml -match "Orbitron") {
    Write-Host "  ✅ Fuente Orbitron cargada correctamente" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Fuente Orbitron NO encontrada" -ForegroundColor Red
}
Write-Host ""

# Verificar que no hay indicadores de debug
Write-Host "🔍 Verificando eliminación de indicadores de debug..." -ForegroundColor Yellow
$debugEncontrados = 0

$archivosClientes = Get-ChildItem -Path "templates" -Recurse -Filter "*lista_clientes.html" | Select-Object -ExpandProperty FullName

foreach ($archivo in $archivosClientes) {
    $contenido = Get-Content $archivo -Raw
    if ($contenido -match "CRUZ|position: fixed.*z-index: 99999") {
        Write-Host "  ⚠️  Indicador de debug encontrado en: $archivo" -ForegroundColor Red
        $debugEncontrados++
    }
}

if ($debugEncontrados -eq 0) {
    Write-Host "  ✅ Todos los indicadores de debug han sido eliminados" -ForegroundColor Green
} else {
    Write-Host "  ❌ Se encontraron $debugEncontrados indicadores de debug" -ForegroundColor Red
}
Write-Host ""

# Verificar grid de 2 columnas en cliente_form
Write-Host "📐 Verificando grid de 2 columnas en formulario..." -ForegroundColor Yellow
$clienteForm = Get-Content "templates\taller\common\clientes\cliente_form.html" -Raw
if ($clienteForm -match "md:grid-cols-2") {
    Write-Host "  ✅ Grid de 2 columnas implementado" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Grid de 2 columnas NO encontrado" -ForegroundColor Red
}
Write-Host ""

# Verificar animaciones CSS
Write-Host "✨ Verificando animaciones CSS..." -ForegroundColor Yellow
$animaciones = @("title-glow", "glow-pulse", "electric-border", "shine-sweep")
$animacionesEncontradas = 0

foreach ($animacion in $animaciones) {
    if ($baseHtml -match $animacion) {
        Write-Host "  ✅ Animación '$animacion' encontrada" -ForegroundColor Green
        $animacionesEncontradas++
    } else {
        Write-Host "  ⚠️  Animación '$animacion' NO encontrada" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "  Total: $animacionesEncontradas de $($animaciones.Count) animaciones" -ForegroundColor Cyan
Write-Host ""

# Verificar partículas animadas
Write-Host "🌟 Verificando fondo con partículas..." -ForegroundColor Yellow
if ($clienteForm -match "partículas animadas") {
    Write-Host "  ✅ Fondo con partículas implementado" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Fondo con partículas NO encontrado" -ForegroundColor Red
}
Write-Host ""

# Verificar iconos en campos
Write-Host "🎨 Verificando iconos en campos del formulario..." -ForegroundColor Yellow
$iconos = @("👤", "👥", "📧", "📱", "🆔", "📍")
$iconosEncontrados = 0

foreach ($icono in $iconos) {
    if ($clienteForm -match [regex]::Escape($icono)) {
        $iconosEncontrados++
    }
}

if ($iconosEncontrados -ge 4) {
    Write-Host "  ✅ Iconos implementados en formulario ($iconosEncontrados iconos)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Solo se encontraron $iconosEncontrados iconos" -ForegroundColor Red
}
Write-Host ""

# Resumen final
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    RESUMEN FINAL                            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($encontrados -eq $archivos.Count -and $debugEncontrados -eq 0 -and $animacionesEncontradas -ge 3) {
    Write-Host "🎉 ¡TODAS LAS MEJORAS IMPLEMENTADAS EXITOSAMENTE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
    Write-Host "  1. Iniciar servidor: python manage.py runserver" -ForegroundColor White
    Write-Host "  2. Abrir navegador: http://localhost:8000/us/clientes/editar/7/" -ForegroundColor White
    Write-Host "  3. Verificar visualmente el nuevo diseño" -ForegroundColor White
    Write-Host "  4. Probar responsive (resize ventana del navegador)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  Algunas verificaciones fallaron. Revisar detalles arriba." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "📚 Documentación generada:" -ForegroundColor Cyan
Write-Host "  - MEJORAS_TEMPLATE_CLIENTE_VISUAL.md" -ForegroundColor White
Write-Host "  - RESUMEN_FINAL_MEJORAS.md" -ForegroundColor White
Write-Host ""

Write-Host "Presiona cualquier tecla para salir..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")







