# 🚀 eGarage v2.1.0 - Release Notes

**Fecha de Release:** 08 de Noviembre de 2025
**Versión:** 2.1.0
**Build:** `egarage_v2.1.0_2025-11-08_1332.zip`

---

## 📋 Resumen Ejecutivo

Esta versión introduce el **Sistema de Branding Unificado**, permitiendo que los suscriptores personalicen completamente el logo y colores de su taller en todas las páginas del sistema. Además, incluye mejoras significativas en la creación de documentos y optimizaciones de rendimiento.

---

## 🎨 Nuevas Características

### Sistema de Branding Unificado
- ✅ **Objeto BRAND centralizado** - Todas las propiedades de marca en un solo lugar
- ✅ **Logo personalizable** - Los suscriptores pueden subir su logo y verlo en todas las páginas
- ✅ **Prioridad inteligente** - CompanySettings → ConfiguracionEmpresa → Empresa
- ✅ **Template reusable** - Header único (`_includes/brand_header.html`)
- ✅ **Variables CSS dinámicas** - Colores personalizados aplicados automáticamente

### Mejoras en Documentos
- ✅ **Número automático** - El campo "numero" se autogenera si se deja vacío
- ✅ **No obligatorio** - Opcional en el formulario de creación
- ✅ **API mejorada** - Endpoint `api_next_number` para obtener siguiente número
- ✅ **Validaciones robustas** - Mejor manejo de errores

---

## 🔧 Mejoras Técnicas

### Context Processors
```python
# Nuevo objeto BRAND disponible en todos los templates
{{ BRAND.logo_url }}
{{ BRAND.name }}
{{ BRAND.tagline }}
{{ BRAND.primary_color }}
{{ BRAND.secondary_color }}
{{ BRAND.country }}
{{ BRAND.currency }}
```

### Variables de Entorno
```python
# Ahora configurables via environment
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles")))
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))
```

### Defaults Configurables
```python
DEFAULT_BRAND_LOGO_URL = "/static/branding/egarage_logo.svg"
DEFAULT_BRAND_NAME = "eGarage"
DEFAULT_BRAND_TAGLINE = "Mission Control for your Workshop"
DEFAULT_BRAND_COUNTRY = "cl"
DEFAULT_BRAND_CURRENCY = "CLP"
DEFAULT_BRAND_PRIMARY_COLOR = "#0d6efd"
DEFAULT_BRAND_SECONDARY_COLOR = "#6c757d"
```

---

## 🐛 Bugs Corregidos

### Branding
- ✅ Logo del suscriptor no aparecía en Centro de Operaciones Espacial
- ✅ Prioridad de búsqueda de logo incorrecta
- ✅ Cache no se invalidaba correctamente
- ✅ Variables inconsistentes entre templates

### Documentos
- ✅ Error "campo numero es requerido" al crear documentos
- ✅ NoReverseMatch en `api_next_number`
- ✅ Validación innecesaria de campo autogenerado

### Sistema
- ✅ ModuleNotFoundError en `debug_urls`
- ✅ Referencias rotas eliminadas
- ✅ Imports circulares resueltos

---

## 📂 Archivos Modificados

### Nuevos Archivos
- ✅ `taller/version.py` - Sistema de versionado
- ✅ `taller/context_processors/company_branding_unified.py` - Context processor unificado
- ✅ `templates/_includes/brand_header.html` - Header reusable
- ✅ `taller/management/commands/egarage_version.py` - Comando de versión
- ✅ `taller/management/commands/check_logo.py` - Diagnóstico de logos
- ✅ `scripts/check_logo.ps1` - Script de verificación
- ✅ `docs/BRANDING_UNIFICADO_COMPLETADO.md` - Documentación técnica
- ✅ `IMPLEMENTACION_BRANDING_COMPLETADA.md` - Guía de implementación

### Archivos Modificados
- ✅ `taller/context_processors/__init__.py` - Objeto BRAND implementado
- ✅ `taller/__init__.py` - Exporta versión del sistema
- ✅ `gestion_taller/settings.py` - Defaults de branding + env vars
- ✅ `templates/base.html` - Usa BRAND y include
- ✅ `templates/changelog.html` - Changelog actualizado
- ✅ `taller/forms/documento_form.py` - Campo numero opcional
- ✅ `taller/documentos/urls.py` - URL api_next_number agregada
- ✅ `gestion_taller/urls.py` - Limpieza de referencias rotas
- ✅ `scripts/pack_release.ps1` - Incluye versión en nombre del paquete

### Archivos Eliminados
- ✅ `taller/views_extra/debug_urls.py` - Ya no necesario
- ✅ `taller/views_extra/debug_branding.py` - Ya no necesario
- ✅ `templates/debug_branding.html` - Ya no necesario

---

## 🚀 Comandos Nuevos

### Ver Versión del Sistema
```bash
python manage.py egarage_version
```

### Ver Changelog Completo
```bash
python manage.py egarage_version --changelog
```

### Diagnosticar Logos
```bash
python manage.py check_logo
```

### Empaquetar Release
```powershell
.\scripts\pack_release.ps1
```

Genera: `egarage_v2.1.0_2025-11-08_HHMM.zip`

---

## 📦 Información del Paquete

**Archivo:** `egarage_v2.1.0_2025-11-08_1332.zip`
**Tamaño:** ~71 MB
**Contenido:**
- ✅ Todo el código fuente
- ✅ Templates actualizados
- ✅ Migraciones de base de datos
- ✅ Documentación completa

