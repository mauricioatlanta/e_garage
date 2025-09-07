# 🚀 GUÍA COMPLETA DE DESPLIEGUE EN PYTHONANYWHERE
## eGarage - Sistema de Gestión de Talleres Automotrices

### 📋 INFORMACIÓN DEL PROYECTO
- **Nombre:** eGarage
- **URL de Producción:** https://e-garage-atlantareciclajes.pythonanywhere.com
- **Repositorio:** mauricioatlanta/e_garage
- **Framework:** Django 5.1.6
- **Base de Datos:** MySQL (PythonAnywhere)

---

## ✅ PASO 1: CONFIGURACIÓN INICIAL EN PYTHONANYWHERE

### 1.1 Crear cuenta y configurar proyecto
```bash
# En el dashboard de PythonAnywhere:
# 1. Ir a "Web" → "Add a new web app"
# 2. Seleccionar "Manual configuration" → Python 3.11
# 3. Domain: e-garage-atlantareciclajes.pythonanywhere.com
```

### 1.2 Configurar directorio de trabajo
```bash
# En consola de PythonAnywhere:
cd ~
git clone https://github.com/mauricioatlanta/e_garage.git
cd e_garage
```

---

## ✅ PASO 2: CONFIGURAR ENTORNO VIRTUAL

### 2.1 Crear y activar virtualenv
```bash
# Crear virtualenv (si no existe)
mkvirtualenv --python=/usr/bin/python3.11 venv_egarage

# Activar virtualenv
workon venv_egarage

# Verificar que está activo
which python
# Debe mostrar: /home/atlantareciclajes/.virtualenvs/venv_egarage/bin/python
```

### 2.2 Instalar dependencias
```bash
# Instalar requirements
pip install -r requirements_pythonanywhere.txt

# Verificar instalaciones críticas
pip list | grep -E "(Django|mysqlclient|gunicorn)"
```

---

## ✅ PASO 3: CONFIGURAR BASE DE DATOS MYSQL

### 3.1 Crear base de datos en PythonAnywhere
```bash
# En el dashboard:
# 1. Ir a "Databases"
# 2. Crear nueva base: atlantareciclajes$egarage
# 3. Usuario: atlantareciclajes
# 4. Password: laila2013
# 5. Hostname: atlantareciclajes.mysql.pythonanywhere-services.com
```

### 3.2 Configurar variables de entorno
```bash
# Crear archivo .env en el directorio del proyecto
echo "DJANGO_SECRET_KEY=laila2013-production-key-change-in-server" > .env
echo "DB_NAME=atlantareciclajes\$egarage" >> .env
echo "DB_USER=atlantareciclajes" >> .env
echo "DB_PASSWORD=laila2013" >> .env
echo "DB_HOST=atlantareciclajes.mysql.pythonanywhere-services.com" >> .env
echo "DB_PORT=3306" >> .env
```

---

## ✅ PASO 4: MIGRACIONES Y CONFIGURACIÓN DJANGO

### 4.1 Ejecutar migraciones
```bash
# Activar virtualenv
workon venv_egarage

# Ir al directorio del proyecto
cd ~/e_garage

# Ejecutar migraciones con settings de producción
python manage.py migrate --settings=e_garage.settings_production

# Crear superusuario
python manage.py createsuperuser --settings=e_garage.settings_production
```

### 4.2 Recopilar archivos estáticos
```bash
# Recopilar archivos estáticos
python manage.py collectstatic --noinput --settings=e_garage.settings_production

# Verificar que se creó la carpeta staticfiles
ls -la staticfiles/
```

---

## ✅ PASO 5: CONFIGURAR APLICACIÓN WEB

### 5.1 Configurar en el dashboard Web
```
# En Web → Configuration:

# Source code:
/home/atlantareciclajes/e_garage

# Working directory:
/home/atlantareciclajes/e_garage

# WSGI configuration file:
/var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

# Python version:
3.11

# Virtualenv:
/home/atlantareciclajes/.virtualenvs/venv_egarage
```

### 5.2 Configurar archivo WSGI
```python
# Editar archivo WSGI:
# /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

import os
import sys

# Path del proyecto
path = '/home/atlantareciclajes/e_garage'
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings_production')

# Aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

---

## ✅ PASO 6: CONFIGURAR ARCHIVOS ESTÁTICOS Y MEDIA

### 6.1 Configurar rutas estáticas en dashboard
```
# En Web → Static files:

# URL: /static/
# Directory: /home/atlantareciclajes/e_garage/staticfiles/

# URL: /media/
# Directory: /home/atlantareciclajes/e_garage/media/
```

### 6.2 Crear directorios necesarios
```bash
# Crear directorios si no existen
mkdir -p ~/e_garage/staticfiles
mkdir -p ~/e_garage/media
mkdir -p ~/e_garage/logs

