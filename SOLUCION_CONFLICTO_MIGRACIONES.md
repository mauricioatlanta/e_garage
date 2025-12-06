# 🔧 Solución: Conflicto de Migraciones en Servidor

## ⚠️ Problema

```
error: Your local changes to the following files would be overwritten by merge:
        taller/migrations/0011_improve_empresa_model_robust.py
```

---

## ✅ Solución Paso a Paso

### 1. Ver qué cambios locales tienes

```bash
# En el servidor (PythonAnywhere)
cd ~/apps/egarage/current

# Ver qué cambios hay en el archivo
git diff taller/migrations/0011_improve_empresa_model_robust.py
```

### 2. Opción A: Descartar cambios locales (RECOMENDADO)

```bash
# Si los cambios locales no son importantes, descartarlos
git checkout -- taller/migrations/0011_improve_empresa_model_robust.py

# Luego hacer pull
git pull origin main
```

### 3. Opción B: Guardar cambios locales temporalmente

```bash
# Guardar cambios locales en stash
git stash

# Hacer pull
git pull origin main

# Si necesitas los cambios después:
# git stash pop
```

### 4. Opción C: Hacer commit de los cambios locales

```bash
# Si los cambios locales son importantes
git add taller/migrations/0011_improve_empresa_model_robust.py
git commit -m "Fix local: migración 0011"

# Luego hacer pull (puede haber merge)
git pull origin main

# Si hay conflictos, resolverlos y hacer commit
```

---

## 🚀 Comandos Completos para PythonAnywhere

```bash
# 1. Ir al proyecto
cd ~/apps/egarage/current

# 2. Activar entorno virtual
workon venv_egarage310

# 3. Resolver conflicto (descartar cambios locales)
git checkout -- taller/migrations/0011_improve_empresa_model_robust.py

# 4. Actualizar código
git pull origin main

# 5. Crear migraciones nuevas
python manage.py makemigrations

# 6. Aplicar migraciones
python manage.py migrate

# 7. Limpiar cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null

# 8. Forzar actualización del template
git checkout HEAD -- templates/taller/reportes/reportes.html

# 9. Recolectar estáticos
python manage.py collectstatic --noinput

# 10. Reiniciar servidor (PythonAnywhere)
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🔍 Verificar que Funcionó

1. **Verificar template:**
   ```bash
   grep "kilometraje/recordatorios" templates/taller/reportes/reportes.html
   ```

2. **Acceder a:** `https://atlantareciclajes.pythonanywhere.com/reportes/`
   - Debe aparecer "Recordatorios de Mantenimiento"

---

## ⚠️ Nota sobre PythonAnywhere

En PythonAnywhere:
- **NO hay sudo** - es normal
- **Reiniciar servidor:** `touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py`
- **No uses systemctl** - no está disponible

---

**¡Ejecuta estos comandos y debería funcionar! 🚀**

