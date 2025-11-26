# 📋 Checklist de Despliegue - PythonAnywhere

## ✅ Pre-Despliegue Completado

Todas las configuraciones de producción han sido implementadas:
- ✅ Variables de entorno con `python-dotenv`
- ✅ WhiteNoise para archivos estáticos
- ✅ MySQL con utf8mb4
- ✅ Configuración de seguridad completa

## 🚀 Pasos para Desplegar

### Paso 1: Preparar Servidor

```bash
# 1. Conectar a PythonAnywhere Bash Console
# 2. Clonar repositorio o subir código
cd /home/tuusuario/
git clone https://github.com/tu-repo/egarage.git mysite
cd mysite
```

### Paso 2: Crear Entorno Virtual

```bash
# Crear venv
python3.10 -m venv venv

# Activar venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno

```bash
# Crear archivo .env
nano .env
```

**Contenido del .env:**
```bash
# Seguridad
DJANGO_SECRET_KEY=tu-secret-key-generado-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tuusuario.pythonanywhere.com

# Base de Datos
DB_ENGINE=mysql
DB_NAME=egarage
DB_USER=tuusuario
DB_PASSWORD=tu-password-de-mysql
DB_HOST=tuusuario.mysql.pythonanywhere-services.com
DB_PORT=3306

# Email
EMAIL_HOST=srv24.cpanelhost.cl
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=subscription@egarage.cl
EMAIL_PASSWORD=tu-password-de-email
DEFAULT_FROM_EMAIL=eGarage <subscription@egarage.cl>

# Static Files
DJANGO_USE_WHITENOISE=True
STATIC_ROOT=/home/tuusuario/mysite/staticfiles
MEDIA_ROOT=/home/tuusuario/mysite/media

# Seguridad SSL
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_CSRF_TRUSTED_ORIGINS=https://tuusuario.pythonanywhere.com
```

### Paso 4: Crear Base de Datos MySQL

```bash
# En PythonAnywhere, ve a la pestaña "Databases"
# Crea una nueva base de datos MySQL llamada "egarage"
# Anota el nombre de usuario y host generados
```

**O manualmente:**
```sql
-- Conectar a MySQL
mysql -u root -p

-- Crear base de datos con utf8mb4
CREATE DATABASE tuusuario$egarage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Paso 5: Ejecutar Migraciones

```bash
# Activar venv
source venv/bin/activate

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser
```

### Paso 6: Recolectar Archivos Estáticos

```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Verificar que se crearon
ls -la staticfiles/
```

### Paso 7: Configurar WSGI

En PythonAnywhere, ve a la pestaña "Web" y edita el archivo WSGI:

```python
import os
import sys

# Agregar directorio del proyecto al path
path = '/home/tuusuario/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_taller.settings'

# Cargar aplicación
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Paso 8: Configurar Archivos Estáticos (Web Tab)

En PythonAnywhere, ve a la pestaña "Web" → "Static files":

```
URL: /static/
Directorio: /home/tuusuario/mysite/staticfiles/

URL: /media/
Directorio: /home/tuusuario/mysite/media/
```

### Paso 9: Verificar Configuración

```bash
# Verificar configuración
python manage.py check --deploy

# Probar servidor
python manage.py runserver 0.0.0.0:8000
```

### Paso 10: Recargar Aplicación Web

En PythonAnywhere:
1. Ve a la pestaña "Web"
2. Haz clic en el botón verde "Reload"
3. Verifica que no hay errores en el log

## ✅ Checklist Final

- [ ] Código subido al servidor
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`requirements.txt`)
- [ ] Archivo `.env` creado con todas las variables
- [ ] Base de datos MySQL creada con utf8mb4
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Archivos estáticos recolectados (`collectstatic`)
- [ ] WSGI configurado correctamente
- [ ] Archivos estáticos configurados en PythonAnywhere
- [ ] Aplicación recargada sin errores
- [ ] Sitio accesible en `https://tuusuario.pythonanywhere.com`
- [ ] Archivos estáticos se cargan correctamente
- [ ] Login funciona correctamente
- [ ] Email de prueba enviado exitosamente

## 🔧 Troubleshooting

### Error: "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### Error: "SECRET_KEY not set"

```bash
# Verificar que .env existe y tiene DJANGO_SECRET_KEY
cat .env | grep SECRET_KEY
```

### Error: "Static files not found"

```bash
# Verificar que collectstatic se ejecutó
ls -la staticfiles/

# Ejecutar de nuevo
python manage.py collectstatic --noinput
```

### Error: "Database connection failed"

```bash
# Verificar variables de DB en .env
cat .env | grep DB_

# Probar conexión
python manage.py dbshell
```

### Error: "Email not sending"

```bash
# Verificar EMAIL_PASSWORD en .env
cat .env | grep EMAIL_PASSWORD

# Probar email
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', 'from@example.com', ['to@example.com'])
```

## 📝 Notas Finales

### Variables de Entorno en PythonAnywhere

PythonAnywhere permite configurar variables de entorno de dos formas:

1. **Archivo .env** (Recomendado): Crea `.env` en el directorio del proyecto
2. **Panel Web**: Ve a "Web" → "Environment variables" y agrega variables

### WhiteNoise vs Nginx

**WhiteNoise** (Configurado):
- ✅ Funciona sin configuración adicional
- ✅ Perfecto para PythonAnywhere
- ✅ Compresión automática

**Nginx** (No necesario):
- ⚠️ PythonAnywhere maneja esto automáticamente
- ✅ Puedes usar si prefieres

**Recomendación**: Usar WhiteNoise (ya configurado).

## 🎉 Resultado Final

**✅ Proyecto configurado para producción**
**✅ Variables de entorno centralizadas**
**✅ Archivos estáticos optimizados**
**✅ Base de datos preparada**
**✅ Seguridad activada**

**¡eGarage está listo para producción en PythonAnywhere!** 🚀

---

**Estado:** ✅ **LISTO PARA PRODUCCIÓN**
**Fecha:** 2025-01-XX
**Servidor:** PythonAnywhere

