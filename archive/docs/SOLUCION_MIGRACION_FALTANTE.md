# Solución: Migración 0056 No Encontrada

## Problema:
La migración 0056 no se encuentra en `taller/migrations/` aunque git pull la trajo.

## Posibles Causas:
1. El archivo está en otra ubicación
2. Hay un problema con la estructura del proyecto `deploy_atlantareciclajes`
3. El archivo no se copió correctamente

## Solución:

### Paso 1: Verificar todas las migraciones existentes

```bash
# Ver todas las migraciones
ls -la taller/migrations/*.py | tail -10

# Ver el número más alto de migración
ls -1 taller/migrations/*.py | sort -V | tail -5
```

### Paso 2: Verificar si el archivo está en el repositorio pero no en el directorio

```bash
# Ver qué archivos trajo el git pull
git log --oneline -1
git show --name-only HEAD | grep 0056

# Ver si el archivo existe en el índice de git
git ls-files | grep 0056
```

### Paso 3: Si el archivo no está, copiarlo manualmente

Si el archivo está en git pero no en el sistema de archivos:

```bash
# Forzar checkout del archivo
git checkout HEAD -- taller/migrations/0056_add_company_settings_fields.py

# Verificar que existe ahora
ls -la taller/migrations/0056*.py
```

### Paso 4: Crear el archivo manualmente si no existe

Si el archivo no está en git, crearlo manualmente:

```bash
cat > taller/migrations/0056_add_company_settings_fields.py <<'EOF'
# Generated manually to add missing CompanySettings fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0055_remove_logauditoria_empresa_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="companysettings",
            name="terms_and_conditions",
            field=models.TextField(
                blank=True,
                help_text="Términos que aparecen en contratos y documentos",
                verbose_name="Términos y condiciones",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="apply_tax_by_default",
            field=models.BooleanField(
                default=True,
                help_text="Aplicar impuesto automáticamente en nuevos documentos",
                verbose_name="Aplicar impuesto por defecto",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="separate_by_technician",
            field=models.BooleanField(
                default=False,
                help_text="Mostrar reportes separados por técnico",
                verbose_name="Separar por técnico",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=19.0,
                help_text="Tasa de impuesto por defecto (ej: 19.00 para Chile, 0.00 para USA)",
                max_digits=5,
                verbose_name="Tasa de impuesto",
            ),
        ),
    ]
EOF
```

### Paso 5: Aplicar la migración manualmente (si Django no funciona)

Como Django tiene un error, aplicar directamente en SQLite:

```bash
# Backup
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# Aplicar cambios
sqlite3 db.sqlite3 <<'EOF'
ALTER TABLE taller_companysettings ADD COLUMN terms_and_conditions text DEFAULT '';
ALTER TABLE taller_companysettings ADD COLUMN apply_tax_by_default integer DEFAULT 1;
ALTER TABLE taller_companysettings ADD COLUMN separate_by_technician integer DEFAULT 0;
ALTER TABLE taller_companysettings ADD COLUMN tax_rate text DEFAULT '19.00';
EOF
```
