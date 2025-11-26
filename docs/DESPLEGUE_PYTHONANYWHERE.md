# 🚀 Guía de Despliegue en PythonAnywhere - eGarage

**Fecha:** Diciembre 2024  
**Versión:** 1.0  
**Estado:** ✅ Listo para Producción

---

## 📋 Resumen

Guía paso a paso para desplegar eGarage en PythonAnywhere, incluyendo los 3 consejos críticos de supervivencia para evitar errores comunes.

---

## ⚠️ Los 3 Consejos Críticos de Supervivencia

### 1. 🎯 El "Trampa" del Archivo WSGI

**Problema:** En producción, `manage.py` no corre el servidor. Lo hace un archivo WSGI. A veces el servidor web arranca Django antes de que `settings.py` tenga oportunidad de leer el archivo `.env`.

**Solución:** Cargar el `.env` explícitamente en el archivo WSGI de PythonAnywhere.

#### Archivo WSGI Template

Edita `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`:

```python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv  # ✅ CRÍTICO: Cargar .env ANTES de Django

# Ruta del proyecto (ajusta según tu estructura)
project_home = '/home/tu_usuario/egarage'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ✅ Cargar variables de entorno ANTES de iniciar Django
env_path = Path(project_home) / '.env'
load_dotenv(env_path)

# Ahora sí, inicializar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**⚠️ IMPORTANTE:** 
- El `load_dotenv()` debe estar **ANTES** de `get_wsgi_application()`
- Asegúrate de que la ruta del proyecto sea correcta
- Verifica que el archivo `.env` esté en la raíz del proyecto

---

### 2. 🗄️ Base de Datos: La Codificación Correcta

**Problema:** Si la base de datos no tiene `utf8mb4`, no podrás guardar emojis (importante para comentarios de clientes).

**Solución:** Crear o alterar la base de datos con `utf8mb4` antes de correr migraciones.

#### Paso 1: Crear Base de Datos en PythonAnywhere

1. Ve a la pestaña **"Databases"** en PythonAnywhere
2. Crea una nueva base de datos MySQL
3. Anota el nombre de usuario y la contraseña

#### Paso 2: Configurar Codificación

En la consola MySQL de PythonAnywhere (pestaña **"Databases"** → **"Open MySQL console"**):

```sql
-- Verificar codificación actual
SHOW CREATE DATABASE tu_nombre_de_db;

-- Si no es utf8mb4, alterar
ALTER DATABASE tu_nombre_de_db 
    CHARACTER SET = utf8mb4 
    COLLATE = utf8mb4_unicode_ci;

-- Verificar que se aplicó
SHOW CREATE DATABASE tu_nombre_de_db;
-- Debe mostrar: DEFAULT CHARACTER SET utf8mb4
```

#### Paso 3: Verificar en settings.py

Tu `settings.py` ya tiene la configuración correcta:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES', character_set_connection=utf8mb4, collation_connection=utf8mb4_unicode_ci",
        },
    }
}
```

**✅ Verificación:** Después de correr migraciones, verifica que las tablas tengan utf8mb4:

```sql
-- Verificar codificación de tablas
SELECT 
    TABLE_NAME,
    TABLE_COLLATION
FROM 
    information_schema.TABLES
WHERE 
    TABLE_SCHEMA = 'tu_nombre_de_db'
LIMIT 5;
```

---

### 3. 🔒 HTTPS Forzado

**Problema:** Sin HTTPS, las cookies y datos sensibles pueden ser interceptados.

**Solución:** Activar SSL en PythonAnywhere y configurar variables de entorno.

#### Paso 1: Activar SSL en PythonAnywhere

1. Ve a la pestaña **"Web"**
2. Si tienes dominio personalizado:
   - Haz clic en **"Add a new web app"** o edita la existente
   - Selecciona **"Let's Encrypt"** para certificado SSL gratuito
   - Ingresa tu dominio
3. Si usas `tu_usuario.pythonanywhere.com`:
   - El SSL se activa automáticamente

#### Paso 2: Configurar Variables de Entorno

En tu archivo `.env` de producción:

