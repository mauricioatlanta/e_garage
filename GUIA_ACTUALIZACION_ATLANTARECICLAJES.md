    # 🚀 GUÍA DE ACTUALIZACIÓN EGARAGE - ATLANTARECICLAJES

**Cuenta PythonAnywhere**: atlantareciclajes  
**URL**: https://atlantareciclajes.pythonanywhere.com/  
**Fecha**: 26 de octubre de 2025

---

## 📋 **INFORMACIÓN DE TU CUENTA**

```
Usuario: atlantareciclajes
URL producción: https://atlantareciclajes.pythonanywhere.com/
Ruta proyecto: /home/atlantareciclajes/egarage/
Base de datos: SQLite (probablemente db.sqlite3)
```

---

## 🎯 **PASO A PASO PARA ATLANTARECICLAJES**

### **PASO 1: BACKUP COMPLETO (15 minutos)**

#### **1.1. Conectar a Console de PythonAnywhere**

```
1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Login con tus credenciales
3. Ir a pestaña "Consoles"
4. Clic en "Bash" (crear nueva consola bash)
```

#### **1.2. Hacer Backup de TODO**

```bash
# En la consola Bash que se abre:

# Ir al proyecto
cd /home/atlantareciclajes/egarage/

# Ver qué tienes actualmente
ls -la

# Crear carpeta de backups
mkdir -p backups_$(date +%Y%m%d)

# Backup de base de datos (CRÍTICO)
cp db.sqlite3 backups_$(date +%Y%m%d)/

# Backup de media (archivos subidos)
cp -r media/ backups_$(date +%Y%m%d)/ 2>/dev/null || echo "No media folder"

# Backup de settings
cp gestion_taller/settings.py backups_$(date +%Y%m%d)/

# Ver cuántos usuarios tienes (ANOTA ESTE NÚMERO)
python manage.py shell << EOF
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
print(f"Usuarios: {User.objects.count()}")
print(f"Empresas: {Empresa.objects.count()}")
EOF

# Comprimir todo el backup
cd /home/atlantareciclajes/
tar -czf egarage_backup_completo_$(date +%Y%m%d_%H%M).tar.gz egarage/
```

#### **1.3. Descargar Backup a tu PC con FileZilla**

**Configuración FileZilla:**
```
Host: atlantareciclajes.pythonanywhere.com
Protocol: SFTP - SSH File Transfer Protocol
Logon Type: Normal
User: atlantareciclajes
Password: [tu password de PythonAnywhere]
Port: 22
```

**Archivos a descargar:**
```
1. Conectar con FileZilla
2. Navegar a: /home/atlantareciclajes/
3. Descargar a tu PC:
   - egarage_backup_completo_20251026_*.tar.gz
   - egarage/db.sqlite3 (copia adicional por seguridad)
   - egarage/media/ (si existe)

4. Guardar en: E:\backups_egarage_pythonanywhere\
```

---

## 📤 **PASO 2: PREPARAR ACTUALIZACIÓN EN TU PC (10 minutos)**

### **2.1. Crear Carpeta de Deploy**

```bash
# En tu PC (Windows):
cd E:\projecto\e_garage\

# Crear carpeta limpia
mkdir deploy_atlantareciclajes

# Copiar SOLO archivos a actualizar
```

### **2.2. Lista de Archivos a Copiar**

**Copia estos archivos/carpetas desde tu proyecto local:**

```
deploy_atlantareciclajes\
│
├── templates\
│   ├── account\
│   │   ├── login.html
│   │   └── email\
│   │       ├── email_confirmation_subject.txt
│   │       ├── email_confirmation_message.txt
│   │       └── email_confirmation_message.html
│   ├── auth\
│   │   └── signup.html
│   ├── email\
│   │   ├── comprobante_recibido.html
│   │   ├── pago_confirmado.html
│   │   ├── recordatorio_vencimiento.html
│   │   ├── suscripcion_vencida.html
│   │   └── admin_pago_nuevo.html
│   ├── public\
│   │   └── landing_chile_completa.html
│   └── onboarding\
│       └── bienvenida_usa.html
│
├── taller\
│   ├── views_extra\
│   │   ├── signup_complete.py
│   │   ├── payment_views.py
│   │   ├── paypal_webhook.py
│   │   └── admin_payment_views.py
│   ├── models\
│   │   └── pago.py
│   ├── forms\
│   │   └── signup_complete.py
│   ├── signals.py
│   ├── apps.py
│   └── management\
│       ├── __init__.py
│       └── commands\
│           ├── __init__.py
│           ├── enviar_recordatorios.py
│           └── verificar_suscripciones.py
│
├── gestion_taller\
│   ├── urls.py
│   └── settings_CHANGES.txt  ← (ver abajo)
│
└── INSTRUCCIONES.txt
```

