# 🧹 LIMPIEZA COMPLETA DE ARCHIVOS ESTÁTICOS - eGarage

Este toolkit completo automatiza la limpieza, reorganización y optimización de archivos estáticos en eGarage, siguiendo las mejores prácticas para producción con Django + WhiteNoise.

## 🎯 Objetivos

- ✅ **Eliminar archivos innecesarios** en producción (.map, .psd, .zip, etc.)
- ✅ **Reorganizar estructura** siguiendo convenciones canónicas
- ✅ **Normalizar nombres** (kebab-case, sin espacios/mayúsculas/acentos)
- ✅ **Eliminar duplicados** por hash y nombre
- ✅ **Optimizar para WhiteNoise** y DEBUG=False
- ✅ **Generar backups** y cuarentena automática
- ✅ **Validar resultados** con reportes detallados

## 📁 Estructura de Archivos

```
tools/
├── clean/                           # Scripts de limpieza
│   ├── audit_static.py             # Auditoría completa
│   ├── suggest_moves.py            # Plan de reorganización
│   ├── update_template_refs.py     # Actualización de referencias
│   ├── hash_assets.py              # Cache-busting
│   └── README_static_cleanup.md    # Documentación básica
├── apply_static_cleanup.ps1        # Script principal de limpieza
├── generate_clean_static_zip.ps1   # Generador de ZIP canónico
├── validate_static_cleanup.ps1     # Validador de resultados
├── run_complete_static_cleanup.ps1 # Script maestro completo
├── quarantine_delete_static.ps1    # Script de cuarentena
└── README_COMPLETE_STATIC_CLEANUP.md # Esta documentación
```

## 🚀 Uso Rápido

### Opción 1: Proceso Completo Automático
```powershell
# Dry run (recomendado primero)
.\tools\run_complete_static_cleanup.ps1 -Root "E:\projecto\e_garage" -DryRun

# Aplicar cambios reales
.\tools\run_complete_static_cleanup.ps1 -Root "E:\projecto\e_garage"

# Con generación de ZIP canónico
.\tools\run_complete_static_cleanup.ps1 -Root "E:\projecto\e_garage" -GenerateZip
```

### Opción 2: Proceso Paso a Paso
```powershell
# 1. Auditoría
python tools/clean/audit_static.py --base "E:\projecto\e_garage\static" --out "tools\reports\audit_static.csv"

# 2. Plan de reorganización
python tools/clean/suggest_moves.py --base "E:\projecto\e_garage\static" --manifest "tools\reports\manifest.json"

# 3. Aplicar limpieza
.\tools\apply_static_cleanup.ps1 -Root "E:\projecto\e_garage"

# 4. Actualizar referencias
python tools/clean/update_template_refs.py --templates "E:\projecto\e_garage\templates" --static "E:\projecto\e_garage\static" --manifest "tools\reports\manifest.json"

# 5. Validar resultados
.\tools\validate_static_cleanup.ps1 -Root "E:\projecto\e_garage"

# 6. Collectstatic
python manage.py collectstatic --noinput
```

## 📊 Proceso Detallado

### 1. Auditoría (`audit_static.py`)
**Detecta:**
- Duplicados por SHA1
- Nombres problemáticos (espacios, mayúsculas, acentos)
- Tipos de archivo
- Tamaños
- Archivos innecesarios en producción

**Salida:** `tools/reports/audit_static.csv`

### 2. Plan de Reorganización (`suggest_moves.py`)
**Genera:**
- Estructura canónica: `taller/{common,cl,us}/{css,js,img,fonts,media}`
- Nombres normalizados (kebab-case)
- Mapeo old → new
- Eliminación de duplicados

**Salida:** `tools/reports/manifest.json`

### 3. Aplicación de Limpieza (`apply_static_cleanup.ps1`)
**Acciones:**
- Borra archivos innecesarios (.map, .psd, .zip, etc.)
- Mueve archivos a estructura canónica
- Normaliza nombres
- Crea backups automáticos
- Envía archivos borrados a cuarentena

### 4. Actualización de Referencias (`update_template_refs.py`)
**Actualiza:**
- Templates HTML (`{% static %}` tags)
- Archivos CSS (`url()` references)
- Archivos JavaScript (`import`/`require`)
- Crea backups (.bak) automáticamente

