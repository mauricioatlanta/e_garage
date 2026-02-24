# 🔧 Solución: Agregar Columna ha_usado_prueba

## ❌ Problema

```
sqlite3.OperationalError: no such column: taller_empresa.ha_usado_prueba
```

La columna `ha_usado_prueba` está definida en el modelo pero no existe en la base de datos del servidor.

## ✅ Solución Rápida

### Opción 1: Usar el Script Automático (Recomendado)

```bash
cd /home/atlantareciclajes/apps/egarage/current
python3.10 crear_migracion_ha_usado_prueba.py
```

Este script:
- Verifica si la columna existe
- La agrega directamente a la base de datos si no existe
- Verifica que se agregó correctamente

### Opción 2: Agregar Manualmente con SQL

```bash
python3.10 manage.py shell
```

```python
from django.db import connection

cursor = connection.cursor()

# Para SQLite
cursor.execute("""
    ALTER TABLE taller_empresa 
    ADD COLUMN ha_usado_prueba BOOLEAN DEFAULT 0 NOT NULL
""")

# Verificar
cursor.execute("PRAGMA table_info(taller_empresa)")
columns = cursor.fetchall()
for col in columns:
    if 'ha_usado_prueba' in col:
        print("✅ Columna agregada")
        break
```

### Opción 3: Crear Migración Normal

```bash
# Crear migración
python3.10 manage.py makemigrations taller

# Aplicar
python3.10 manage.py migrate
```

**⚠️ NOTA**: Esto solo funciona si no hay otros problemas de migraciones.

## 🔍 Verificar

Después de agregar la columna:

```bash
python3.10 diagnostico_registro.py
```

Debería funcionar sin el error de la columna faltante.

## 📋 Checklist

- [ ] Columna `ha_usado_prueba` agregada a la base de datos
- [ ] Script de diagnóstico funciona sin errores
- [ ] Registro de usuarios funciona correctamente

---

**Última actualización**: Diciembre 2024
