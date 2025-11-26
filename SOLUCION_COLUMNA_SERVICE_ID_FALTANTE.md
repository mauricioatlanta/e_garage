# 🔧 Solución: Columna `service_id` faltante en `taller_lineaservicio`

## 📋 Problema

Error al acceder a `/us/centro-operaciones-espacial/`:
```
OperationalError: no such column: taller_lineaservicio.service_id
```

## 🔍 Causa

El modelo `LineaServicio` tiene un campo `service` (ForeignKey a "taller.Service"), pero la columna `service_id` no existe en la base de datos. Esto significa que hay una migración pendiente que agrega este campo.

## ✅ SOLUCIÓN

### Opción 1: Crear la columna manualmente (Rápida)

```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310

# Agregar la columna service_id a la tabla
python manage.py dbshell << 'SQL'
ALTER TABLE taller_lineaservicio 
ADD COLUMN service_id INTEGER NULL 
REFERENCES taller_service(id) 
DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX IF NOT EXISTS taller_lineaservicio_service_id_idx 
ON taller_lineaservicio(service_id);
.quit
SQL

# Verificar que se creó
python manage.py dbshell << EOF
.schema taller_lineaservicio | grep service
.quit
EOF
```

### Opción 2: Crear y aplicar migración (Recomendada)

```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310

# Crear migración para agregar el campo
python manage.py makemigrations taller

# Aplicar la migración
python manage.py migrate taller

# Verificar
python manage.py check
```

### Opción 3: Verificar si hay migraciones pendientes

```bash
# Ver todas las migraciones
python manage.py showmigrations taller

# Si hay alguna pendiente que agregue service_id, aplicarla
python manage.py migrate
```

## 🔍 Verificación

Después de aplicar la solución:

1. **Verificar que la columna existe:**
   ```bash
   python manage.py dbshell << EOF
   .schema taller_lineaservicio
   .quit
   EOF
   ```

2. **Probar el sitio:**
   - Abrir: https://www.egarage.cl/us/centro-operaciones-espacial/
   - Debe cargar sin errores

## 📝 Nota

El modelo `LineaServicio` tiene dos campos relacionados con servicios:
- `servicio` (ForeignKey a "taller.Servicio") - Legacy
- `service` (ForeignKey a "taller.Service") - Nuevo con I18N

La columna faltante es `service_id` (del campo `service`).

---

**¡Solución lista!** 🚀

