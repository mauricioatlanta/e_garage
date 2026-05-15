# 🔧 Solución: Error de Migraciones 0009 y 0010

## ❌ Error

```
django.db.migrations.exceptions.NodeNotFoundError: 
Migration taller.0010_migrate_tecnico_roles dependencies reference 
nonexistent parent node ('taller', '0009_alter_tecnico_rol')
```

## 🔍 Causa

La migración `0010` depende de `0009`, pero `0009` no está aplicada (o marcada como aplicada) en el servidor.

## ✅ Soluciones

### Opción 1: Aplicar Migraciones en Orden (Recomendado)

```bash
cd /home/atlantareciclajes/apps/egarage/current

# Ver estado actual
python3.10 manage.py showmigrations taller

# Aplicar migraciones faltantes
python3.10 manage.py migrate taller 0009
python3.10 manage.py migrate taller 0010

# O aplicar todas
python3.10 manage.py migrate
```

### Opción 2: Marcar Migración como Aplicada (Si los cambios ya existen)

Si la migración `0009` ya tiene sus cambios aplicados en la base de datos pero Django no lo sabe:

```bash
# Marcar como aplicada sin ejecutarla
python3.10 manage.py migrate --fake taller 0009

# Luego aplicar las siguientes
python3.10 manage.py migrate
```

### Opción 3: Usar el Script de Fix

```bash
python3.10 fix_migraciones_servidor.py
```

Este script:
- Verifica el estado de las migraciones
- Verifica si la columna `ha_usado_prueba` existe
- Intenta aplicar las migraciones
- Muestra el estado final

## 🔍 Verificar Estado

### Ver qué migraciones están aplicadas:

```bash
python3.10 manage.py showmigrations taller
```

Deberías ver:
- `✓` para migraciones aplicadas
- `✗` para migraciones pendientes

### Verificar columna en la base de datos:

```bash
python3.10 manage.py shell
```

```python
from django.db import connection

cursor = connection.cursor()
# Para SQLite
cursor.execute("PRAGMA table_info(taller_empresa)")
# Para MySQL
# cursor.execute("DESCRIBE taller_empresa")

columns = cursor.fetchall()
for col in columns:
    print(col)
```

## ⚠️ Importante

**NO ejecutes `makemigrations` en el servidor**. Solo usa `migrate` para aplicar las migraciones que ya existen en el código.

## 📋 Checklist

- [ ] Estado de migraciones verificado
- [ ] Migración 0009 aplicada o marcada como aplicada
- [ ] Migración 0010 aplicada
- [ ] Columna `ha_usado_prueba` existe en la base de datos
- [ ] Script de diagnóstico funciona sin errores

---

**Última actualización**: Diciembre 2024