### **2.3. Crear Archivo de Cambios de Settings**

Crea `deploy_atlantareciclajes\gestion_taller\settings_CHANGES.txt`:

```txt
====================================
CAMBIOS PARA settings.py
====================================

BUSCAR esta línea (aproximadamente línea 74-77):
--------------------------------------------------
ACCOUNT_EMAIL_VERIFICATION = os.getenv(
    "ACCOUNT_EMAIL_VERIFICATION", "none" if DEBUG else "mandatory"
)
ACCOUNT_EMAIL_REQUIRED = False

REEMPLAZAR por:
--------------------------------------------------
ACCOUNT_EMAIL_VERIFICATION = os.getenv(
    "ACCOUNT_EMAIL_VERIFICATION", "mandatory"  # 🔒 Siempre obligatorio
)
ACCOUNT_EMAIL_REQUIRED = True  # 🔒 Email es REQUERIDO

--------------------------------------------------

BUSCAR esta línea (aproximadamente línea 78):
--------------------------------------------------
ACCOUNT_CONFIRM_EMAIL_ON_GET = env_bool(
    "ACCOUNT_CONFIRM_EMAIL_ON_GET", False if not DEBUG else True
)

REEMPLAZAR por:
--------------------------------------------------
ACCOUNT_CONFIRM_EMAIL_ON_GET = True  # Confirmar email con un solo clic

====================================
FIN DE CAMBIOS
====================================
```

### **2.4. Comprimir Paquete**

```bash
# En tu PC:
cd E:\projecto\e_garage\

# Comprimir con WinRAR o 7-Zip:
# Seleccionar carpeta: deploy_atlantareciclajes
# Clic derecho → 7-Zip → Add to archive
# Nombre: egarage_update_atlantareciclajes.zip
```

---

## 📤 **PASO 3: SUBIR ACTUALIZACIÓN (10 minutos)**

### **3.1. Subir con FileZilla**

```
1. Abrir FileZilla
2. Conectar a: atlantareciclajes.pythonanywhere.com (puerto 22, SFTP)
3. Lado remoto, ir a: /home/atlantareciclajes/
4. Crear nueva carpeta: "egarage_update"
5. Entrar a: /home/atlantareciclajes/egarage_update/
6. Desde tu PC, arrastrar: egarage_update_atlantareciclajes.zip
7. Esperar que termine la subida (puede tardar 5-10 min)
```

---

## 🔧 **PASO 4: INSTALAR ACTUALIZACIÓN (20 minutos)**

### **4.1. Descomprimir en Servidor**

```bash
# En PythonAnywhere Console (Bash):
cd /home/atlantareciclajes/egarage_update/

# Descomprimir
unzip egarage_update_atlantareciclajes.zip

# Verificar contenido
ls -la
cd deploy_atlantareciclajes/
ls -la
```

### **4.2. Actualizar Settings.py MANUALMENTE**

```bash
# Ver los cambios necesarios
cd /home/atlantareciclajes/egarage_update/deploy_atlantareciclajes/gestion_taller/
cat settings_CHANGES.txt

# Editar settings actual
cd /home/atlantareciclajes/egarage/gestion_taller/
nano settings.py

# Buscar las líneas indicadas (Ctrl+W para buscar)
# Hacer los cambios como indica settings_CHANGES.txt
# Guardar: Ctrl+O, Enter
# Salir: Ctrl+X
```

### **4.3. Copiar Archivos Nuevos**

