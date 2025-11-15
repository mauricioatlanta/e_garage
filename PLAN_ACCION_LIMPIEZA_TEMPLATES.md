# PLAN DE ACCIÓN: LIMPIEZA Y ORGANIZACIÓN DE TEMPLATES

**Proyecto:** e_garage
**Fecha de creación:** 27 de Octubre, 2025
**Versión:** 1.0

---

## OBJETIVO

Organizar, limpiar y optimizar la estructura de templates de e_garage para:
- ✅ Eliminar duplicaciones y archivos obsoletos
- ✅ Mejorar mantenibilidad
- ✅ Reducir espacio de almacenamiento (~1,300+ archivos en backups)
- ✅ Establecer políticas de mantenimiento continuo

---

## FASE 1: LIMPIEZA INMEDIATA (1-2 horas)

### ✅ Tarea 1.1: Mover archivo suelto en raíz

**Problema:** `document_payment_status.html` está suelto en raíz del proyecto

**Acción:**
```powershell
# Crear carpeta de componentes si no existe
New-Item -ItemType Directory -Path "templates\components" -Force

# Mover archivo
Move-Item "document_payment_status.html" "templates\components\payment_status_snippet.html"
```

**Verificación:**
- ✅ Archivo movido correctamente
- ✅ No hay referencias rotas (buscar en código)

**Comandos de verificación:**
```powershell
# Buscar referencias al archivo antiguo
Get-ChildItem -Path "taller" -Filter "*.py" -Recurse |
    Select-String "document_payment_status.html"
```

---

### ✅ Tarea 1.2: Verificar y limpiar duplicados en actualizacion_pythonanywhere/

**Archivos a revisar:**
- `actualizacion_pythonanywhere/bienvenida_chile.html`
- `actualizacion_pythonanywhere/bienvenida_usa.html`

**Acción:**
```powershell
# Comparar con templates principales
$file1 = Get-Content "actualizacion_pythonanywhere\bienvenida_chile.html"
$file2 = Get-Content "templates\taller\bienvenida_chile.html"

# Si son idénticos, eliminar duplicados
if (Compare-Object $file1 $file2 -eq $null) {
    Write-Host "Archivos idénticos - se pueden eliminar duplicados"
    Remove-Item "actualizacion_pythonanywhere\bienvenida_chile.html"
}

# Repetir para bienvenida_usa.html
```

**Decisión:**
- Si son **idénticos** → ELIMINAR de `actualizacion_pythonanywhere/`
- Si son **diferentes** → DOCUMENTAR diferencias y decidir cuál mantener
- Si carpeta queda vacía → ELIMINAR carpeta completa

---

### ✅ Tarea 1.3: Organizar archivos en scripts/

**Archivos actuales:**
1. `scripts/company_settings.html`
2. `scripts/crear_documento_moderno_backup.html`
3. `scripts/debug_js.html`
4. `scripts/diagnostico_imagenes.html`
5. `scripts/landing_egarage.html`
6. `scripts/legacy_documentos/templates/documentos/lista.html`

**Acción:**
```powershell
# Crear carpeta dev_tools si no existe
New-Item -ItemType Directory -Path "dev_tools\html_snippets" -Force

# Mover archivos de desarrollo
Move-Item "scripts\company_settings.html" "dev_tools\html_snippets\"
Move-Item "scripts\crear_documento_moderno_backup.html" "dev_tools\html_snippets\"
Move-Item "scripts\debug_js.html" "dev_tools\html_snippets\"
Move-Item "scripts\diagnostico_imagenes.html" "dev_tools\html_snippets\"
Move-Item "scripts\landing_egarage.html" "dev_tools\html_snippets\"

# Revisar legacy_documentos
# Si es obsoleto:
Remove-Item "scripts\legacy_documentos" -Recurse -Force
```

**Alternativa:** Si prefieres mantenerlos en `scripts/`, crear subcarpeta:
```powershell
New-Item -ItemType Directory -Path "scripts\html_testing" -Force
Move-Item "scripts\*.html" "scripts\html_testing\"
```

---

### ✅ Tarea 1.4: Eliminar templates muy antiguas

**Acción:**
```powershell
# Eliminar vehiculos_old (versiones muy antiguas)
Remove-Item "_disabled_templates\vehiculos_old" -Recurse -Force
```

**Justificación:** Archivos con nombres como `OLD_OLD_crear_vehiculo.html` claramente obsoletos

