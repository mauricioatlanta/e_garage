# Solución: Error Git Pull y NameError en Servidor

## Problema 1: Git Pull Bloqueado

El archivo `.aider.tags.cache.v4/cache.db` tiene cambios locales que bloquean el pull.

### Solución Rápida:

```bash
# Opción 1: Ignorar el archivo de cache (recomendado)
git stash
git pull
git stash pop

# Opción 2: Agregar el archivo a .gitignore y hacer commit
echo ".aider.tags.cache.v4/" >> .gitignore
git add .gitignore
git commit -m "Ignorar archivos de cache de aider"
git pull

# Opción 3: Descartar cambios en el archivo de cache
git checkout -- .aider.tags.cache.v4/cache.db
git pull
```

---

## Problema 2: NameError - User no definido

El archivo `taller/models/empresa.py` en el servidor no tiene el import de `User`.

### Solución:

Verificar que el archivo tenga esta línea al inicio (después de la línea 6):

```python
from django.contrib.auth.models import User
```

**El archivo debe comenzar así:**

```python
from datetime import timedelta
from decimal import Decimal
from math import ceil

import pytz

from django.contrib.auth.models import User  # ← Esta línea debe estar
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils import timezone
```

---

## Pasos Completos para Resolver:

### 1. Resolver el problema de Git:

```bash
# Descartar cambios en el archivo de cache
git checkout -- .aider.tags.cache.v4/cache.db

# Hacer pull
git pull
```

### 2. Verificar/Corregir el import en empresa.py:

```bash
# Verificar si tiene el import
head -10 taller/models/empresa.py | grep -i "from django.contrib.auth"

# Si no aparece, agregarlo manualmente o copiar el archivo completo desde el repo
```

### 3. Aplicar la migración:

```bash
python manage.py migrate taller 0056
```

### 4. Reiniciar servidor:

```bash
touch gestion_taller/wsgi.py
```

---

## Si el problema persiste:

Puedes copiar directamente el archivo `taller/models/empresa.py` desde el repositorio o verificar que tenga el import correcto.