```bash
cd /home/atlantareciclajes/

# Templates - Email
mkdir -p egarage/templates/email/
cp egarage_update/deploy_atlantareciclajes/templates/email/* egarage/templates/email/

mkdir -p egarage/templates/account/email/
cp egarage_update/deploy_atlantareciclajes/templates/account/email/* egarage/templates/account/email/

mkdir -p egarage/templates/auth/
cp egarage_update/deploy_atlantareciclajes/templates/auth/* egarage/templates/auth/

# Templates - Landing completa
cp egarage_update/deploy_atlantareciclajes/templates/public/landing_chile_completa.html egarage/templates/public/

# Templates - USA actualizada
cp egarage_update/deploy_atlantareciclajes/templates/onboarding/bienvenida_usa.html egarage/templates/onboarding/

# Login actualizado
cp egarage_update/deploy_atlantareciclajes/templates/account/login.html egarage/templates/account/

# Views Extra
cp egarage_update/deploy_atlantareciclajes/taller/views_extra/signup_complete.py egarage/taller/views_extra/
cp egarage_update/deploy_atlantareciclajes/taller/views_extra/payment_views.py egarage/taller/views_extra/
cp egarage_update/deploy_atlantareciclajes/taller/views_extra/paypal_webhook.py egarage/taller/views_extra/
cp egarage_update/deploy_atlantareciclajes/taller/views_extra/admin_payment_views.py egarage/taller/views_extra/

# Models
cp egarage_update/deploy_atlantareciclajes/taller/models/pago.py egarage/taller/models/

# Forms
mkdir -p egarage/taller/forms/
cp egarage_update/deploy_atlantareciclajes/taller/forms/signup_complete.py egarage/taller/forms/

# Signals y Apps
cp egarage_update/deploy_atlantareciclajes/taller/signals.py egarage/taller/
cp egarage_update/deploy_atlantareciclajes/taller/apps.py egarage/taller/

# Management Commands
mkdir -p egarage/taller/management/commands/
cp egarage_update/deploy_atlantareciclajes/taller/management/__init__.py egarage/taller/management/
cp egarage_update/deploy_atlantareciclajes/taller/management/commands/* egarage/taller/management/commands/

# URLs
cp egarage/gestion_taller/urls.py egarage/backups_$(date +%Y%m%d)/urls_old.py
cp egarage_update/deploy_atlantareciclajes/gestion_taller/urls.py egarage/gestion_taller/

# Verificar que se copiaron
ls -la egarage/templates/email/
ls -la egarage/taller/views_extra/
ls -la egarage/taller/management/commands/
```

### **4.4. Migrar Base de Datos**

```bash
cd /home/atlantareciclajes/egarage/

# Backup adicional antes de migrar
cp db.sqlite3 backups_$(date +%Y%m%d)/db_antes_migracion.sqlite3

# Ver migraciones pendientes
python manage.py showmigrations

# Crear migraciones si hay cambios en modelos
python manage.py makemigrations

# Ejecutar migraciones
python manage.py migrate

# Verificar que no hubo errores
echo $?
# Si retorna 0 = OK
# Si retorna otro número = ERROR
```

### **4.5. Recolectar Estáticos**

```bash
cd /home/atlantareciclajes/egarage/

# Limpiar y recolectar
python manage.py collectstatic --clear --noinput
python manage.py collectstatic --noinput
```

---

## ♻️ **PASO 5: REINICIAR APLICACIÓN (2 minutos)**

```
1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Clic en pestaña "Web"
3. Buscar tu aplicación web
4. Clic en botón verde grande:
   "Reload atlantareciclajes.pythonanywhere.com"
5. Esperar 10-15 segundos
```

---

## ✅ **PASO 6: VERIFICACIÓN (10 minutos)**

### **6.1. Verificar Homepage**

```
Abrir: https://atlantareciclajes.pythonanywhere.com/

¿Carga sin errores? ✅
¿Sale error 500? ❌ → Ver logs
```

### **6.2. Verificar Landing Chile**

```
Ir a: https://atlantareciclajes.pythonanywhere.com/cl/

¿Se ve la nueva landing completa con pricing? ✅
¿Tiene los 4 sectores y testimonios? ✅
```

### **6.3. Verificar Login Existente**