# Permisos
chmod 755 ~/e_garage/staticfiles
chmod 755 ~/e_garage/media
chmod 755 ~/e_garage/logs
```

---

## ✅ PASO 7: CONFIGURACIÓN DE EMAIL

### 7.1 Verificar configuración de email
```python
# Ya configurado en settings_production.py:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.atlantareciclajes.cl'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'contacto@atlantareciclajes.cl'
EMAIL_HOST_PASSWORD = 'laila2013@'
```

### 7.2 Probar envío de emails
```bash
# En consola Django
python manage.py shell --settings=e_garage.settings_production

# Ejecutar en shell:
from django.core.mail import send_mail
send_mail(
    'Test eGarage',
    'Sistema funcionando correctamente.',
    'contacto@atlantareciclajes.cl',
    ['contacto@atlantareciclajes.cl'],
    fail_silently=False,
)
```

---

## ✅ PASO 8: CARGAR DATOS INICIALES

### 8.1 Ejecutar scripts de carga de datos
```bash
# Activar virtualenv
workon venv_egarage
cd ~/e_garage

# Cargar datos de prueba (si es necesario)
python manage.py shell --settings=e_garage.settings_production < crear_usuarios_prueba.py
```

### 8.2 Verificar datos cargados
```bash
# Verificar en admin
# https://e-garage-atlantareciclajes.pythonanywhere.com/admin/

# O via shell
python manage.py shell --settings=e_garage.settings_production
# >>> from django.contrib.auth.models import User
# >>> User.objects.count()
```

---

## ✅ PASO 9: PRUEBAS Y VALIDACIÓN

### 9.1 Verificar URLs principales
```bash
# Testear URLs principales:
curl -I https://e-garage-atlantareciclajes.pythonanywhere.com/
curl -I https://e-garage-atlantareciclajes.pythonanywhere.com/admin/
curl -I https://e-garage-atlantareciclajes.pythonanywhere.com/accounts/login/
```

### 9.2 Verificar logs
```bash
# Ver logs de Django
tail -f ~/e_garage/django.log

# Ver logs de PythonAnywhere
# En dashboard → Tasks → View logs
```

---

## ✅ PASO 10: COMANDOS DE MANTENIMIENTO

### 10.1 Actualizar código
```bash
# Actualizar desde repositorio
cd ~/e_garage
git pull origin main

# Activar virtualenv
workon venv_egarage

# Instalar nuevas dependencias (si las hay)
pip install -r requirements_pythonanywhere.txt

# Ejecutar migraciones
python manage.py migrate --settings=e_garage.settings_production

# Recopilar estáticos
python manage.py collectstatic --noinput --settings=e_garage.settings_production

# Reiniciar aplicación web
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

### 10.2 Backup de base de datos
```bash
# Hacer backup de la base de datos
mysqldump -h atlantareciclajes.mysql.pythonanywhere-services.com \
          -u atlantareciclajes -p \
          'atlantareciclajes$egarage' > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🔧 TROUBLESHOOTING

### Problema 1: Error 500 - Internal Server Error
```bash
# Verificar logs
tail -f ~/e_garage/django.log

# Verificar configuración WSGI
python manage.py check --settings=e_garage.settings_production

# Verificar permisos
chmod 755 ~/e_garage
```

### Problema 2: No se cargan archivos estáticos
```bash
# Recopilar estáticos
python manage.py collectstatic --noinput --settings=e_garage.settings_production

# Verificar configuración en dashboard Web → Static files
```

### Problema 3: Error de base de datos
```bash
# Verificar conexión
python manage.py dbshell --settings=e_garage.settings_production

# Verificar migraciones
python manage.py showmigrations --settings=e_garage.settings_production
```

---

## 🚀 COMANDOS RÁPIDOS PARA COPIAR/PEGAR

### Activar entorno y ir al proyecto
```bash
workon venv_egarage && cd ~/e_garage
```

### Actualizar proyecto completo
```bash
workon venv_egarage && cd ~/e_garage && git pull && pip install -r requirements_pythonanywhere.txt && python manage.py migrate --settings=e_garage.settings_production && python manage.py collectstatic --noinput --settings=e_garage.settings_production && touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

### Verificar estado del proyecto
```bash
workon venv_egarage && cd ~/e_garage && python manage.py check --settings=e_garage.settings_production
```

---

## 📱 INFORMACIÓN DE ACCESO

- **URL Principal:** https://e-garage-atlantareciclajes.pythonanywhere.com/
- **Admin:** https://e-garage-atlantareciclajes.pythonanywhere.com/admin/
- **Login:** https://e-garage-atlantareciclajes.pythonanywhere.com/accounts/login/

---

## 📞 CONTACTO DE SOPORTE

- **Email:** contacto@atlantareciclajes.cl
- **Sistema:** eGarage v1.0
- **Fecha de Deploy:** $(date +"%d/%m/%Y")

---

**¡Proyecto eGarage desplegado exitosamente en PythonAnywhere! 🚀**
