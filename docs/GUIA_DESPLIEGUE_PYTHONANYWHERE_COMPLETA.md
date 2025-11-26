# 🚀 Guía Completa de Despliegue - PythonAnywhere

## 📋 Resumen Ejecutivo

**✅ Estado:** Código listo para producción
- ✅ Variables de entorno configuradas
- ✅ WhiteNoise para archivos estáticos
- ✅ MySQL con utf8mb4
- ✅ Seguridad completa
- ✅ **Sentry configurado para monitoreo de errores** 🚨

## 🚨 ANTES DE EMPEZAR: Configurar Sentry

### ¿Por qué Sentry?

**Sentry es tu red de seguridad.** Cuando un usuario en producción tenga un "Error 500", Sentry te enviará un email diciéndote:
- ✅ Exactamente en qué línea de código falló
- ✅ Qué usuario estaba usando la aplicación
- ✅ Qué acción estaba intentando realizar
- ✅ Stack trace completo del error

**Sin Sentry, estarás ciego si algo falla en producción.**

### Paso 1: Crear Cuenta en Sentry

1. Ve a https://sentry.io/signup/
2. Crea una cuenta gratuita
3. Crea un nuevo proyecto "Django"
4. Copia tu **DSN** (Data Source Name) - algo como:
   ```
   https://abc123def456@o123456.ingest.sentry.io/7890123
   ```

### Paso 2: Agregar SENTRY_DSN al .env

En tu archivo `.env` (en el servidor), agrega:
```bash
SENTRY_DSN=https://tu-dsn-aqui@sentry.io/project-id
```

**Nota:** Sentry solo se activa cuando `DEBUG=False`, así que es seguro agregarlo al `.env` de producción.

## 📝 PASO A PASO: Despliegue en PythonAnywhere

### Paso 1: Preparar el Servidor

```bash
# 1. Conectar a PythonAnywhere Bash Console
# 2. Navegar al directorio de tu usuario
cd ~
mkdir -p egarage
cd egarage
```

### Paso 2: Clonar el Repositorio

```bash
# Clonar tu repositorio
git clone https://github.com/tu-repo/egarage.git .

# O si ya tienes el código, subirlo via SFTP/SCP
```

### Paso 3: Crear Entorno Virtual

```bash
# Crear venv con Python 3.10 (recomendado para PythonAnywhere)
python3.10 -m venv venv

# Activar venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

**⚠️ IMPORTANTE:** Asegúrate de que `python3.10` esté disponible. Si no, usa la versión que tengas:
```bash
python3 --version  # Verificar versión
```

### Paso 4: Crear Archivo .env en el Servidor

**⚠️ CRÍTICO:** Este archivo NO se sube automáticamente (está en `.gitignore`). Debes crearlo manualmente.

```bash
# En PythonAnywhere Bash Console
cd ~/egarage
nano .env
```

**Contenido del `.env`:**
```bash
# ===============================================================
# 🔒 SEGURIDAD
# ===============================================================
DJANGO_SECRET_KEY=tu-secret-key-generado-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tuusuario.pythonanywhere.com

# CSRF (reemplazar con tu dominio real)
DJANGO_CSRF_TRUSTED_ORIGINS=https://tuusuario.pythonanywhere.com

# SSL (True en producción)
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True

# ===============================================================
# 🗄️ BASE DE DATOS (MySQL en PythonAnywhere)
# ===============================================================
# ⚠️ IMPORTANTE: PythonAnywhere NO usa localhost para MySQL
# El host será algo como: tuusuario.mysql.pythonanywhere-services.com

DB_ENGINE=mysql
DB_NAME=tuusuario$egarage  # Formato: usuario$nombre_db
DB_USER=tuusuario  # Tu usuario de PythonAnywhere
DB_PASSWORD=tu-password-de-mysql  # Password de MySQL que configuraste en PA
DB_HOST=tuusuario.mysql.pythonanywhere-services.com  # ⚠️ NO usar localhost
DB_PORT=3306

# ===============================================================
# 📧 EMAIL
# ===============================================================
EMAIL_HOST=srv24.cpanelhost.cl
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=subscription@egarage.cl
EMAIL_PASSWORD=tu-password-de-email
DEFAULT_FROM_EMAIL=eGarage <subscription@egarage.cl>

# ===============================================================
# 📁 ARCHIVOS ESTÁTICOS
# ===============================================================
STATIC_ROOT=/home/tuusuario/egarage/staticfiles
MEDIA_ROOT=/home/tuusuario/egarage/media
DJANGO_USE_WHITENOISE=True