```
Ir a: https://atlantareciclajes.pythonanywhere.com/accounts/login/

Iniciar sesión con usuario existente
¿Funciona? ✅
¿Puedes ver dashboard? ✅
```

### **6.4. Verificar Número de Usuarios**

```bash
# En Console
cd /home/atlantareciclajes/egarage/
python manage.py shell << EOF
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
print(f"Usuarios DESPUÉS: {User.objects.count()}")
print(f"Empresas DESPUÉS: {Empresa.objects.count()}")
EOF

# Comparar con el número que anotaste en PASO 1.2
# Deben ser IGUALES
```

### **6.5. Probar Registro Nuevo**

```
1. Abrir navegador en modo incógnito
2. Ir a: https://atlantareciclajes.pythonanywhere.com/cl/
3. Clic "Registrarse"
4. Llenar formulario con email REAL tuyo
5. Submit
6. Debería mostrar: "Confirma tu email"
7. Revisar tu bandeja de entrada
8. ¿Llegó el email? ✅

Si NO llega email:
- Ver logs de error
- Verificar configuración EMAIL_* en settings
```

---

## 🚨 **SI ALGO SALE MAL - ROLLBACK**

### **Restaurar Backup:**

```bash
# En Console
cd /home/atlantareciclajes/egarage/

# Restaurar base de datos
cp backups_20251026/db.sqlite3 .

# O restaurar TODO desde el tar.gz
cd /home/atlantareciclajes/
rm -rf egarage/
tar -xzf egarage_backup_completo_20251026_*.tar.gz
```

**Luego:**
```
1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Web → Reload
3. ¡Volviste al estado anterior!
```

---

## 📊 **LOGS Y DEBUGGING**

### **Ver Logs de Error:**

```
1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Pestaña "Web"
3. Scroll down
4. Clic en: "Error log"
5. Ver últimas líneas para errores
```

### **Ver Logs en Console:**

```bash
# Ver últimas 50 líneas de error log
tail -50 /var/log/atlantareciclajes.pythonanywhere.com.error.log

# Ver en tiempo real
tail -f /var/log/atlantareciclajes.pythonanywhere.com.error.log
```

---

## ⏰ **MEJOR MOMENTO PARA HACERLO**

```
✅ Madrugada (2-4 AM hora Chile)
✅ Domingo temprano
❌ Horario laboral
❌ Viernes tarde
```

---

## 📝 **CHECKLIST RÁPIDO**

```
Antes:
□ Backup descargado a PC: E:\backups_egarage_pythonanywhere\
□ Número de usuarios anotado: _____
□ Paquete preparado: egarage_update_atlantareciclajes.zip

Durante:
□ Archivos subidos a /home/atlantareciclajes/egarage_update/
□ Settings.py actualizado manualmente
□ Archivos copiados (templates, views, models)
□ Migraciones ejecutadas: python manage.py migrate
□ Estáticos recolectados: collectstatic
□ App recargada en Web panel

Después:
□ Homepage carga: https://atlantareciclajes.pythonanywhere.com/
□ Landing Chile funciona: /cl/
□ Login funciona
□ Número de usuarios igual que antes
□ Registro nuevo pide confirmación email
```

---

## 🎯 **RESUMEN PARA ATLANTARECICLAJES**

**Tu ruta específica:**
```
Usuario: atlantareciclajes
Proyecto: /home/atlantareciclajes/egarage/
URL: https://atlantareciclajes.pythonanywhere.com/
Backup: /home/atlantareciclajes/egarage_backup_completo_*.tar.gz
```

**Tiempo total estimado: 1 hora**

**Momento recomendado: Madrugada del domingo**

---

## 📞 **SI TIENES DUDAS**

**Antes de comenzar, verifica:**
1. ¿Cuántos suscriptores tienes actualmente?
2. ¿Todos tienen muy poca información todavía?
3. ¿Tienes backup descargado a tu PC?
4. ¿Tienes acceso a FileZilla y Console?

**¿Todo listo? ¡Comienza con el PASO 1!** 🚀

---

**Última actualización**: 26 de octubre de 2025  
**Para**: atlantareciclajes  
**Proyecto**: eGarage

