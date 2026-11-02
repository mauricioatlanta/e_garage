# 🧹 Toolkit de Limpieza de Archivos Estáticos

Este toolkit automatiza la limpieza y reorganización de archivos estáticos en eGarage, siguiendo las mejores prácticas de Django.

## 📋 Proceso Completo

### 1. Auditoría de Archivos
```bash
python tools/clean/audit_static.py --base E:\projecto\e_garage\static --out E:\projecto\e_garage\tools\reports\audit_static.csv
```

**Detecta:**
- ✅ Duplicados por SHA1
- ✅ Nombres con espacios/mayúsculas/acentos
- ✅ Extensiones problemáticas
- ✅ Tamaños de archivos
- ✅ Tipos de archivo

### 2. Plan de Reorganización
```bash
python tools/clean/suggest_moves.py --base E:\projecto\e_garage\static --manifest E:\projecto\e_garage\tools\reports\manifest.json
```

**Genera:**
- 📁 Estructura canónica: `static/taller/{common,cl,us}/{css,js,img,fonts,media}`
- 🏷️ Nombres normalizados: kebab-case, sin espacios/mayúsculas/acentos
- 📦 Archivos de terceros en `vendor/`
- 🗂️ Manifest JSON con mapeo old → new

### 3. Aplicar Reorganización
```bash
python tools/clean/suggest_moves.py --base E:\projecto\e_garage\static --manifest E:\projecto\e_garage\tools\reports\manifest.json --apply
```

### 4. Actualizar Referencias
```bash
# Dry run primero
python tools/clean/update_template_refs.py --templates E:\projecto\e_garage\templates --static E:\projecto\e_garage\static --manifest E:\projecto\e_garage\tools\reports\manifest.json --dry

# Aplicar cambios
python tools/clean/update_template_refs.py --templates E:\projecto\e_garage\templates --static E:\projecto\e_garage\static --manifest E:\projecto\e_garage\tools\reports\manifest.json
```

**Actualiza:**
- 🎨 Referencias en templates HTML
- 📄 Referencias en archivos CSS
- ⚡ Referencias en archivos JavaScript
- 💾 Crea backups automáticos (.bak)

### 5. Cache-Busting (Opcional)
```bash
# Generar hashes
python tools/clean/hash_assets.py --base E:\projecto\e_garage\static --manifest E:\projecto\e_garage\tools\reports\hashed.json

# Aplicar hashes
python tools/clean/hash_assets.py --base E:\projecto\e_garage\static --manifest E:\projecto\e_garage\tools\reports\hashed.json --apply

# Actualizar referencias con hashes
python tools/clean/update_template_refs.py --templates E:\projecto\e_garage\templates --static E:\projecto\e_garage\static --manifest E:\projecto\e_garage\tools\reports\hashed.json
```

## 📊 Resultados de la Auditoría Actual

### Estadísticas Generales
- **Total archivos**: 131
- **Archivos con problemas**: 3 (mayúsculas)
- **Archivos duplicados**: 28 (en 13 grupos)
- **Tamaño total**: 11.90 MB

### Problemas Detectados
1. **Archivos con mayúsculas** (3):
   - `documentos/README_patch.md`
   - `img/TallerPro_logo.png`
   - `src/App.vue`

2. **Duplicados principales**:
   - Select2 CSS (2 copias)
   - Tailwind CSS (3 copias)
   - Videos intro (2 copias)
   - jQuery (2 copias)

### Estructura Propuesta
```
static/
├── taller/
│   ├── common/          # Archivos compartidos
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   ├── fonts/
│   │   └── media/
│   ├── cl/              # Específicos de Chile
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── us/              # Específicos de USA
│       ├── css/
│       ├── js/
│       └── img/
└── vendor/              # Librerías de terceros
    ├── jquery/
    ├── select2/
    └── autocomplete_light_custom/
```

## 🎯 Beneficios

1. **Organización**: Estructura clara y predecible
2. **Mantenimiento**: Fácil localización de archivos
3. **Performance**: Eliminación de duplicados
4. **Escalabilidad**: Separación por país/idioma
5. **Cache**: Sistema de cache-busting opcional
6. **Backup**: Respaldo automático de cambios

## ⚠️ Consideraciones

- **Backup**: Siempre hacer backup antes de aplicar cambios
- **Testing**: Probar en entorno de desarrollo primero
- **Django**: Asegurar que `STATIC_URL` esté configurado correctamente
- **Collectstatic**: Ejecutar `python manage.py collectstatic` después de cambios

## 🔧 Comandos de Verificación

```bash
# Verificar estructura
find static/ -type f | head -20

# Verificar duplicados
python tools/clean/audit_static.py --base static --out reports/audit_check.csv

# Verificar referencias rotas
python manage.py check --deploy
```
