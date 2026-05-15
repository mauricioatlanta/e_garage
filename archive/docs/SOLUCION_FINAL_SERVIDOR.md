# Solución Final - Servidor

## Problema: Git Pull sigue bloqueado

El archivo `.aider.tags.cache.v4/cache.db` se recreó o no se eliminó correctamente.

## Solución Definitiva:

### Paso 1: Forzar eliminación y hacer pull

```bash
# Eliminar completamente el directorio de cache
rm -rf .aider.tags.cache.v4/

# Agregar a .gitignore para que no cause problemas en el futuro
echo ".aider.tags.cache.v4/" >> .gitignore
git add .gitignore

# Hacer stash de cualquier cambio pendiente
git stash

# Ahora hacer pull
git pull

# Si hay conflictos, resolverlos
```

### Paso 2: Si el pull sigue fallando, usar reset

```bash
# Guardar cambios importantes primero (si los hay)
git stash

# Forzar actualización desde el remoto
git fetch origin
git reset --hard origin/main
```

### Paso 3: Verificar que la migración 0056 existe

```bash
# Ver todas las migraciones
ls -la taller/migrations/ | grep 0056

# Debe mostrar: 0056_add_company_settings_fields.py
```

### Paso 4: Aplicar la migración

```bash
python manage.py migrate taller 0056
```

### Paso 5: Reiniciar

```bash
touch gestion_taller/wsgi.py
```

---

## Comando Todo-en-Uno (si no hay cambios importantes):

```bash
# ⚠️ ADVERTENCIA: Esto descartará TODOS los cambios locales
# Solo usar si no hay cambios importantes que conservar

rm -rf .aider.tags.cache.v4/
git fetch origin
git reset --hard origin/main
python manage.py migrate taller 0056
touch gestion_taller/wsgi.py
```