---

**CHECKPOINT FASE 1:**
- [ ] document_payment_status.html movido
- [ ] actualizacion_pythonanywhere/ verificado y limpiado
- [ ] scripts/ organizado
- [ ] vehiculos_old/ eliminado
- [ ] Git commit creado: `chore: clean up loose template files and old backups`

---

## FASE 2: COMPRIMIR BACKUPS (30 minutos)

### ✅ Tarea 2.1: Comprimir "revision templates/"

**Tamaño:** 758 archivos HTML

**Acción:**
```powershell
# Crear carpeta de archives si no existe
New-Item -ItemType Directory -Path "_archives" -Force

# Comprimir revision templates
Compress-Archive -Path "revision templates" `
    -DestinationPath "_archives\revision_templates_archive_2024-2025.zip" `
    -CompressionLevel Optimal

# Verificar que se creó correctamente
Get-Item "_archives\revision_templates_archive_2024-2025.zip"

# Si todo está bien, eliminar carpeta original
# PRECAUCIÓN: Verificar primero que el ZIP está completo
Remove-Item "revision templates" -Recurse -Force
```

**Estimación de ahorro:** ~15-20 MB dependiendo del contenido

---

### ✅ Tarea 2.2: Política de backups recientes

**Archivos:**
- `_backup_templates_20251026_215347/` (270 archivos) - hace 1 día
- `_backup_templates_20251026_215527/` (~270 archivos) - hace 1 día

**Decisión:** MANTENER por ahora (backup reciente de seguridad)

**Política para el futuro:**
```powershell
# Script de mantenimiento automático (ejecutar mensualmente)
# Guardar como: scripts/cleanup_old_backups.ps1

$backupFolders = Get-ChildItem -Path "_backup_templates_*" -Directory
$cutoffDate = (Get-Date).AddDays(-30)

foreach ($folder in $backupFolders) {
    if ($folder.CreationTime -lt $cutoffDate) {
        Write-Host "Comprimiendo backup antiguo: $($folder.Name)"

        # Comprimir
        Compress-Archive -Path $folder.FullName `
            -DestinationPath "_archives\$($folder.Name).zip" `
            -CompressionLevel Optimal

        # Eliminar original
        Remove-Item $folder.FullName -Recurse -Force

        Write-Host "✅ Backup comprimido y eliminado: $($folder.Name)"
    }
}

# Eliminar backups comprimidos mayores a 90 días
$oldArchives = Get-ChildItem -Path "_archives\_backup_templates_*.zip" |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-90) }

foreach ($archive in $oldArchives) {
    Write-Host "Eliminando backup muy antiguo: $($archive.Name)"
    Remove-Item $archive.FullName -Force
}
```

---

### ✅ Tarea 2.3: Comprimir _disabled_templates/

**Acción:**
```powershell
# Comprimir disabled templates (mayormente archivos .py y .backup)
Compress-Archive -Path "_disabled_templates" `
    -DestinationPath "_archives\disabled_templates_archive.zip" `
    -CompressionLevel Optimal

# Verificar contenido
# Si no se necesita para referencia diaria, eliminar
Remove-Item "_disabled_templates" -Recurse -Force
```

---

**CHECKPOINT FASE 2:**
- [ ] revision templates/ comprimido y eliminado (758 archivos)
- [ ] Script de limpieza automática creado
- [ ] _disabled_templates/ comprimido y eliminado
- [ ] Carpeta _archives/ creada con backups comprimidos
- [ ] Git commit: `chore: compress old template backups and create cleanup script`

**Espacio liberado estimado:** ~25-30 MB

---

## FASE 3: AUDITORÍA DE DUPLICACIONES (2-3 horas)

### ✅ Tarea 3.1: Auditar módulo de clientes

**Ubicaciones detectadas:**
1. `templates/taller/clientes/` (10 archivos)
2. `taller/clientes/templates/taller/clientes/` (1 archivo)
3. `templates/cl/es/clientes/` (9 archivos)
4. `templates/us/en/clientes/` (5 archivos)
5. `templates/us/es/clientes/` (5 archivos)
6. `templates/taller/common/clientes/` (4 archivos)

**Acción:**
```powershell
# Listar todos los archivos de clientes
Write-Host "`n=== TEMPLATES DE CLIENTES ===" -ForegroundColor Cyan