```env
# HTTPS Forzado
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True

# CSRF Trusted Origins
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

#### Paso 3: Verificar Headers

Después del despliegue, verifica que los headers estén correctos:

```bash
curl -I https://tu-dominio.com
```

Debes ver:
- `Strict-Transport-Security: max-age=31536000`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`

---

## 📝 Checklist de Despliegue Completo

### Pre-Despliegue

- [ ] Cuenta de PythonAnywhere creada
- [ ] Base de datos MySQL creada
- [ ] Base de datos configurada con `utf8mb4`
- [ ] Archivo `.env` preparado con todas las variables
- [ ] SSL/HTTPS activado en PythonAnywhere

### Despliegue

- [ ] Clonar repositorio en PythonAnywhere
- [ ] Crear archivo `.env` en la raíz del proyecto
- [ ] Configurar archivo WSGI con `load_dotenv()` antes de Django
- [ ] Instalar dependencias: `pip3.10 install -r requirements.txt`
- [ ] Ejecutar migraciones: `python3.10 manage.py migrate`
- [ ] Recolectar archivos estáticos: `python3.10 manage.py collectstatic --noinput`
- [ ] Crear superusuario: `python3.10 manage.py createsuperuser`
- [ ] Configurar web app en PythonAnywhere (pestaña "Web")
- [ ] Configurar ruta de archivos estáticos en PythonAnywhere
- [ ] Reiniciar web app

### Post-Despliegue

- [ ] Verificar que el sitio carga correctamente
- [ ] Verificar que archivos estáticos cargan (CSS/JS)
- [ ] Verificar que HTTPS funciona (redirección automática)
- [ ] Verificar que el registro funciona desde todos los países
- [ ] Verificar que los emails se envían correctamente
- [ ] Verificar logs de errores (si hay errores 500)

---

## 🔧 Configuración Detallada

### 1. Estructura de Directorios en PythonAnywhere

```
/home/tu_usuario/
    └── egarage/
        ├── .env                    # ✅ Variables de entorno
        ├── manage.py
        ├── requirements.txt
        ├── gestion_taller/
        │   └── settings.py
        ├── taller/
        ├── staticfiles/            # ✅ Generado por collectstatic
        └── media/                   # ✅ Archivos subidos por usuarios
```

### 2. Archivo WSGI Completo

Copia este contenido a `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`:

```python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ruta del proyecto (ajusta según tu estructura)
project_home = '/home/tu_usuario/egarage'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Cargar variables de entorno ANTES de iniciar Django
env_path = Path(project_home) / '.env'
load_dotenv(env_path)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 3. Archivo .env de Producción

```env
# Django Core
DJANGO_SECRET_KEY=tu-clave-super-secreta-generada
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,tu_usuario.pythonanywhere.com

# Base de Datos (MySQL)
DB_ENGINE=mysql
DB_NAME=tu_usuario$egarage_db
DB_USER=tu_usuario
DB_PASSWORD=tu_password_de_pythonanywhere
DB_HOST=tu_usuario.mysql.pythonanywhere-services.com
DB_PORT=3306

# Email (SMTP)
EMAIL_HOST=srv24.cpanelhost.cl
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=subscription@egarage.cl
EMAIL_HOST_PASSWORD=tu_password_email
DEFAULT_FROM_EMAIL=eGarage <subscription@egarage.cl>

# HTTPS Forzado
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True

# Static Files
STATIC_ROOT=/home/tu_usuario/egarage/staticfiles
MEDIA_ROOT=/home/tu_usuario/egarage/media

