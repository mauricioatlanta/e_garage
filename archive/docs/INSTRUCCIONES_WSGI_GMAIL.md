# 📧 Configurar Gmail en PythonAnywhere - Método WSGI

## ✅ Solución: Agregar Variables en el Archivo WSGI

Como no tienes la opción "Environment variables" en tu panel, vamos a agregar las variables directamente en el archivo WSGI.

---

## 🔧 Paso 1: Editar el Archivo WSGI

1. **En PythonAnywhere, ve a la pestaña "Web"**
2. **Busca la sección "WSGI configuration file"**
3. **Haz clic en el enlace del archivo WSGI** (debería ser algo como `/var/www/www_egarage_cl_wsgi.py`)
4. **Se abrirá un editor de texto**

---

## 📝 Paso 2: Reemplazar el Contenido

**Copia y pega este código completo** en el editor del archivo WSGI:

```python
#!/usr/bin/env python
# ======================================================
# WSGI Configuration para PythonAnywhere - eGarage
# CONFIGURADO PARA GMAIL
# ======================================================
# Archivo: /var/www/www_egarage_cl_wsgi.py
# ======================================================

import os
import sys
from pathlib import Path

# Ruta del proyecto
project_home = "/home/atlantareciclajes/apps/egarage/current"

# Agregar directorio del proyecto al path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Cambiar al directorio del proyecto
os.chdir(project_home)

# ======================================================
# CONFIGURACION DE VARIABLES DE ENTORNO PARA GMAIL
# ======================================================
# Estas variables se cargan ANTES de Django
# ======================================================

# Configuración de Gmail
os.environ['EMAIL_HOST'] = 'smtp.gmail.com'
os.environ['EMAIL_PORT'] = '587'
os.environ['EMAIL_USE_TLS'] = 'True'
os.environ['EMAIL_USE_SSL'] = 'False'
os.environ['EMAIL_HOST_USER'] = 'mauricioatlanta@gmail.com'
os.environ['EMAIL_PASSWORD'] = 'aohulwlfwzfvqajz'  # App Password de Gmail
os.environ['DEFAULT_FROM_EMAIL'] = 'eGarage <mauricioatlanta@gmail.com>'

# Cargar variables de entorno (.env) si existe (opcional)
try:
    from dotenv import load_dotenv
    env_path = Path(project_home) / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv no está instalado, continuar sin él

# Configurar Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

# Cargar aplicación WSGI
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

---

## 💾 Paso 3: Guardar y Reiniciar

1. **Haz clic en "Save"** o presiona `Ctrl+S` para guardar
2. **Vuelve a la pestaña "Web"**
3. **Haz clic en el botón "Reload"** o **"Restart"** de tu aplicación web
4. **Espera unos segundos** a que se reinicie

---

## 🧪 Paso 4: Probar

### Opción A: Usar Django Shell

1. Ve a la pestaña **"Consoles"**
2. Abre una consola de **Bash**
3. Ejecuta:

```bash
cd /home/atlantareciclajes/apps/egarage/current
python3.10 manage.py shell
```

4. En el shell de Django:

```python
from django.core.mail import send_mail
from django.conf import settings

# Verificar configuración
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")

# Enviar correo de prueba
send_mail(
    'Test Gmail - eGarage',
    'Este es un correo de prueba desde el servidor.',
    settings.DEFAULT_FROM_EMAIL,
    ['mauricioatlanta@gmail.com'],
    fail_silently=False,
)
```

### Opción B: Probar Registro de Usuario

1. Ve a tu sitio web: `https://www.egarage.cl`
2. Intenta registrar un nuevo usuario
3. Verifica que reciba el correo de bienvenida en `mauricioatlanta@gmail.com`

---

## ✅ Verificación

Después de configurar, verifica:

1. **Las variables se cargan correctamente**:
   ```python
   # En Django shell
   from django.conf import settings
   print(settings.EMAIL_HOST)  # Debe mostrar: smtp.gmail.com
   ```

2. **El correo se envía**:
   - Prueba con el método de arriba
   - Revisa tu bandeja de entrada

3. **El registro funciona**:
   - Registra un nuevo usuario
   - Verifica que reciba el correo de bienvenida

---

## 🔍 Solución de Problemas

### Error: "Module not found" o "Import error"

**Causa**: El archivo WSGI no puede encontrar el proyecto.

**Solución**: Verifica que la ruta `project_home` sea correcta:
```python
project_home = "/home/atlantareciclajes/apps/egarage/current"
```

### Error: "Username and Password not accepted"

**Causa**: La App Password no está correcta.

**Solución**: 
1. Verifica que la App Password sea: `aohulwlfwzfvqajz` (sin espacios)
2. Si no funciona, genera una nueva App Password en: https://myaccount.google.com/apppasswords

### Las variables no se cargan

**Causa**: El archivo WSGI no se guardó o no se reinició la aplicación.

**Solución**:
1. Verifica que guardaste el archivo WSGI
2. Reinicia la aplicación web
3. Verifica en Django shell que las variables estén cargadas

---

## 📋 Checklist

- [ ] Archivo WSGI editado con las variables de Gmail
- [ ] Archivo WSGI guardado
- [ ] Aplicación web reiniciada
- [ ] Prueba de correo exitosa desde Django shell
- [ ] Correo de bienvenida funciona en registro de usuario

---

## 🔒 Seguridad

**⚠️ IMPORTANTE**: 
- La App Password `aohulwlfwzfvqajz` está visible en el código WSGI
- Esto es aceptable porque el archivo WSGI solo es accesible por ti en PythonAnywhere
- Si necesitas más seguridad, considera usar un archivo `.env` (ver método alternativo abajo)

---

## 🔄 Método Alternativo: Usar Archivo .env

Si prefieres no tener la contraseña en el archivo WSGI, puedes:

1. **Crear un archivo `.env`** en el directorio del proyecto:
   ```bash
   cd /home/atlantareciclajes/apps/egarage/current
   nano .env
   ```

2. **Agregar las variables**:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   EMAIL_HOST_USER=mauricioatlanta@gmail.com
   EMAIL_PASSWORD=aohulwlfwzfvqajz
   DEFAULT_FROM_EMAIL=eGarage <mauricioatlanta@gmail.com>
   ```

3. **El archivo WSGI ya está configurado para cargar el .env** (si existe)

---

**Última actualización**: Diciembre 2024