Get-ChildItem -Path "templates" -Filter "*cliente*.html" -Recurse |
    Select-Object Name, DirectoryName |
    Format-Table -AutoSize

# Identificar duplicados por nombre
$clienteFiles = Get-ChildItem -Path "templates" -Filter "*cliente*.html" -Recurse
$duplicates = $clienteFiles | Group-Object Name | Where-Object { $_.Count -gt 1 }

Write-Host "`n=== POSIBLES DUPLICADOS ===" -ForegroundColor Yellow
$duplicates | ForEach-Object {
    Write-Host "`nArchivo: $($_.Name) (encontrado $($_.Count) veces)"
    $_.Group | Select-Object FullName
}
```

**Análisis manual necesario:**
- Comparar contenido de archivos con mismo nombre
- Determinar si son duplicados reales o versiones localizadas
- Documentar diferencias encontradas

**Crear documento:** `docs/AUDIT_CLIENTES_TEMPLATES.md`

---

### ✅ Tarea 3.2: Auditar dashboards

**Ubicaciones detectadas:**
1. `templates/taller/dashboard/` (2 archivos)
2. `templates/taller/common/dashboard/` (2 archivos)
3. `templates/cl/es/dashboard/` (1 archivo)
4. `templates/cl/en/dashboard/` (1 archivo)
5. `templates/common/dashboard/` (1 archivo)
6. `templates/us/` (dashboard_usa.html)
7. `taller/templates/taller/` (suscriptor_dashboard.html)

**Acción:**
```powershell
# Listar dashboards
Get-ChildItem -Path "templates" -Filter "*dashboard*.html" -Recurse |
    Select-Object Name, FullName |
    Format-Table -AutoSize
```

**Decisión esperada:**
- **Consolidar** dashboards comunes en `templates/taller/common/dashboard/`
- **Mantener** versiones país-específicas solo si hay diferencias significativas
- **Usar herencia** de templates para evitar duplicación

---

### ✅ Tarea 3.3: Auditar configuración

**Ubicaciones:**
1. `templates/taller/configuracion.html`
2. `templates/taller/configuracion/` (5 archivos)
3. `taller/templates/taller/configuracion.html`

**Acción:**
```powershell
# Comparar archivos de configuración
fc "templates\taller\configuracion.html" "taller\templates\taller\configuracion.html"
```

**Decisión:**
- Si son idénticos → mantener solo uno (preferiblemente en `templates/taller/configuracion/`)
- Si son diferentes → renombrar para clarificar propósito

---

**CHECKPOINT FASE 3:**
- [ ] Auditoría de clientes completada
- [ ] Auditoría de dashboards completada
- [ ] Auditoría de configuración completada
- [ ] Documento de hallazgos creado: `docs/DUPLICATES_AUDIT.md`
- [ ] Lista de acciones de consolidación definida

---

## FASE 4: CONSOLIDACIÓN (Variable - 3-8 horas)

### ✅ Tarea 4.1: Implementar consolidaciones identificadas

**Basado en resultados de Fase 3**

**Proceso para cada duplicado:**

1. **Identificar template "canónica"** (la versión a mantener)
2. **Verificar diferencias** entre versiones
3. **Si son idénticas:**
   ```powershell
   # Eliminar duplicado
   Remove-Item "path/to/duplicate.html"

   # Buscar referencias en código
   Get-ChildItem -Path "taller" -Filter "*.py" -Recurse |
       Select-String "duplicate.html"

   # Actualizar referencias para apuntar a versión canónica
   ```

4. **Si tienen diferencias menores:**
   - Usar tags `{% trans %}` para textos
   - Usar bloques `{% if LANGUAGE_CODE == 'es' %}` si necesario
   - Consolidar en una sola template

5. **Si tienen diferencias significativas:**
   - Crear template base común
   - Usar herencia: `{% extends "base.html" %}`
   - Sobrescribir solo bloques diferentes

**Ejemplo de consolidación:**

**ANTES:**
```
templates/taller/clientes/lista_clientes.html  (español)
templates/taller/us/en/clientes/customer_list.html  (inglés)
```

**DESPUÉS:**
```django
<!-- templates/taller/common/clientes/lista_clientes.html -->
{% load i18n %}
<h1>{% trans "Customers" %}</h1>
<!-- contenido común con i18n -->
```

---

### ✅ Tarea 4.2: Actualizar referencias en código Python

**Acción:**
```powershell
# Buscar todas las referencias a templates
Get-ChildItem -Path "taller" -Filter "*.py" -Recurse |
    Select-String "\.html" |
    Out-File "template_references.txt"

