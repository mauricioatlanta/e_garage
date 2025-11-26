# 🔧 SOLUCIÓN: Agregar Columna part_id Manualmente

## ✅ Diagnóstico Confirmado

- ❌ **Columna `part_id` NO existe** en `taller_linearepuesto`
- ✅ **Tabla `taller_part` SÍ existe**
- ✅ **Migración marcada como aplicada** pero columna no se creó
- ✅ **Base de datos**: `/home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg/db.sqlite3`

## 🔧 Solución: Agregar Columna Manualmente

### **Paso 1: Backup de la Base de Datos**

```bash
cd /home/atlantareciclajes/apps/egarage/current
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

### **Paso 2: Verificar que la Tabla Part Existe**

```bash
sqlite3 db.sqlite3 "SELECT name FROM sqlite_master WHERE type='table' AND name='taller_part';"
```

**Debería mostrar**: `taller_part`

### **Paso 3: Agregar la Columna part_id**

```bash
sqlite3 db.sqlite3 << 'EOF'
-- Agregar la columna part_id
ALTER TABLE taller_linearepuesto ADD COLUMN part_id INTEGER REFERENCES taller_part(id);

-- Verificar que se creó
.schema taller_linearepuesto
EOF
```

### **Paso 4: Verificar que la Columna se Creó**

```bash
sqlite3 db.sqlite3 "PRAGMA table_info(taller_linearepuesto);" | grep -i part
```

**Debería mostrar**:
```
10|part_id|INTEGER|0||0|taller_part(id)
```

O verificar con:
```bash
sqlite3 db.sqlite3 ".schema taller_linearepuesto" | grep -i part
```

**Debería mostrar**:
```sql
"part_id" INTEGER REFERENCES "taller_part" ("id")
```

### **Paso 5: Recargar Aplicación**

- PythonAnywhere: Pestaña "Web" → Click "Reload"

## ✅ Verificación Final

Después de agregar la columna:

1. ✅ `sqlite3 db.sqlite3 "PRAGMA table_info(taller_linearepuesto);" | grep part` muestra `part_id`
2. ✅ `https://www.egarage.cl/us/documentos/` carga sin errores
3. ✅ `https://www.egarage.cl/cl/documentos/` carga sin errores
4. ✅ No aparece el error `no such column: taller_linearepuesto.part_id`

## 🔍 Comandos Completos (Copia y Pega)

```bash
cd /home/atlantareciclajes/apps/egarage/current

# Backup
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# Verificar tabla Part
sqlite3 db.sqlite3 "SELECT name FROM sqlite_master WHERE type='table' AND name='taller_part';"

# Agregar columna
sqlite3 db.sqlite3 "ALTER TABLE taller_linearepuesto ADD COLUMN part_id INTEGER REFERENCES taller_part(id);"

# Verificar
sqlite3 db.sqlite3 "PRAGMA table_info(taller_linearepuesto);" | grep -i part
```

---

**Fecha**: 2025-11-25
**Problema**: Columna part_id no existe aunque migración está aplicada
**Solución**: Agregar columna manualmente con ALTER TABLE

