# Solución: Error AppRegistryNotReady en Servidor

## Problemas Detectados:

1. **Migración 0056 no encontrada** aunque git pull la trajo
2. **Error AppRegistryNotReady** impide ejecutar cualquier comando de Django

## Diagnóstico:

El error `AppRegistryNotReady` ocurre cuando Django intenta cargar settings y hay un problema de importación circular o configuración. Esto impide ejecutar CUALQUIER comando de Django.

## Solución Paso a Paso:

### Paso 1: Verificar estructura del proyecto

```bash
# Verificar dónde está la migración
find . -name "0056_add_company_settings_fields.py" -type f

# Verificar estructura de directorios
ls -la taller/migrations/ | grep 005

# Verificar si hay un problema con la ruta
pwd
ls -la | grep taller
```

### Paso 2: Verificar el error de Django

El error sugiere un problema con la importación de `allauth.account.middleware`. Esto puede ser:

1. **Problema de importación circular** en settings.py
2. **Problema con la versión de django-allauth**
3. **Problema con la configuración de INSTALLED_APPS**

### Paso 3: Intentar aplicar migración directamente con SQL

Si Django no puede iniciar, podemos aplicar la migración manualmente:

```bash
# Ver el SQL que se ejecutaría
python manage.py sqlmigrate taller 0056 2>/dev/null || echo "No se puede ejecutar Django"

# Si no funciona, aplicar directamente con SQLite
sqlite3 db.sqlite3 <<EOF
ALTER TABLE taller_companysettings ADD COLUMN terms_and_conditions text DEFAULT '';
ALTER TABLE taller_companysettings ADD COLUMN apply_tax_by_default bool DEFAULT 1;
ALTER TABLE taller_companysettings ADD COLUMN separate_by_technician bool DEFAULT 0;
ALTER TABLE taller_companysettings ADD COLUMN tax_rate decimal(5,2) DEFAULT 19.00;
EOF
```

### Paso 4: Marcar migración como aplicada

```bash
# Si aplicaste manualmente, marcar como aplicada
python manage.py migrate taller 0056 --fake 2>/dev/null || echo "Django no funciona"
```

---

## Solución Alternativa: Aplicar Migración Manualmente

Si Django no puede iniciar, podemos aplicar la migración directamente en la base de datos:

```bash
# 1. Hacer backup
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# 2. Aplicar cambios directamente (SQLite)
sqlite3 db.sqlite3 <<'EOF'
-- Agregar columnas faltantes
ALTER TABLE taller_companysettings ADD COLUMN terms_and_conditions text DEFAULT '';
ALTER TABLE taller_companysettings ADD COLUMN apply_tax_by_default integer DEFAULT 1;
ALTER TABLE taller_companysettings ADD COLUMN separate_by_technician integer DEFAULT 0;
ALTER TABLE taller_companysettings ADD COLUMN tax_rate text DEFAULT '19.00';
EOF

# 3. Marcar migración como aplicada (cuando Django funcione)
# python manage.py migrate taller 0056 --fake
```

---

## Resolver el Error de Django

El error `AppRegistryNotReady` puede ser por:

1. **Importación circular en settings.py**
2. **Problema con django-allauth**

Verificar:

```bash
# Verificar versión de django-allauth
pip show django-allauth

# Verificar si hay imports problemáticos en settings.py
grep -n "from.*models import" gestion_taller/settings.py
```

---

## Comandos de Diagnóstico:

```bash
# 1. Verificar estructura
find . -name "0056*.py" -type f

# 2. Verificar si la migración está en el lugar correcto
ls -la taller/migrations/005*.py

# 3. Verificar error de Django
python -c "import django; django.setup()" 2>&1 | head -20

# 4. Verificar imports de settings
python -c "import sys; sys.path.insert(0, '.'); from gestion_taller import settings" 2>&1 | head -20
```