### 5. Validación (`validate_static_cleanup.ps1`)
**Verifica:**
- Estructura de directorios
- Ausencia de archivos problemáticos
- Nombres correctos
- Ausencia de duplicados
- Archivos críticos presentes

### 6. Generación de ZIP (`generate_clean_static_zip.ps1`)
**Crea:**
- ZIP con estructura canónica
- Archivo de documentación de estructura
- Solo archivos necesarios para producción

## 🗂️ Estructura Canónica Final

```
static/
├── taller/
│   ├── common/              # Archivos compartidos
│   │   ├── css/            # Estilos globales
│   │   ├── js/             # Scripts globales
│   │   ├── img/            # Imágenes globales
│   │   ├── fonts/          # Fuentes globales
│   │   └── media/          # Videos/audio globales
│   ├── cl/                 # Específicos de Chile
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── us/                 # Específicos de USA
│       ├── css/
│       ├── js/
│       └── img/
└── vendor/                 # Librerías de terceros
    ├── jquery/
    ├── select2/
    └── autocomplete_light/
```

## 🗑️ Archivos Eliminados en Producción

### Automáticamente Borrados:
- **Source maps**: `*.map`
- **Archivos de diseño**: `*.psd`, `*.ai`, `*.fig`
- **Archivos comprimidos**: `*.zip`, `*.rar`, `*.7z`
- **Versiones no-minificadas** cuando existe `.min.*`
- **Archivos experimentales**: `*experimental*`, `*temp*`, `*test*`, `*debug*`
- **Duplicados por hash** (mantiene solo uno)

### Conservados:
- Archivos minificados (`.min.css`, `.min.js`)
- Archivos únicos (sin versión minificada)
- Archivos críticos para la aplicación
- Librerías de terceros

## 📋 Reportes Generados

### En `tools/reports/`:
- `audit_static.csv` - Auditoría completa
- `manifest.json` - Plan de reorganización
- `cleanup_report_*.txt` - Reporte de limpieza
- `validation_report_*.txt` - Reporte de validación
- `static_clean_canonical.zip` - ZIP con estructura canónica

### En `tools/backup/`:
- `static_backup_*/` - Backup completo antes de cambios
- `static_cleanup_*/` - Backup de archivos individuales

### En `tools/quarantine/`:
- `deleted_*/` - Archivos borrados (con log de motivos)
- `static_deletes_*.zip` - ZIP de archivos en cuarentena

## ⚙️ Configuración para Producción

### Django Settings:
```python
# settings.py
DEBUG = False
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... otros middlewares
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Comandos Post-Limpieza:
```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Verificar configuración
python manage.py check --deploy

# Probar en modo producción
python manage.py runserver --settings=gestion_taller.settings_prod
```

## 🔧 Troubleshooting

### Problemas Comunes:

1. **Error de permisos**: Ejecutar PowerShell como administrador
2. **Archivos en uso**: Cerrar servidor Django antes de limpiar
3. **Referencias rotas**: Verificar que `STATIC_URL` esté configurado
4. **Archivos faltantes**: Revisar cuarentena en `tools/quarantine/`

### Recuperación:
```powershell
# Restaurar desde backup
Copy-Item "tools\backup\static_backup_*\*" "static\" -Recurse -Force

# Restaurar desde cuarentena
Expand-Archive "tools\quarantine\static_deletes_*.zip" -DestinationPath "static\"
```

## 📈 Beneficios Esperados

- **Reducción de tamaño**: 20-40% menos archivos
- **Mejor organización**: Estructura predecible
- **Fácil mantenimiento**: Nombres consistentes
- **Mejor performance**: Sin duplicados, archivos optimizados
- **Escalabilidad**: Separación por país/idioma
- **Seguridad**: Backups automáticos

## 🎯 Próximos Pasos

1. **Revisar reportes** en `tools/reports/`
2. **Probar aplicación** en modo DEBUG=False
3. **Verificar WhiteNoise** sirve archivos correctamente
4. **Hacer commit** de los cambios
5. **Documentar** cualquier customización necesaria

## 📞 Soporte

Si encuentras problemas:
1. Revisar logs en `tools/reports/`
2. Verificar backups en `tools/backup/`
3. Consultar cuarentena en `tools/quarantine/`
4. Ejecutar validación: `.\tools\validate_static_cleanup.ps1`

---

**¡Tu carpeta `static/` quedará técnicamente perfecta y lista para producción!** 🎉
