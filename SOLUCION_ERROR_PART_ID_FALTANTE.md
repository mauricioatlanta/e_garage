# 🔧 SOLUCIÓN: Error `no such column: taller_linearepuesto.part_id`

## ❌ Error

```
OperationalError at /cl/documentos/
no such column: taller_linearepuesto.part_id
```

## 🔍 Causa

La migración `0028_catalogo_i18n_precios.py` que agrega el campo `part` a la tabla `taller_linearepuesto` **no se ha ejecutado en el servidor**.

Esta migración fue creada el **2025-11-11** y agrega:
- El modelo `Part` (catálogo de repuestos con I18N)
- El campo `part` (ForeignKey) a `LineaRepuesto`
- El modelo `Service` (catálogo de servicios con I18N)
- El campo `service` (ForeignKey) a `LineaServicio`
- Modelos relacionados: `PartI18N`, `ServiceI18N`, `PartPrice`, `ServicePrice`, `TaxPolicy`

## ✅ Solución: Ejecutar Migraciones Pendientes

### **Paso 1: Verificar Migraciones Pendientes**

En la **Bash Console del servidor**:

```bash
cd /home/atlantareciclajes/apps/egarage/current
python manage.py showmigrations taller
```

**Busca migraciones marcadas con `[ ]` (sin X)**. Deberías ver algo como:

```
taller
 [X] 0001_initial_migration
 [X] 0002_alter_documento_tipo
 ...
 [ ] 0028_catalogo_i18n_precios  ← ESTA NO ESTÁ APLICADA
 [X] 0029_add_use_address_v2_flag
 ...
```

### **Paso 2: Ejecutar Migraciones**

**⚠️ IMPORTANTE: Hacer backup de la base de datos antes de ejecutar migraciones**

```bash
# 1. Backup de la base de datos
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# 2. Verificar qué migraciones se van a ejecutar
python manage.py migrate --plan

# 3. Ejecutar las migraciones
python manage.py migrate taller

# 4. Verificar que se aplicaron correctamente
python manage.py showmigrations taller | grep "0028"
```

**Debería mostrar**:
```
 [X] 0028_catalogo_i18n_precios
```

### **Paso 3: Verificar que la Columna Existe**

```bash
# Verificar estructura de la tabla
sqlite3 db.sqlite3 ".schema taller_linearepuesto" | grep -i part
```

**Debería mostrar**:
```sql
"part_id" INTEGER REFERENCES "taller_part" ("id") DEFERRABLE INITIALLY DEFERRED
```

### **Paso 4: Recargar Aplicación**

- PythonAnywhere: Pestaña "Web" → Click "Reload"
- Otro servidor: Reiniciar servicio Django/Gunicorn/uWSGI

## 🔍 Verificación Adicional

### **Verificar que el Modelo Part Existe**

```bash
python manage.py shell
```

En el shell de Python:
```python
from taller.models import Part
print("Modelo Part existe:", Part.objects.count(), "registros")
```

### **Verificar que la Vista Funciona**

Después de ejecutar las migraciones:
1. Ir a: `https://www.egarage.cl/cl/documentos/`
2. Debe cargar sin errores
3. No debe mostrar el error `no such column: taller_linearepuesto.part_id`

## 📋 Migraciones Relacionadas

La migración `0028_catalogo_i18n_precios.py` crea:

1. **Modelo `Part`**: Catálogo de repuestos con I18N
2. **Modelo `PartI18N`**: Nombres de repuestos en múltiples idiomas
3. **Modelo `Service`**: Catálogo de servicios con I18N
4. **Modelo `ServiceI18N`**: Nombres de servicios en múltiples idiomas
5. **Modelo `PartPrice`**: Precios de repuestos por empresa/moneda
6. **Modelo `ServicePrice`**: Precios de servicios por empresa/moneda
7. **Modelo `TaxPolicy`**: Políticas de impuestos por país/estado/ciudad
8. **Campo `part`** en `LineaRepuesto`: FK opcional al catálogo nuevo
9. **Campo `service`** en `LineaServicio`: FK opcional al catálogo nuevo

## ⚠️ Notas Importantes

1. **Backup**: Siempre hacer backup antes de ejecutar migraciones en producción
2. **Tiempo**: Esta migración puede tardar varios minutos si hay muchos documentos
3. **Compatibilidad**: El campo `part` es opcional (`null=True, blank=True`), así que los documentos existentes seguirán funcionando
4. **Legacy**: El campo `repuesto` (legacy) sigue funcionando, pero se recomienda migrar a `part`

## 🐛 Si Hay Errores Durante la Migración

### **Error: "table already exists"**
```bash
# Verificar si las tablas ya existen
sqlite3 db.sqlite3 ".tables" | grep -i part
```

### **Error: "column already exists"**
```bash
# Verificar si la columna ya existe
sqlite3 db.sqlite3 ".schema taller_linearepuesto" | grep -i part
```

### **Error: "foreign key constraint failed"**
- Verificar que el modelo `Part` existe
- Verificar que hay datos válidos en `taller_part`

## ✅ Verificación Final

Después de ejecutar las migraciones:

1. ✅ `python manage.py showmigrations taller` muestra `[X] 0028_catalogo_i18n_precios`
2. ✅ `sqlite3 db.sqlite3 ".schema taller_linearepuesto"` muestra `part_id`
3. ✅ `https://www.egarage.cl/cl/documentos/` carga sin errores
4. ✅ No aparece el error `no such column: taller_linearepuesto.part_id`

---

**Fecha de creación**: 2025-11-25
**Migración requerida**: `0028_catalogo_i18n_precios.py`
**Tiempo estimado**: 5-15 minutos (depende del tamaño de la base de datos)

