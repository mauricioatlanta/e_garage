# 🔧 Solución: AccountMiddleware en el Servidor

## Problema
```
django.core.exceptions.ImproperlyConfigured: 
allauth.account.middleware.AccountMiddleware must be added to settings.MIDDLEWARE
```

## ✅ Solución Aplicada Localmente

Ya actualizamos los archivos locales:
- ✅ `gestion_taller/settings.py` - Middleware agregado (línea 139)
- ✅ `gestion_taller/compacto/settings.py` - Middleware agregado (línea 136)

## 🚀 Pasos para Actualizar el Servidor

### Paso 1: Identificar el archivo de settings que usa el servidor

En el servidor, ejecuta:
```bash
cd ~/apps/egarage/current
python manage.py shell -c "from django.conf import settings; print(settings.SETTINGS_MODULE)"
```

O verifica el valor de `DJANGO_SETTINGS_MODULE`:
```bash
echo $DJANGO_SETTINGS_MODULE
```

### Paso 2: Actualizar el archivo de settings en el servidor

Según el resultado del Paso 1, edita el archivo correspondiente:

#### Opción A: Si usa `gestion_taller.settings`
```bash
nano gestion_taller/settings.py
```

Busca la línea:
```python
"django.contrib.auth.middleware.AuthenticationMiddleware",
```

Agrega después de ella:
```python
"django.contrib.auth.middleware.AuthenticationMiddleware",
# AccountMiddleware de allauth (requerido en versiones recientes)
"allauth.account.middleware.AccountMiddleware",
```

#### Opción B: Si usa `gestion_taller.compacto.settings`
```bash
nano gestion_taller/compacto/settings.py
```

Y aplica el mismo cambio.

### Paso 3: Verificar el cambio

En el archivo editado, la sección de MIDDLEWARE debe verse así:
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # <-- AGREGAR ESTA LÍNEA
    # ... resto del middleware
]
```

### Paso 4: Probar

```bash
python manage.py test taller.tests.test_security_isolation
```

## 📝 Nota sobre Releases

Si estás usando un sistema de releases, asegúrate de actualizar el release actual o crear uno nuevo:
```bash
# Ver release actual
ls -la ~/apps/egarage/current

# Si usas releases, actualiza el código:
cd ~/apps/egarage/current
# Edita el archivo como se indica arriba
```

## 🔄 Alternativa: Actualizar desde Git (Recomendado)

Si el código está en Git y ya subiste los cambios:
```bash
cd ~/apps/egarage/current
git pull origin main  # o tu rama correspondiente
```

Luego verifica que el cambio esté presente:
```bash
grep -A 2 "AuthenticationMiddleware" gestion_taller/settings.py
```

Debe mostrar:
```python
"django.contrib.auth.middleware.AuthenticationMiddleware",
"allauth.account.middleware.AccountMiddleware",
```



