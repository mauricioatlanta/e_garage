# 🔧 Solución: Tabla taller_kilometrajeregistro no existe

## ⚠️ Error

```
OperationalError: no such table: taller_kilometrajeregistro
```

**Causa:** Las migraciones no se han aplicado correctamente.

---

## ✅ Solución Completa

### 1. Resolver Conflicto de Migraciones

```bash
cd ~/apps/egarage/current
workon venv_egarage310

# Crear migración de merge
python manage.py makemigrations --merge

# Cuando pregunte, selecciona la opción 1 (crear merge automático)
```

### 2. Aplicar TODAS las Migraciones

```bash
# Aplicar migraciones (esto creará la tabla)
python manage.py migrate

# Verificar que se aplicaron
python manage.py showmigrations taller | grep -E "\[X\]|\[ \]"
```

### 3. Verificar que la Tabla Existe

```bash
# Verificar en la base de datos
python manage.py dbshell

# En SQLite shell:
.tables
# Debe aparecer: taller_kilometrajeregistro

# O verificar directamente:
.schema taller_kilometrajeregistro
```

### 4. Si la Tabla Aún No Existe

```bash
# Forzar creación de la migración específica
python manage.py makemigrations taller

# Aplicar solo la migración de KilometrajeRegistro
python manage.py migrate taller 0047
```

### 5. Reiniciar Servidor

```bash
# Reiniciar (PythonAnywhere)
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🚀 Comandos Completos (Todo en Uno)

```bash
cd ~/apps/egarage/current
workon venv_egarage310

# 1. Resolver conflicto
python manage.py makemigrations --merge
# Seleccionar opción 1

# 2. Aplicar migraciones
python manage.py migrate

# 3. Verificar migraciones aplicadas
python manage.py showmigrations taller

# 4. Verificar tabla existe
python manage.py dbshell
# .tables (debe mostrar taller_kilometrajeregistro)
# .quit

# 5. Reiniciar
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🔍 Verificación Post-Migración

### Verificar Migraciones Aplicadas:

```bash
python manage.py showmigrations taller | grep -E "0047|0048|0049"
```

Debe mostrar:
```
[X] 0047_kilometrajeregistro
[X] 0048_clientecredencial_clientetoken
[X] 0049_merge_... (si se creó)
```

### Verificar Tabla en Base de Datos:

```bash
python manage.py dbshell
```

```sql
-- En SQLite:
.tables
-- Debe aparecer: taller_kilometrajeregistro

-- Ver estructura:
.schema taller_kilometrajeregistro

-- Salir:
.quit
```

---

## ⚠️ Si Aún Hay Problemas

### Opción A: Aplicar Migración Específica

```bash
# Ver qué migraciones están pendientes
python manage.py showmigrations taller

# Aplicar migración específica
python manage.py migrate taller 0047_kilometrajeregistro
```

### Opción B: Forzar Recreación

```bash
# Si nada funciona, crear migración desde cero
python manage.py makemigrations taller --name create_kilometrajeregistro
python manage.py migrate
```

---

## ✅ Checklist

- [ ] `makemigrations --merge` ejecutado
- [ ] `migrate` ejecutado sin errores
- [ ] Tabla `taller_kilometrajeregistro` existe (verificado con dbshell)
- [ ] Servidor reiniciado
- [ ] URL `/reportes/kilometraje/recordatorios/` funciona

---

**¡Ejecuta `makemigrations --merge` y luego `migrate` para crear la tabla! 🚀**

