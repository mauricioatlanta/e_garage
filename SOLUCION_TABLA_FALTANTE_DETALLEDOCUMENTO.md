# 🔧 Solución: Error "no such table: taller_detalledocumento"

## 📋 Problema

Después de marcar la migración 0001 como aplicada (fake), la migración 0005 falla porque la tabla `taller_detalledocumento` no existe, aunque debería haber sido creada por la migración 0001.

## 🔍 Causa

La base de datos tiene algunas tablas de la migración 0001 (como `taller_categoriaservicio`) pero no todas. Al hacer `--fake` de la 0001, Django asumió que todas las tablas ya existían.

## ✅ SOLUCIÓN 1: Revertir y Aplicar Correctamente (Recomendada)

### Paso 1: Revertir el fake de la migración 0001

```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310

# Revertir el fake (marcar como no aplicada)
python manage.py migrate taller 0001 --fake-initial --fake
# O mejor, desmarcar manualmente:
python manage.py migrate taller zero --fake
```

### Paso 2: Aplicar la migración 0001 de verdad (solo creará las tablas que faltan)

```bash
# Intentar aplicar la 0001 de verdad
python manage.py migrate taller 0001
```

Si falla con "table already exists" para alguna tabla, puedes:
- Ignorar ese error específico
- O crear manualmente solo las tablas faltantes

### Paso 3: Continuar con el resto

```bash
python manage.py migrate
```

---

## ✅ SOLUCIÓN 2: Crear Tabla Faltante Manualmente

Si prefieres crear solo la tabla que falta:

### Paso 1: Verificar estructura de la tabla

```bash
python manage.py sqlmigrate taller 0001 | grep -A 50 "CREATE TABLE.*detalledocumento"
```

### Paso 2: Crear la tabla manualmente

```bash
python manage.py dbshell
```

Luego ejecutar el SQL que muestra `sqlmigrate` para crear la tabla `taller_detalledocumento`.

### Paso 3: Marcar migraciones como aplicadas

```bash
# Marcar 0001-0004 como aplicadas (fake)
python manage.py migrate taller 0004 --fake

# Aplicar desde 0005 en adelante
python manage.py migrate
```

---

## ✅ SOLUCIÓN 3: Aplicar Migraciones Específicas con Manejo de Errores

### Script Python para aplicar migraciones saltando errores de "tabla ya existe"

```python
# Crear archivo: fix_migrations.py
import subprocess
import sys

migrations = [
    "0001_initial_migration",
    "0002_alter_documento_tipo",
    "0003_convert_fac_bol_to_rec",
    "0004_documento_numero_documento_db",
]

for mig in migrations:
    print(f"Aplicando {mig}...")
    result = subprocess.run(
        ["python", "manage.py", "migrate", "taller", mig],
        capture_output=True,
        text=True
    )
    if "already exists" in result.stderr:
        print(f"  ⚠️  Tabla ya existe, marcando como aplicada...")
        subprocess.run(["python", "manage.py", "migrate", "taller", mig, "--fake"])
    elif result.returncode == 0:
        print(f"  ✅ {mig} aplicada correctamente")
    else:
        print(f"  ❌ Error en {mig}:")
        print(result.stderr)
        sys.exit(1)

print("\n✅ Aplicando migraciones restantes...")
subprocess.run(["python", "manage.py", "migrate"])
```

Ejecutar:
```bash
python fix_migrations.py
```

---

## ✅ SOLUCIÓN 4: Verificar y Crear Solo Tablas Faltantes (Más Segura)

### Paso 1: Verificar qué tablas existen

```bash
python manage.py dbshell
```

Luego:
```sql
.tables
.quit
```

### Paso 2: Ver qué tablas debería crear la migración 0001

```bash
python manage.py sqlmigrate taller 0001 | grep "CREATE TABLE" | grep taller_
```

### Paso 3: Comparar y crear las faltantes

Si falta `taller_detalledocumento`, obtener su SQL:

```bash
python manage.py sqlmigrate taller 0001 > migration_0001.sql
grep -A 30 "CREATE TABLE.*detalledocumento" migration_0001.sql
```

Luego ejecutar ese SQL en `dbshell`.

### Paso 4: Marcar migraciones como aplicadas

```bash
# Marcar hasta 0004 como aplicadas
python manage.py migrate taller 0004 --fake

# Aplicar desde 0005
python manage.py migrate
```

---

## 🚀 SOLUCIÓN RÁPIDA (Recomendada para este caso)

Ejecuta estos comandos en orden:

```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310

# 1. Ver qué tablas existen
python manage.py dbshell << EOF
.tables | grep taller
.quit
EOF

# 2. Obtener SQL de creación de detalledocumento
python manage.py sqlmigrate taller 0001 | grep -A 50 "CREATE TABLE.*detalledocumento" > create_detalle.sql

# 3. Si el archivo tiene contenido, crear la tabla manualmente
# (Revisar create_detalle.sql y ejecutar el SQL en dbshell)

# 4. Marcar migraciones 0001-0004 como aplicadas (fake)
python manage.py migrate taller 0004 --fake

# 5. Aplicar desde 0005 en adelante
python manage.py migrate
```

---

## 📝 Verificación Final

```bash
# Verificar que todas las tablas existen
python manage.py dbshell << EOF
.tables | grep -E "(detalle|categoria|documento)"
.quit
EOF

# Verificar estado de migraciones
python manage.py showmigrations taller | tail -10

# Verificar que no hay errores
python manage.py check
```

---

## ⚠️ IMPORTANTE

- **Siempre hacer backup antes de manipular la base de datos**
- **Verificar qué tablas realmente existen antes de crear nuevas**
- **Si hay datos importantes, no eliminar tablas existentes**

---

**¡Solución lista!** 🚀