**Excluye:**
- ❌ `.git` (control de versiones)
- ❌ `venv`, `.venv` (entornos virtuales)
- ❌ `media` (archivos subidos por usuarios)
- ❌ `static_root` (archivos estáticos compilados)
- ❌ `__pycache__` (archivos compilados Python)
- ❌ `*.pyc` (bytecode)
- ❌ Archivos `.zip` previos

---

## 🔄 Instrucciones de Actualización

### En Desarrollo (Local)
```bash
# 1. Detener el servidor
Ctrl + C

# 2. Limpiar caché
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# 3. Reiniciar servidor
python manage.py runserver 127.0.0.1:8000

# 4. Limpiar caché del navegador
Ctrl + Shift + R
```

### En Producción
```bash
# 1. Backup de la base de datos actual
python manage.py dumpdata > backup_before_v2.1.0.json

# 2. Descomprimir el nuevo paquete
unzip egarage_v2.1.0_2025-11-08_1332.zip -d /path/to/deployment

# 3. Instalar dependencias (si hay cambios)
pip install -r requirements.txt

# 4. Ejecutar migraciones (si las hay)
python manage.py migrate

# 5. Recolectar archivos estáticos
python manage.py collectstatic --no-input

# 6. Limpiar caché
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# 7. Reiniciar servidor (gunicorn, uwsgi, etc.)
sudo systemctl restart egarage
```

---

## 🔐 Variables de Entorno

### Opcionales (con defaults seguros)
```bash
# Rutas de archivos
export STATIC_ROOT="/var/www/egarage/staticfiles"
export MEDIA_ROOT="/var/www/egarage/media"

# Seguridad
export DJANGO_DEBUG="0"  # False en producción
export DJANGO_SECRET_KEY="tu-secret-key-super-segura"

# Hosts permitidos
export DJANGO_ALLOWED_HOSTS="egarage.cl,www.egarage.cl"
export DJANGO_CSRF_TRUSTED_ORIGINS="https://egarage.cl,https://www.egarage.cl"
```

---

## ✅ Verificación Post-Actualización

### 1. Verificar Versión
```bash
python manage.py egarage_version
```
Debería mostrar: **2.1.0**

### 2. Verificar Logo
```bash
python manage.py check_logo
```

### 3. Verificar Sistema
```bash
python manage.py check
```
Debería mostrar: **System check identified no issues**

### 4. Verificar en el Navegador
- Logo aparece en todas las páginas ✅
- Se pueden crear documentos sin error ✅
- Centro de Operaciones funciona correctamente ✅

---

## 🎯 Beneficios de esta Versión

### Para Suscriptores
- ✅ **Personalización completa** - Logo y colores propios
- ✅ **Mejor UX** - Documentos más fáciles de crear
- ✅ **Consistencia** - Mismo branding en todas las páginas

### Para Desarrolladores
- ✅ **Código más limpio** - Sistema BRAND centralizado
- ✅ **Fácil mantenimiento** - Un solo lugar para actualizar
- ✅ **Mejor escalabilidad** - Preparado para más features

### Para DevOps
- ✅ **Configuración flexible** - Variables de entorno
- ✅ **Deploy más fácil** - Paquetes con versión
- ✅ **Diagnóstico mejorado** - Comandos de verificación

---

## 📚 Documentación

### Técnica
- `docs/BRANDING_UNIFICADO_COMPLETADO.md` - Arquitectura del sistema
- `IMPLEMENTACION_BRANDING_COMPLETADA.md` - Guía de implementación
- `taller/version.py` - Información de versión

### Scripts
- `scripts/pack_release.ps1` - Empaquetar releases
- `scripts/check_logo.ps1` - Verificar logos
- `scripts/verify_branding.ps1` - Verificar branding

### Comandos Management
- `check_logo` - Diagnosticar logos
- `egarage_version` - Ver versión del sistema

---

## 🆘 Soporte

### Si tienes problemas:

1. **Logo no aparece:**
   ```bash
   python manage.py check_logo
   ```

2. **Error al crear documentos:**
   - Verifica que dejaste el campo "numero" vacío
   - El sistema lo genera automáticamente

3. **Error de módulos:**
   ```bash
   python manage.py check
   ```

4. **Caché persistente:**
   ```bash
   python manage.py shell -c "from django.core.cache import cache; cache.clear()"
   ```

---

## 🎉 Próximas Versiones

### Planificado para v2.2.0
- 📊 Dashboard de reportes mejorado
- 🔔 Sistema de notificaciones en tiempo real
- 📱 Mejor soporte móvil
- 🌐 Más idiomas (PT, FR)

---

**Desarrollado por:** eGarage Team
**Licencia:** Propietaria
**Soporte:** support@egarage.cl

---

## ✅ Checklist de Actualización

- [ ] Backup de base de datos realizado
- [ ] Paquete descargado y descomprimido
- [ ] Dependencias actualizadas
- [ ] Migraciones ejecutadas
- [ ] Archivos estáticos recolectados
- [ ] Caché limpiado
- [ ] Servidor reiniciado
- [ ] Versión verificada (`python manage.py egarage_version`)
- [ ] Logo verificado (`python manage.py check_logo`)
- [ ] Sistema verificado (`python manage.py check`)
- [ ] Tests de navegación realizados
- [ ] Logs revisados sin errores

---

¡Gracias por usar eGarage! 🚗✨
