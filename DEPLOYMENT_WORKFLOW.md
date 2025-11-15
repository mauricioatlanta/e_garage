# 🔄 Flujo de Trabajo - eGarage

## 🎯 OBJETIVO
**Una sola fuente de verdad: Git**

PC → Git → Servidor (SOLO en esta dirección)

---

## 📅 FLUJO DIARIO DE TRABAJO

### Mañana (Inicio del día)
```bash
# 1. Asegurarte de tener la última versión
cd E:\projecto\e_garage
git pull origin main

# 2. Crear branch para tu trabajo del día (opcional pero recomendado)
git checkout -b feature/descripcion-corta

# 3. Trabajar normalmente
# Editar archivos, probar localmente, etc.
```

### Durante el Día (Desarrollo)
```bash
# Probar cambios localmente
python manage.py runserver

# Commits frecuentes (cada funcionalidad pequeña)
git add .
git commit -m "feat: Descripción clara del cambio"
```

### Tarde (Antes de deployment)
```bash
# 1. Asegurarte que todo funciona local
python manage.py check
python manage.py test  # Si tienes tests

# 2. Merge a main
git checkout main
git merge feature/descripcion-corta

# 3. Push a Git
git push origin main

# 4. DEPLOYMENT
./scripts/deploy_to_server.sh
```

---

## 🚨 SI YA EDITASTE EN EL SERVIDOR (Rescate de Emergencia)

### Paso 1: Traer Cambios del Servidor a PC
```powershell
# Opción A: Con script automático
.\scripts\sync_from_server.ps1

# Opción B: Manual con SCP
scp -r atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/* E:\projecto\e_garage\
```

### Paso 2: Revisar y Commitear
```bash
# Ver qué cambió
git status
git diff

# Commitear los cambios rescatados
git add -A
git commit -m "fix: Cambios rescatados del servidor ($(date))"
git push origin main
```

### Paso 3: Desde Ahora, SOLO Editar en PC
**Nunca más editar en el servidor directamente.**

---

## 🔍 DIAGNÓSTICO: ¿Por Qué Fallan las Instalaciones?

### Problema 1: Dependencias Desactualizadas
**Síntoma**: `pip install` falla o instala versiones incorrectas

**Causa**: `requirements.txt` no refleja las dependencias reales

**Solución**:
```bash
# En tu PC, regenerar requirements.txt
pip freeze > requirements.txt

# Verificar que esté limpio (sin paquetes innecesarios)
# Editar manualmente si es necesario

# Commitear y pushear
git add requirements.txt
git commit -m "chore: Actualizar requirements.txt"
git push origin main
```

### Problema 2: Versiones de Python Diferentes
**Síntoma**: Errores de sintaxis o `ImportError` en el servidor

**Causa**: Tu PC usa Python 3.13, servidor usa Python 3.10

**Solución**:
```bash
# En tu PC, verificar versión
python --version

# En el servidor, verificar versión
ssh atlantareciclajes@ssh.pythonanywhere.com
python --version

# Si son diferentes, especificar versión mínima en requirements.txt
# Agregar al inicio de requirements.txt:
# python_version >= "3.10"
```

### Problema 3: Configuración de Entorno
**Síntoma**: Aplicación funciona local pero falla en servidor

**Causa**: Variables de entorno o configuración diferente

**Solución**: Crear `settings_local.py` en el servidor
```python
# /home/atlantareciclajes/apps/egarage/current/gestion_taller/settings_local.py

import os
from pathlib import Path

# NO subir este archivo a Git (agregar a .gitignore)

DEBUG = False
ALLOWED_HOSTS = ['atlantareciclajes.pythonanywhere.com', 'www.egarage.cl']

# Base de datos del servidor
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/home/atlantareciclajes/apps/egarage/db.sqlite3',
    }
}

# Rutas del servidor
MEDIA_ROOT = '/home/atlantareciclajes/apps/egarage/media'
STATIC_ROOT = '/home/atlantareciclajes/apps/egarage/staticfiles'

# Email del servidor (si aplica)
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Secret key del servidor
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
```

Luego en `settings.py`, agregar al final:
```python
# Al final de settings.py
try:
    from .settings_local import *
except ImportError:
    pass
```

### Problema 4: Permisos de Archivos
**Síntoma**: Error 500 o "Permission denied"

**Solución**:
```bash
# En el servidor
cd /home/atlantareciclajes/apps/egarage
chmod -R 755 current/
chmod -R 775 media/
chmod -R 775 staticfiles/
```

### Problema 5: Migraciones Desincronizadas
**Síntoma**: `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solución**:
```bash
# Ver estado
python manage.py showmigrations

# Si hay migraciones fake necesarias
python manage.py migrate --fake nombre_app numero_migracion

# O resetear BD (CUIDADO: PIERDES DATOS)
# Solo en desarrollo/testing
rm db.sqlite3
python manage.py migrate
```

---

## ✅ MEJORES PRÁCTICAS

### 1. Commits Descriptivos
```bash
# ❌ Mal
git commit -m "fix"
git commit -m "cambios"

# ✅ Bien
git commit -m "fix: Corregir error en cálculo de IVA"
git commit -m "feat: Agregar filtro por fecha en reportes"
git commit -m "chore: Actualizar dependencias de seguridad"
```

### 2. Branches para Funcionalidades Grandes
```bash
git checkout -b feature/nuevo-modulo-facturacion
# ... trabajo ...
git commit -m "feat: Agregar módulo de facturación"
git checkout main
git merge feature/nuevo-modulo-facturacion
```

### 3. Testing Local ANTES de Pushear
```bash
# Verificar que no hay errores
python manage.py check

# Probar migraciones
python manage.py migrate

# Correr tests
python manage.py test

# Solo si todo pasa, pushear
git push origin main
```

### 4. Deployment en Horas de Bajo Tráfico
- **Mejor momento**: Madrugada o fines de semana
- **Evitar**: Horas pico (10am-5pm)
- **Notificar**: Usuarios activos si es posible

### 5. Monitorear Post-Deployment
```bash
# Revisar logs por 10-15 minutos después de deployment
ssh atlantareciclajes@ssh.pythonanywhere.com
tail -f /var/log/atlantareciclajes.pythonanywhere.com.error.log
```

---

## 🛠️ HERRAMIENTAS ÚTILES

### Git Aliases (Opcional)
Agregar a `~/.gitconfig`:
```ini
[alias]
    st = status
    co = checkout
    ci = commit
    br = branch
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = log --graph --oneline --all
```

### Script de Verificación Pre-Commit
Crear `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Verificar sintaxis antes de commitear
python manage.py check
if [ $? -ne 0 ]; then
    echo "❌ Errores de sintaxis. Commit cancelado."
    exit 1
fi
```

---

## 📚 RECURSOS ADICIONALES

- **Git Cheatsheet**: https://education.github.com/git-cheat-sheet-education.pdf
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **PythonAnywhere Docs**: https://help.pythonanywhere.com/

---

**Mantén este documento actualizado según aprendes mejores prácticas** ✨



