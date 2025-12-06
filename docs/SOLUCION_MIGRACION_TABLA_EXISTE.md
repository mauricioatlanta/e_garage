# Solución: Error "table already exists" en Migraciones

## Problema
```
sqlite3.OperationalError: table "taller_categoriaservicio" already exists
```

## Causa
La base de datos ya tiene las tablas creadas, pero Django no tiene registradas las migraciones iniciales en `django_migrations`.

## Soluciones

### Opción 1: Usar --fake-initial (Recomendada)
```bash
python manage.py migrate --fake-initial
```

Esto marca las migraciones iniciales como aplicadas si las tablas ya existen, sin intentar crearlas de nuevo.

### Opción 2: Marcar migración específica como fake
```bash
python manage.py migrate taller 0001_initial_migration --fake
```

### Opción 3: Verificar estado de migraciones
```bash
# Ver qué migraciones están aplicadas
python manage.py showmigrations taller

# Ver qué tablas existen en la BD
python manage.py dbshell
.tables
```

### Opción 4: Si necesitas resetear (CUIDADO: pierde datos)
```bash
# Solo si estás seguro de perder datos
python manage.py migrate taller zero
python manage.py migrate
```

## Comando Recomendado para el Servidor

```bash
# 1. Verificar estado actual
python manage.py showmigrations taller

# 2. Aplicar con fake-initial
python manage.py migrate --fake-initial

# 3. Aplicar migraciones pendientes
python manage.py migrate
```

## Nota Importante
- `--fake-initial` solo funciona si las tablas ya existen y coinciden con el estado esperado por la migración inicial
- Si hay diferencias entre las tablas existentes y lo que espera la migración, puede causar problemas
- Siempre hacer backup antes de ejecutar migraciones en producción