# ===============================================================
# 🚨 SENTRY (Monitoreo de Errores)
# ===============================================================
SENTRY_DSN=https://tu-dsn-aqui@sentry.io/project-id
SENTRY_RELEASE=egarage@1.0.0  # Opcional: versión de tu release
```

**⚠️ PUNTOS CRÍTICOS:**

1. **DB_HOST:** NO usar `localhost`. Usa `tuusuario.mysql.pythonanywhere-services.com`
2. **DB_NAME:** Formato especial de PythonAnywhere: `usuario$nombre_db`
3. **SENTRY_DSN:** Obtener de https://sentry.io después de crear proyecto

### Paso 5: Crear Base de Datos MySQL

En PythonAnywhere:

1. Ve a la pestaña **"Databases"**
2. Haz clic en **"Create a new database"**
3. Nombre: `egarage`
4. Anota el **host**, **usuario** y **password** generados
5. Actualiza tu `.env` con estos valores

**O manualmente en MySQL Console:**
```sql
-- En PythonAnywhere, ve a "Databases" → "MySQL Console"
-- O ejecuta en Bash: mysql -u tuusuario -p

-- Crear base de datos con utf8mb4 (CRÍTICO para emojis)
CREATE DATABASE tuusuario$egarage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Verificar que se creó correctamente
SHOW CREATE DATABASE tuusuario$egarage;
-- Debe mostrar: CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
```

### Paso 6: Ejecutar Migraciones

```bash
# En PythonAnywhere Bash Console
cd ~/egarage
source venv/bin/activate

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser
```

### Paso 7: Recolectar Archivos Estáticos

```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Verificar que se crearon
ls -la staticfiles/
```

### Paso 8: Cargar Roles Iniciales (RBAC)

```bash
# Cargar roles del sistema (Owner, Admin, Vendedor, Tecnico)
python manage.py setup_roles
```

### Paso 9: Configurar WSGI

**⚠️ CRÍTICO:** PythonAnywhere no usa `python manage.py runserver`. Usa un archivo WSGI.

En PythonAnywhere:

1. Ve a la pestaña **"Web"**
2. Haz clic en **"WSGI configuration file"**
3. Edita el archivo y reemplaza todo con:

```python
# ⚠️ IMPORTANTE: Actualizar las rutas según tu configuración
import os
import sys
from pathlib import Path

# Agregar directorio del proyecto al path
project_home = '/home/tuusuario/egarage'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ⚠️ CRÍTICO: Cargar .env explícitamente en producción
# Esto asegura que las variables de entorno estén disponibles
from dotenv import load_dotenv
env_path = Path(project_home) / '.env'
load_dotenv(dotenv_path=env_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')

# Cargar aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**⚠️ IMPORTANTE:**
- Reemplazar `/home/tuusuario/egarage` con tu ruta real
- Verificar que `.env` esté en la ruta correcta
- El archivo `.env` debe tener permisos de lectura

### Paso 10: Configurar Archivos Estáticos

En PythonAnywhere, ve a la pestaña **"Web"** → **"Static files"**:

```
URL: /static/
Directorio: /home/tuusuario/egarage/staticfiles/

URL: /media/
Directorio: /home/tuusuario/egarage/media/
```

### Paso 11: Recargar Aplicación Web

En PythonAnywhere:

1. Ve a la pestaña **"Web"**
2. Haz clic en el botón verde **"Reload tuusuario.pythonanywhere.com"**
3. Espera 10-20 segundos
4. Verifica que no haya errores en el log

### Paso 12: Verificar que Todo Funciona

```bash
# 1. Verificar configuración
python manage.py check --deploy

# 2. Probar que la aplicación carga
python manage.py runserver 0.0.0.0:8000  # Solo para verificar, no usar en producción
```

**Verificar en el navegador:**
- ✅ https://tuusuario.pythonanywhere.com carga correctamente
- ✅ Los archivos estáticos se cargan (CSS/JS)
- ✅ El login funciona
- ✅ Puedes crear un documento/prueba

## 🚨 VERIFICACIÓN POST-DESPLIEGUE

### Checklist Final

- [ ] Código subido al servidor
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`requirements.txt`)
- [ ] Archivo `.env` creado con todas las variables
- [ ] Base de datos MySQL creada con **utf8mb4**
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Roles cargados (`setup_roles`)
- [ ] Archivos estáticos recolectados (`collectstatic`)
- [ ] WSGI configurado correctamente (con `load_dotenv`)
- [ ] Archivos estáticos configurados en PythonAnywhere
- [ ] Aplicación recargada sin errores
- [ ] Sitio accesible en `https://tuusuario.pythonanywhere.com`
- [ ] Archivos estáticos se cargan correctamente
- [ ] Login funciona correctamente
- [ ] **Sentry configurado y recibiendo errores** ✅

