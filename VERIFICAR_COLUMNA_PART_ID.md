# 🔍 VERIFICAR: Columna part_id en Base de Datos

## ✅ Estado Actual

- ✅ Migración `0028_catalogo_i18n_precios` está aplicada: `[X]`
- ❌ Error persiste: `no such column: taller_linearepuesto.part_id`

## 🔍 Diagnóstico

Si la migración está aplicada pero el error persiste, puede ser:
1. La columna no se creó correctamente
2. Hay múltiples bases de datos o releases
3. El schema está desincronizado

## ✅ Comandos de Verificación

### **Paso 1: Verificar que la columna existe**

En la Bash Console del servidor:

```bash
cd /home/atlantareciclajes/apps/egarage/current

# Verificar schema de la tabla
sqlite3 db.sqlite3 ".schema taller_linearepuesto" | grep -i part
```

**Debería mostrar**:
```sql
"part_id" INTEGER REFERENCES "taller_part" ("id") DEFERRABLE INITIALLY DEFERRED
```

### **Paso 2: Verificar que la tabla Part existe**

```bash
sqlite3 db.sqlite3 ".tables" | grep -i part
```

**Debería mostrar**:
```
taller_part
taller_parti18n
taller_partprice
```

### **Paso 3: Verificar columnas de la tabla directamente**

```bash
sqlite3 db.sqlite3 "PRAGMA table_info(taller_linearepuesto);" | grep -i part
```

**Debería mostrar**:
```
5|part_id|INTEGER|0||1|taller_part(id)
```

### **Paso 4: Verificar qué release está activo**

```bash
# Verificar el directorio actual
pwd

# Verificar si hay symlink
ls -la /home/atlantareciclajes/apps/egarage/current

# Verificar la base de datos que se está usando
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['NAME'])"
```

## 🔧 Soluciones Posibles

### **Solución 1: Re-ejecutar la migración específica**

Si la columna no existe pero la migración está marcada como aplicada:

```bash
# 1. Marcar la migración como no aplicada (solo si es necesario)
python manage.py migrate taller 0027 --fake

# 2. Re-ejecutar la migración
python manage.py migrate taller 0028

# 3. Verificar
sqlite3 db.sqlite3 ".schema taller_linearepuesto" | grep -i part
```

### **Solución 2: Crear la columna manualmente (solo si es necesario)**

⚠️ **Solo usar si la migración no funciona**:

```bash
sqlite3 db.sqlite3 << 'EOF'
-- Verificar que la tabla Part existe
SELECT name FROM sqlite_master WHERE type='table' AND name='taller_part';

-- Agregar la columna si no existe
ALTER TABLE taller_linearepuesto ADD COLUMN part_id INTEGER REFERENCES taller_part(id);

-- Verificar que se creó
.schema taller_linearepuesto
EOF
```

### **Solución 3: Verificar múltiples releases**

Si hay múltiples releases, verificar cuál está activo:

```bash
# Ver releases disponibles
ls -la /home/atlantareciclajes/apps/egarage/releases/

# Verificar el symlink
ls -la /home/atlantareciclajes/apps/egarage/current

# Verificar la base de datos del release activo
cd /home/atlantareciclajes/apps/egarage/current
python manage.py shell -c "from django.conf import settings; import os; print('DB:', os.path.abspath(settings.DATABASES['default']['NAME']))"
```

## 📋 Información a Recopilar

Ejecuta estos comandos y comparte los resultados:

```bash
cd /home/atlantareciclajes/apps/egarage/current

# 1. Verificar schema
echo "=== SCHEMA ==="
sqlite3 db.sqlite3 ".schema taller_linearepuesto" | grep -i part

# 2. Verificar columnas
echo "=== COLUMNAS ==="
sqlite3 db.sqlite3 "PRAGMA table_info(taller_linearepuesto);" | grep -i part

# 3. Verificar tabla Part
echo "=== TABLA PART ==="
sqlite3 db.sqlite3 ".tables" | grep -i part

# 4. Verificar migraciones
echo "=== MIGRACIONES ==="
python manage.py showmigrations taller | grep "0028"

# 5. Verificar base de datos activa
echo "=== BASE DE DATOS ==="
python manage.py shell -c "from django.conf import settings; import os; print(os.path.abspath(settings.DATABASES['default']['NAME']))"
```

---

**Fecha**: 2025-11-25
**Problema**: Migración aplicada pero columna no existe
**Siguiente paso**: Verificar schema de la base de datos

