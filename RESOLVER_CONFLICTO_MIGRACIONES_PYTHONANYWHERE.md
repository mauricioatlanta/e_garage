# 🔧 Resolver Conflicto de Migraciones en PythonAnywhere

## ⚠️ Error

```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph: 
(0047_alter_detalledocumento_tipo_item, 0048_clientecredencial_clientetoken in taller).

To fix them run 'python manage.py makemigrations --merge'
```

---

## ✅ Solución

### 1. Crear Migración de Merge

```bash
# En PythonAnywhere
cd ~/apps/egarage/current
workon venv_egarage310

# Crear migración de merge
python manage.py makemigrations --merge
```

Django te preguntará qué hacer. Selecciona:
- **Opción 1** para crear la migración de merge automáticamente

### 2. Aplicar Todas las Migraciones

```bash
# Aplicar migraciones (incluyendo la de merge)
python manage.py migrate
```

### 3. Continuar con el Resto de los Pasos

```bash
# Forzar actualización del template
git checkout HEAD -- templates/taller/reportes/reportes.html

# Limpiar cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# Recolectar estáticos
python manage.py collectstatic --noinput

# Reiniciar servidor
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🚀 Comandos Completos (Todo en Uno)

```bash
cd ~/apps/egarage/current
workon venv_egarage310

# Resolver conflicto de migraciones
python manage.py makemigrations --merge
# Seleccionar opción 1 cuando pregunte

# Aplicar migraciones
python manage.py migrate

# Forzar template
git checkout HEAD -- templates/taller/reportes/reportes.html

# Limpiar cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# Estáticos
python manage.py collectstatic --noinput

# Reiniciar
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## ✅ Verificación

```bash
# Verificar que las migraciones están aplicadas
python manage.py showmigrations taller

# Verificar template
grep "kilometraje/recordatorios" templates/taller/reportes/reportes.html
```

---

**¡Ejecuta `python manage.py makemigrations --merge` y luego `migrate`! 🚀**