# Sentry (Opcional)
# SENTRY_DSN=tu_dsn_de_sentry
# SENTRY_RELEASE=egarage@1.0.0
```

### 4. Configuración de Web App en PythonAnywhere

1. Ve a la pestaña **"Web"**
2. Haz clic en **"Add a new web app"** o edita la existente
3. Configura:
   - **Source code:** `/home/tu_usuario/egarage`
   - **Working directory:** `/home/tu_usuario/egarage`
   - **WSGI configuration file:** `/var/www/tu_usuario_pythonanywhere_com_wsgi.py`
4. En **"Static files"**:
   - **URL:** `/static/`
   - **Directory:** `/home/tu_usuario/egarage/staticfiles`
5. En **"Static files"** (media):
   - **URL:** `/media/`
   - **Directory:** `/home/tu_usuario/egarage/media`

---

## 🐛 Troubleshooting

### Error 500: Internal Server Error

**Causa común:** Variables de entorno no cargadas o base de datos no configurada.

**Solución:**
1. Verifica logs: `/var/log/tu_usuario.pythonanywhere.com.error.log`
2. Verifica que el archivo WSGI carga `.env` antes de Django
3. Verifica que todas las variables en `.env` están correctas
4. Verifica que la base de datos existe y tiene permisos

### Archivos Estáticos No Cargan (404)

**Causa común:** `collectstatic` no se ejecutó o ruta incorrecta en PythonAnywhere.

**Solución:**
1. Ejecuta: `python3.10 manage.py collectstatic --noinput`
2. Verifica que la ruta en PythonAnywhere apunta a `/home/tu_usuario/egarage/staticfiles`
3. Reinicia la web app

### Error: "No module named 'dotenv'"

**Causa común:** `python-dotenv` no está instalado.

**Solución:**
```bash
pip3.10 install python-dotenv
```

### Error: "Can't connect to MySQL server"

**Causa común:** Credenciales incorrectas o host incorrecto.

**Solución:**
1. Verifica que el host sea: `tu_usuario.mysql.pythonanywhere-services.com`
2. Verifica que el nombre de la base de datos incluya el prefijo: `tu_usuario$egarage_db`
3. Verifica credenciales en la pestaña "Databases" de PythonAnywhere

### Error: "Incorrect string value" al guardar emojis

**Causa común:** Base de datos no tiene `utf8mb4`.

**Solución:**
```sql
ALTER DATABASE tu_nombre_de_db 
    CHARACTER SET = utf8mb4 
    COLLATE = utf8mb4_unicode_ci;
```

Luego recrea las tablas:
```bash
python3.10 manage.py migrate --run-syncdb
```

---

## 📊 Verificación Post-Despliegue

### 1. Verificar Sitio Carga

```bash
curl -I https://tu-dominio.com
```

Debe retornar `200 OK`.

### 2. Verificar Archivos Estáticos

Visita: `https://tu-dominio.com/static/admin/css/base.css`

Debe cargar el archivo CSS (no 404).

### 3. Verificar HTTPS

Visita: `http://tu-dominio.com`

Debe redirigir automáticamente a `https://tu-dominio.com`.

### 4. Verificar Registro

1. Visita: `https://tu-dominio.com/registro/`
2. Intenta registrarte desde diferentes países
3. Verifica que la moneda y configuración sean correctas

### 5. Verificar Emails

```bash
python3.10 manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'Test desde producción',
    'Este es un test',
    'subscription@egarage.cl',
    ['tu-email@example.com']
)
```

---

## 🎯 Comandos Rápidos de Referencia

```bash
# Instalar dependencias
pip3.10 install -r requirements.txt

# Migraciones
python3.10 manage.py migrate

# Recolectar estáticos
python3.10 manage.py collectstatic --noinput

# Crear superusuario
python3.10 manage.py createsuperuser

# Verificar configuración
python3.10 manage.py check --deploy

# Shell de Django
python3.10 manage.py shell

# Logs de errores
tail -f /var/log/tu_usuario.pythonanywhere.com.error.log
```

---

## ✅ Checklist Final

- [ ] Archivo WSGI configurado con `load_dotenv()` antes de Django
- [ ] Base de datos creada con `utf8mb4`
- [ ] Archivo `.env` configurado con todas las variables
- [ ] SSL/HTTPS activado en PythonAnywhere
- [ ] Variables de seguridad configuradas en `.env`
- [ ] Archivos estáticos recolectados
- [ ] Migraciones aplicadas
- [ ] Web app configurada en PythonAnywhere
- [ ] Sitio carga correctamente
- [ ] HTTPS funciona (redirección automática)
- [ ] Archivos estáticos cargan
- [ ] Registro funciona desde todos los países
- [ ] Emails se envían correctamente

---

**Última actualización:** Diciembre 2024  
**Autor:** Guía de Despliegue PythonAnywhere  
**Estado:** ✅ Listo para Producción



