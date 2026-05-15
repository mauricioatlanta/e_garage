# Solución Completa para el Servidor

## Problemas Detectados:

1. **Git Pull bloqueado** por archivo de cache no rastreado
2. **Archivo `empresa.py` desactualizado** - falta imports y tiene estructura antigua

## Solución Paso a Paso:

### Paso 1: Resolver el problema de Git

El archivo `.aider.tags.cache.v4/cache.db` no está en git pero tiene cambios. Opciones:

```bash
# Opción A: Agregar a .gitignore y hacer stash
echo ".aider.tags.cache.v4/" >> .gitignore
git add .gitignore
git stash
git pull
git stash pop

# Opción B: Eliminar el archivo de cache (más simple)
rm -rf .aider.tags.cache.v4/
git pull
```

### Paso 2: Verificar que el pull trajo el archivo correcto

```bash
# Verificar que empresa.py tiene los imports correctos
head -15 taller/models/empresa.py

# Debe mostrar algo como:
# from datetime import timedelta
# from decimal import Decimal
# from math import ceil
# 
# import pytz
# 
# from django.contrib.auth.models import User
# from django.db import models
```

### Paso 3: Si el archivo sigue incorrecto después del pull

```bash
# Forzar actualización del archivo desde el repositorio
git checkout origin/main -- taller/models/empresa.py
```

### Paso 4: Aplicar la migración

```bash
python manage.py migrate taller 0056
```

### Paso 5: Reiniciar servidor

```bash
touch gestion_taller/wsgi.py
```

---

## Comandos Rápidos (Todo en Uno):

```bash
# 1. Resolver git (eliminar cache y hacer pull)
rm -rf .aider.tags.cache.v4/
git pull

# 2. Forzar actualización de empresa.py si es necesario
git checkout origin/main -- taller/models/empresa.py

# 3. Verificar imports
head -15 taller/models/empresa.py | grep -E "Decimal|User|timedelta"

# 4. Aplicar migración
python manage.py migrate taller 0056

# 5. Reiniciar
touch gestion_taller/wsgi.py
```

---

## Si el problema persiste:

El archivo `empresa.py` en el servidor parece estar muy desactualizado. Después del `git pull`, verifica que el archivo tenga la estructura correcta. Si no, puedes copiarlo manualmente desde el repositorio.
