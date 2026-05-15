# 🔧 Fix: Error de Migraciones en el Servidor

## ❌ Error Detectado

```
django.db.utils.OperationalError: no such column: taller_empresa.ha_usado_prueba
```

## 🔍 Causa

Falta la columna `ha_usado_prueba` en la tabla `taller_empresa`. Esto indica que las migraciones no están aplicadas en el servidor.

## ✅ Solución

### Paso 1: Verificar Migraciones Pendientes

```bash
cd /home/atlantareciclajes/apps/egarage/current
python3.10 manage.py showmigrations taller
```

Esto mostrará qué migraciones están aplicadas (✓) y cuáles no (✗).

### Paso 2: Aplicar Migraciones

```bash
python3.10 manage.py migrate
```

Esto aplicará todas las migraciones pendientes, incluyendo la que crea la columna `ha_usado_prueba`.

### Paso 3: Verificar que se Aplicaron

```bash
python3.10 manage.py showmigrations taller
```

Todas las migraciones deberían mostrar ✓.

### Paso 4: Probar el Diagnóstico de Nuevo

```bash
python3.10 diagnostico_registro.py
```

Ahora debería funcionar sin errores.

## ⚠️ Importante

**NO ejecutes `makemigrations` en el servidor**. Solo ejecuta `migrate` para aplicar las migraciones que ya existen en el código.

## 🔍 Verificar Estado de la Base de Datos

Si quieres verificar el estado actual:

```bash
python3.10 manage.py shell
```

```python
from django.db import connection

# Ver estructura de la tabla
cursor = connection.cursor()
cursor.execute("PRAGMA table_info(taller_empresa)")
columns = cursor.fetchall()
for col in columns:
    print(col)
```

O si usas MySQL:

```python
from django.db import connection

cursor = connection.cursor()
cursor.execute("DESCRIBE taller_empresa")
columns = cursor.fetchall()
for col in columns:
    print(col)
```

## 📋 Checklist

- [ ] Migraciones pendientes identificadas
- [ ] Migraciones aplicadas (`python3.10 manage.py migrate`)
- [ ] Script de diagnóstico funciona sin errores
- [ ] Registro de usuarios funciona correctamente

---

**Última actualización**: Diciembre 2024