# Revisar manualmente y actualizar según consolidaciones
```

**Archivos típicos a actualizar:**
- `taller/views.py`
- `taller/views_*.py`
- `taller/*/views.py`

---

### ✅ Tarea 4.3: Testing exhaustivo

**Acción:**
```powershell
# Ejecutar tests
python manage.py test

# Verificar cada módulo manualmente:
# - Login en Chile español
# - Login en USA inglés
# - Crear cliente (ambos países)
# - Ver dashboard (ambos países)
# - Todas las vistas consolidadas
```

**Crear checklist de testing:** `docs/CONSOLIDATION_TESTING_CHECKLIST.md`

---

**CHECKPOINT FASE 4:**
- [ ] Duplicados consolidados
- [ ] Referencias en código Python actualizadas
- [ ] Tests ejecutados y pasados
- [ ] Testing manual completado
- [ ] Git commits por cada consolidación
- [ ] Git commit final: `refactor: consolidate duplicate templates`

---

## FASE 5: MEJORAS DE ESTRUCTURA (Opcional - 4-6 horas)

### ✅ Tarea 5.1: Reorganizar estructura de directorios

**Propuesta de nueva estructura:**

```
templates/
├── base/                    # Templates base del proyecto
│   ├── base.html
│   ├── base_authenticated.html
│   └── base_public.html
│
├── common/                  # Componentes comunes multiidioma
│   ├── components/
│   │   ├── forms/
│   │   ├── tables/
│   │   └── modals/
│   ├── layouts/
│   │   ├── dashboard_layout.html
│   │   └── form_layout.html
│   └── includes/
│       ├── navbar.html
│       └── footer.html
│
├── country/                 # Templates específicas por país
│   ├── cl/
│   │   └── es/             # Chile español (principal)
│   │       ├── clientes/
│   │       ├── vehiculos/
│   │       └── dashboard/
│   └── us/
│       ├── en/             # USA inglés (principal)
│       │   ├── customers/
│       │   ├── vehicles/
│       │   └── dashboard/
│       └── es/             # USA español (hispanos)
│           └── customers/
│
├── taller/                  # Módulos del taller (multiidioma)
│   ├── clientes/
│   ├── vehiculos/
│   ├── servicios/
│   ├── repuestos/
│   ├── documentos/
│   ├── reportes/
│   └── configuracion/
│
├── account/                 # Autenticación (común)
├── admin/                   # Administración
├── emails/                  # Templates de email
├── pdf/                     # Templates para PDFs
└── public/                  # Landing pages públicas
```

**Acción:** Solo implementar si el equipo está de acuerdo y tienen tiempo

---

### ✅ Tarea 5.2: Mejorar uso de i18n

**Identificar templates sin i18n:**
```powershell
# Buscar templates en common/ sin {% load i18n %}
Get-ChildItem -Path "templates\taller\common" -Filter "*.html" -Recurse |
    Where-Object {
        $content = Get-Content $_.FullName -Raw
        $content -notmatch "{%\s*load\s+i18n\s*%}"
    } |
    Select-Object Name, FullName
```

**Agregar i18n donde corresponda:**
```django
{% load i18n %}

<!-- ANTES -->
<h1>Customers</h1>

<!-- DESPUÉS -->
<h1>{% trans "Customers" %}</h1>
```

---

### ✅ Tarea 5.3: Documentar estrategia

**Crear archivo:** `docs/TEMPLATES_ORGANIZATION_GUIDE.md`

**Contenido:**
- Estructura de directorios
- Cuándo usar template común vs país-específica
- Convenciones de nomenclatura
- Guía de i18n
- Ejemplos de herencia de templates
- Proceso de traducción

---

**CHECKPOINT FASE 5:**
- [ ] Nueva estructura de directorios implementada (si se decidió hacerlo)
- [ ] i18n mejorado en templates comunes
- [ ] Documentación creada
- [ ] Equipo capacitado en nuevas convenciones
- [ ] Git commit: `refactor: improve templates structure and i18n`

---

## FASE 6: AUTOMATIZACIÓN Y MANTENIMIENTO (1-2 horas)

### ✅ Tarea 6.1: Script de limpieza automática

**Crear archivo:** `scripts/cleanup_templates.ps1`

```powershell
<#
.SYNOPSIS
Script de limpieza automática de templates backup

.DESCRIPTION
Comprime backups mayores a 30 días y elimina archives mayores a 90 días
Ejecutar mensualmente o agregar a tarea programada

.EXAMPLE
.\scripts\cleanup_templates.ps1
#>

$ErrorActionPreference = "Stop"
$projectRoot = "E:\projecto\e_garage"
Set-Location $projectRoot

Write-Host "`n=== LIMPIEZA DE TEMPLATES BACKUP ===" -ForegroundColor Cyan
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

# Crear carpeta de archives si no existe
if (-not (Test-Path "_archives")) {
    New-Item -ItemType Directory -Path "_archives" | Out-Null
    Write-Host "✅ Carpeta _archives/ creada"
}

# 1. Comprimir backups mayores a 30 días
$backupFolders = Get-ChildItem -Path "_backup_templates_*" -Directory
$cutoffDate = (Get-Date).AddDays(-30)
$compressed = 0

foreach ($folder in $backupFolders) {
    if ($folder.CreationTime -lt $cutoffDate) {
        $zipName = "$($folder.Name).zip"
        $zipPath = "_archives\$zipName"

        Write-Host "📦 Comprimiendo: $($folder.Name)..."

        try {
            Compress-Archive -Path $folder.FullName `
                -DestinationPath $zipPath `
                -CompressionLevel Optimal `
                -Force

            Remove-Item $folder.FullName -Recurse -Force
            Write-Host "   ✅ Comprimido y eliminado" -ForegroundColor Green
            $compressed++
        }
        catch {
            Write-Host "   ❌ Error: $_" -ForegroundColor Red
        }
    }
}

if ($compressed -eq 0) {
    Write-Host "ℹ️  No hay backups antiguos para comprimir (>30 días)"
}

# 2. Eliminar archives mayores a 90 días
$oldArchives = Get-ChildItem -Path "_archives\_backup_templates_*.zip" -ErrorAction SilentlyContinue |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-90) }

if ($oldArchives) {
    Write-Host "`n🗑️  Eliminando archives muy antiguos (>90 días)..."
    foreach ($archive in $oldArchives) {
        Write-Host "   Eliminando: $($archive.Name)"
        Remove-Item $archive.FullName -Force
    }
    Write-Host "   ✅ $(($oldArchives | Measure-Object).Count) archives eliminados"
}
else {
    Write-Host "`nℹ️  No hay archives muy antiguos para eliminar (>90 días)"
}

# 3. Reporte final
Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
$currentBackups = (Get-ChildItem -Path "_backup_templates_*" -Directory -ErrorAction SilentlyContinue).Count
$currentArchives = (Get-ChildItem -Path "_archives\_backup_templates_*.zip" -ErrorAction SilentlyContinue).Count

Write-Host "Backups activos (carpetas): $currentBackups"
Write-Host "Archives comprimidos: $currentArchives"
Write-Host "`n✅ Limpieza completada`n"
```

---

### ✅ Tarea 6.2: Tarea programada de Windows

**Acción:**
```powershell
# Crear tarea programada para ejecutar el 1ro de cada mes
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"E:\projecto\e_garage\scripts\cleanup_templates.ps1`""

$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 2am

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

Register-ScheduledTask -TaskName "E_Garage_Template_Cleanup" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Description "Limpieza mensual de templates backup"

Write-Host "✅ Tarea programada creada: 1ro de cada mes a las 2am"
```

---

### ✅ Tarea 6.3: Pre-commit hook para prevenir archivos sueltos

**Crear archivo:** `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Pre-commit hook para verificar templates

echo "Verificando templates..."

# Buscar archivos .html en raíz (excepto algunos permitidos)
html_files=$(find . -maxdepth 1 -name "*.html" -not -name "base.html" 2>/dev/null)

if [ -n "$html_files" ]; then
    echo "❌ ERROR: Archivos HTML sueltos en raíz del proyecto:"
    echo "$html_files"
    echo ""
    echo "Por favor, mueve los archivos a la carpeta 'templates/' correspondiente"
    exit 1
fi

echo "✅ Verificación de templates OK"
exit 0
```

---

**CHECKPOINT FASE 6:**
- [ ] Script de limpieza automática creado
- [ ] Tarea programada configurada (opcional)
- [ ] Pre-commit hook instalado (opcional)
- [ ] Documentación de mantenimiento actualizada
- [ ] Git commit: `chore: add automated template cleanup scripts`

---

## RESUMEN DE ESTIMACIONES

| Fase | Duración Estimada | Prioridad | Impacto |
|------|-------------------|-----------|---------|
| Fase 1: Limpieza Inmediata | 1-2 horas | 🔴 Alta | 🟢 Alto |
| Fase 2: Comprimir Backups | 30 minutos | 🟡 Media | 🟢 Alto |
| Fase 3: Auditoría | 2-3 horas | 🟡 Media | 🟢 Alto |
| Fase 4: Consolidación | 3-8 horas | 🟡 Media | 🟢 Alto |
| Fase 5: Mejoras Estructura | 4-6 horas | 🟢 Baja | 🟡 Medio |
| Fase 6: Automatización | 1-2 horas | 🟡 Media | 🟢 Alto |
| **TOTAL** | **12-22 horas** | - | - |

---

## RESULTADOS ESPERADOS

### Antes:
- ✖️ 291 templates activas
- ✖️ ~1,307 archivos en backups sin comprimir
- ✖️ 11 archivos sueltos fuera de templates/
- ✖️ Duplicaciones sin documentar
- ✖️ Sin política de mantenimiento
- ✖️ Espacio total: ~40-50 MB

### Después:
- ✅ ~250-270 templates activas (consolidación de 20-40 archivos)
- ✅ Backups comprimidos en _archives/
- ✅ 0 archivos sueltos
- ✅ Duplicaciones auditadas y documentadas
- ✅ Política de mantenimiento automático
- ✅ Espacio total: ~20-25 MB (50% reducción)
- ✅ Mantenibilidad mejorada significativamente

---

## CHECKLIST GENERAL

### Pre-inicio:
- [ ] Backup completo del proyecto creado
- [ ] Git branch creado: `feature/template-cleanup`
- [ ] Equipo notificado del trabajo

### Durante ejecución:
- [ ] Commits frecuentes con mensajes descriptivos
- [ ] Testing después de cada fase
- [ ] Documentación actualizada

### Post-finalización:
- [ ] Testing completo en ambiente de desarrollo
- [ ] Code review del equipo
- [ ] Merge a rama principal
- [ ] Deploy y verificación en staging
- [ ] Documentación final actualizada
- [ ] Capacitación del equipo (si hubo cambios estructurales)

---

## COMANDOS ÚTILES DE REFERENCIA

### Estadísticas de templates:
```powershell
# Total de templates activas
(Get-ChildItem -Path "templates" -Filter "*.html" -Recurse).Count

# Templates por módulo
Get-ChildItem -Path "templates\taller" -Directory | ForEach-Object {
    $count = (Get-ChildItem $_.FullName -Filter "*.html" -Recurse).Count
    [PSCustomObject]@{
        Módulo = $_.Name
        'Archivos HTML' = $count
    }
} | Format-Table -AutoSize

# Archivos más grandes
Get-ChildItem -Path "templates" -Filter "*.html" -Recurse |
    Sort-Object Length -Descending |
    Select-Object -First 10 Name, @{Name="Tamaño (KB)";Expression={[math]::Round($_.Length/1KB,2)}}, FullName
```

### Buscar templates no referenciadas:
```powershell
# Listar todas las templates
$allTemplates = Get-ChildItem -Path "templates" -Filter "*.html" -Recurse |
    Select-Object -ExpandProperty Name

# Buscar referencias en código Python
foreach ($template in $allTemplates) {
    $refs = Get-ChildItem -Path "taller" -Filter "*.py" -Recurse |
        Select-String $template

    if (-not $refs) {
        Write-Host "⚠️  Sin referencias: $template"
    }
}
```

### Verificar uso de i18n:
```powershell
# Templates sin i18n en common/
Get-ChildItem -Path "templates\taller\common" -Filter "*.html" -Recurse |
    Where-Object {
        (Get-Content $_.FullName -Raw) -notmatch "{%\s*load\s+i18n\s*%}"
    } |
    Select-Object Name, FullName
```

---

## CONTACTO Y SOPORTE

Si tienes dudas durante la ejecución:
1. Revisar documentación en `docs/`
2. Consultar este plan de acción
3. Crear issue en repositorio (si aplica)
4. Consultar con el equipo

---

**Buena suerte con la limpieza! 🚀**

**Próxima revisión recomendada:** 3 meses después de completar este plan