### Probar Sentry

Para verificar que Sentry funciona:

1. Ve a https://sentry.io
2. Entra a tu proyecto
3. Intenta generar un error en producción (ej: dividir por cero en una vista)
4. Debes recibir una notificación por email
5. El error debe aparecer en el dashboard de Sentry

## 🔧 TROUBLESHOOTING COMÚN

### Error: "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### Error: "SECRET_KEY not set"

```bash
# Verificar que .env existe y tiene DJANGO_SECRET_KEY
cat .env | grep SECRET_KEY

# Generar nuevo secret key
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Error: "Database connection failed"

**Problema:** PythonAnywhere NO usa `localhost` para MySQL.

**Solución:**
```bash
# Verificar variables de DB en .env
cat .env | grep DB_

# El DB_HOST debe ser algo como:
# tuusuario.mysql.pythonanywhere-services.com
# NO debe ser: localhost
```

### Error: "Static files not found"

```bash
# Verificar que collectstatic se ejecutó
ls -la staticfiles/

# Ejecutar de nuevo
python manage.py collectstatic --noinput

# Verificar configuración en PythonAnywhere Web → Static files
```

### Error: "Character set 'utf8' is not a compiled character set"

**Problema:** Base de datos no está en utf8mb4.

**Solución:**
```sql
-- Verificar charset actual
SHOW CREATE DATABASE tuusuario$egarage;

-- Si no está en utf8mb4, recrear base de datos
DROP DATABASE tuusuario$egarage;
CREATE DATABASE tuusuario$egarage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Luego ejecutar migraciones de nuevo
python manage.py migrate
```

### Error: "EMAIL_PASSWORD must be set in production"

```bash
# Verificar que EMAIL_PASSWORD está en .env
cat .env | grep EMAIL_PASSWORD

# Si no está, agregarlo
nano .env
# Agregar: EMAIL_PASSWORD=tu-password
```

### Error: Sentry no recibe errores

1. Verificar que `SENTRY_DSN` está en `.env`
2. Verificar que `DEBUG=False` (Sentry solo funciona en producción)
3. Recargar aplicación web en PythonAnywhere
4. Probar generando un error manualmente

## 📝 NOTAS IMPORTANTES

### Variables de Entorno en PythonAnywhere

PythonAnywhere permite configurar variables de entorno de dos formas:

1. **Archivo `.env`** (Recomendado): Crea `.env` en el directorio del proyecto
2. **Panel Web**: Ve a "Web" → "Environment variables" y agrega variables

**Recomendación:** Usar archivo `.env` porque:
- ✅ Más fácil de mantener
- ✅ Versionado localmente (`.env.example` en git)
- ✅ Compatible con `python-dotenv`

### WhiteNoise vs Nginx

**WhiteNoise** (Configurado):
- ✅ Funciona sin configuración adicional
- ✅ Perfecto para PythonAnywhere
- ✅ Compresión automática
- ✅ No requiere nginx/apache

**Recomendación:** Usar WhiteNoise (ya configurado).

### MySQL utf8mb4

**⚠️ CRÍTICO:** Asegúrate de crear la base de datos con utf8mb4:

```sql
CREATE DATABASE tuusuario$egarage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Si la base de datos ya existe:**
```sql
ALTER DATABASE tuusuario$egarage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Sentry

**Sentry es tu red de seguridad.** Sin Sentry, si un usuario tiene un error en producción:
- ❌ No sabrás qué pasó
- ❌ No sabrás en qué línea falló
- ❌ No sabrás qué usuario estaba usando la app

**Con Sentry:**
- ✅ Recibes email inmediato con el error
- ✅ Stack trace completo
- ✅ Información del usuario (si configuraste `send_default_pii=True`)
- ✅ Historial de errores

## 🎉 RESULTADO FINAL

**✅ Proyecto desplegado en PythonAnywhere**
**✅ Variables de entorno configuradas**
**✅ Base de datos MySQL con utf8mb4**
**✅ Archivos estáticos optimizados con WhiteNoise**
**✅ Seguridad activada**
**✅ Sentry configurado para monitoreo de errores**

**¡eGarage está en producción y monitoreado!** 🚀

---

**Estado:** ✅ **LISTO PARA PRODUCCIÓN**
**Fecha:** 2025-01-XX
**Servidor:** PythonAnywhere
**Monitoreo:** Sentry configurado



