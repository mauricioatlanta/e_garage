# 🚀 GUÍA DE ACTUALIZACIÓN SEGURA - PythonAnywhere

**Fecha**: 26 de octubre de 2025  
**Objetivo**: Actualizar eGarage sin perder datos de suscriptores

---

## ⚠️ **ADVERTENCIA IMPORTANTE**

**NUNCA actualices producción sin backup completo.**

Tienes suscriptores reales registrados. Un error puede causar:
- ❌ Pérdida de datos
- ❌ Sistema no funcional
- ❌ Clientes molestos
- ❌ Pérdida de ingresos

**Sigue TODOS los pasos en orden.**

---

## 📋 **ANTES DE COMENZAR**

### **Información Necesaria:**
```
□ Usuario PythonAnywhere: _______________
□ Nombre de la app: _______________
□ Ruta del proyecto: /home/usuario/egarage/
□ Base de datos: SQLite o MySQL/PostgreSQL?
□ Email configurado para notificaciones: _______________
□ Backup reciente existe? □ Sí □ No
```

---

## 🔍 **PASO 0: EVALUACIÓN INICIAL**

### **0.1. Conectarse a PythonAnywhere Console**

```bash
# Ir a: pythonanywhere.com → Dashboard → Consoles
# Abrir "Bash console"

# Verificar ruta del proyecto
cd /home/tu_usuario/
ls -la

# Entrar al proyecto
cd egarage
ls -la

# Ver archivos críticos
ls -la db.sqlite3     # Base de datos
ls -la media/         # Archivos subidos
ls -la gestion_taller/settings.py
```

### **0.2. Verificar Versión Actual**

```bash
# Ver qué archivos tienes
ls -la

# Ver última modificación
ls -lt | head -20

# Ver si hay .git
ls -la .git/

# ¿Cuántos suscriptores tienes?
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.count()
>>> from taller.models.empresa import Empresa
>>> Empresa.objects.count()
>>> exit()
```

---

## 💾 **PASO 1: BACKUP COMPLETO (¡CRÍTICO!)**

### **1.1. Backup de Base de Datos**

#### **Si usas SQLite:**
```bash
# En PythonAnywhere Console
cd /home/tu_usuario/egarage/

# Crear carpeta de backups
mkdir -p backups

# Backup de la base de datos
cp db.sqlite3 backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3

# Verificar que se creó
ls -lh backups/

# Descargar a tu PC (importante)
# Desde tu PC, usar FileZilla:
# Conectar a: tu_usuario.pythonanywhere.com
# Puerto: 22 (SFTP)
# Descargar: /home/tu_usuario/egarage/backups/db_backup_*.sqlite3
```

#### **Si usas MySQL/PostgreSQL:**
```bash
# MySQL
mysqldump -u tu_usuario -p tu_database > backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# PostgreSQL
pg_dump tu_database > backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# Descargar a tu PC con FileZilla
```

### **1.2. Backup de Archivos Media**

```bash
# Backup de archivos subidos (comprobantes, fotos, etc.)
cd /home/tu_usuario/egarage/

# Comprimir media/
tar -czf backups/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/

# Verificar
ls -lh backups/

# Descargar a tu PC con FileZilla
```

### **1.3. Backup de Settings**

```bash
# Copiar settings actual
cp gestion_taller/settings.py backups/settings_backup_$(date +%Y%m%d_%H%M%S).py

# Descargar a tu PC con FileZilla
```

### **1.4. Lista de Archivos Actuales**

```bash
# Crear lista de lo que tienes
find . -name "*.py" > backups/archivos_actuales.txt

# Descargar para comparar después
```

---

## 🎯 **PASO 2: PREPARAR ACTUALIZACIÓN EN TU PC**

### **2.1. Crear Paquete de Actualización**

En tu PC local (Windows):

```bash
cd E:\projecto\e_garage\

# Crear carpeta para subir
mkdir deploy_pythonanywhere

# Copiar SOLO archivos necesarios (NO todo)
# Ver lista abajo
```

### **2.2. Archivos a ACTUALIZAR**

**✅ COPIAR (código nuevo):**
```
deploy_pythonanywhere/
├── taller/
│   ├── views_extra/
│   │   ├── signup_complete.py (NUEVO)
│   │   ├── payment_views.py (NUEVO)
│   │   ├── paypal_webhook.py (NUEVO)
│   │   └── admin_payment_views.py (NUEVO)
│   ├── models/
│   │   └── pago.py (ACTUALIZADO)
│   ├── forms/
│   │   └── signup_complete.py (NUEVO)
│   ├── signals.py (NUEVO)
│   ├── apps.py (ACTUALIZADO)
│   └── management/
│       └── commands/
│           ├── enviar_recordatorios.py (NUEVO)
│           └── verificar_suscripciones.py (NUEVO)
├── templates/
│   ├── account/
│   │   ├── login.html (ACTUALIZADO)
│   │   └── email/ (NUEVO)
│   ├── auth/
│   │   └── signup.html (NUEVO)
│   ├── email/ (NUEVO - 6 templates)
│   ├── public/
│   │   └── landing_chile_completa.html (NUEVO)
│   └── onboarding/
│       └── bienvenida_usa.html (ACTUALIZADO)
├── gestion_taller/
│   ├── urls.py (ACTUALIZADO)
│   └── settings.py (⚠️ CUIDADO - comparar manualmente)
└── requirements.txt (verificar nuevas dependencias)
```

**❌ NO COPIAR (datos existentes):**
```
❌ db.sqlite3 (tu base de datos actual)
❌ media/ (archivos de suscriptores)
❌ staticfiles/ (se regenera)
❌ __pycache__/
❌ *.pyc
❌ .env (credenciales producción)
```

### **2.3. Comprimir Paquete**

```bash
# En tu PC
cd E:\projecto\e_garage\

# Crear ZIP con solo los archivos actualizados
# Usar WinRAR o 7-Zip para crear:
egarage_update_20251026.zip
```

---

## 📤 **PASO 3: SUBIR ACTUALIZACIÓN CON FILEZILLA**

### **3.1. Configurar FileZilla**

```
Host: tu_usuario.pythonanywhere.com
Protocol: SFTP - SSH File Transfer Protocol
Port: 22
Username: tu_usuario
Password: tu_password_pythonanywhere
```

### **3.2. Navegar a la Carpeta Temporal**

```
# En FileZilla, lado remoto (servidor):
Ir a: /home/tu_usuario/

# Crear carpeta temporal
Clic derecho → Create directory → "egarage_update"
```

### **3.3. Subir Archivo ZIP**

```
# Arrastrar desde tu PC (lado izquierdo) a servidor (lado derecho):
egarage_update_20251026.zip → /home/tu_usuario/egarage_update/

# Esperar que termine la subida (puede tardar varios minutos)
```

---

## 🔧 **PASO 4: INSTALAR ACTUALIZACIÓN (Momento Crítico)**

### **4.1. Descomprimir Actualización**

```bash
# En PythonAnywhere Console
cd /home/tu_usuario/egarage_update/

# Descomprimir
unzip egarage_update_20251026.zip

# Verificar contenido
ls -la
```

### **4.2. Comparar Settings (IMPORTANTE)**

```bash
# Ver diferencias entre settings antiguo y nuevo
diff /home/tu_usuario/egarage/gestion_taller/settings.py \
     /home/tu_usuario/egarage_update/gestion_taller/settings.py

# ⚠️ NO sobrescribir settings.py directamente
# COPIAR MANUALMENTE solo las líneas nuevas
```

**Líneas nuevas en settings.py que DEBES agregar:**
```python
# En ACCOUNT_EMAIL_VERIFICATION
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
```

### **4.3. Copiar Archivos Nuevos/Actualizados**

```bash
cd /home/tu_usuario/

# OPCIÓN A: Copiar selectivamente (MÁS SEGURO)
cp -r egarage_update/taller/views_extra/signup_complete.py egarage/taller/views_extra/
cp -r egarage_update/taller/views_extra/payment_views.py egarage/taller/views_extra/
cp -r egarage_update/taller/views_extra/paypal_webhook.py egarage/taller/views_extra/
cp -r egarage_update/taller/models/pago.py egarage/taller/models/
cp -r egarage_update/taller/signals.py egarage/taller/
cp -r egarage_update/taller/forms/ egarage/taller/
cp -r egarage_update/taller/management/ egarage/taller/
cp -r egarage_update/templates/email/ egarage/templates/
cp -r egarage_update/templates/account/email/ egarage/templates/account/
cp -r egarage_update/templates/auth/ egarage/templates/
cp -r egarage_update/templates/public/landing_chile_completa.html egarage/templates/public/

# ⚠️ URLs - Cuidado, verificar manualmente primero
cp egarage/gestion_taller/urls.py egarage/backups/urls_old.py
cp egarage_update/gestion_taller/urls.py egarage/gestion_taller/

# OPCIÓN B: Copiar todo EXCEPTO db y media (MÁS RÁPIDO pero más arriesgado)
# ⚠️ Solo si estás seguro
rsync -av --exclude='db.sqlite3' --exclude='media/' --exclude='staticfiles/' \
      egarage_update/ egarage/
```

### **4.4. Instalar Nuevas Dependencias**

```bash
cd /home/tu_usuario/egarage/

# Verificar si hay nuevas dependencias
diff requirements.txt ../egarage_update/requirements.txt

# Instalar (si hay cambios)
pip install --user -r requirements.txt
```

---

## 🗄️ **PASO 5: MIGRAR BASE DE DATOS**

### **5.1. Verificar Migraciones Pendientes**

```bash
cd /home/tu_usuario/egarage/

# Ver migraciones pendientes
python manage.py showmigrations

# Ver si hay nuevas
python manage.py makemigrations --dry-run
```

### **5.2. Ejecutar Migraciones**

```bash
# ⚠️ Este es el momento crítico
# La base de datos se va a actualizar

# Primero, hacer otro backup
cp db.sqlite3 backups/db_antes_migracion_$(date +%Y%m%d_%H%M%S).sqlite3

# Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# Verificar que no hubo errores
echo $?  # Si retorna 0, todo bien
```

---

## 🎨 **PASO 6: RECOLECTAR ARCHIVOS ESTÁTICOS**

```bash
cd /home/tu_usuario/egarage/

# Limpiar archivos estáticos viejos
python manage.py collectstatic --clear --noinput

# Recolectar nuevos
python manage.py collectstatic --noinput
```

---

## ♻️ **PASO 7: REINICIAR APLICACIÓN**

### **7.1. Recargar Web App**

```
1. Ir a: pythonanywhere.com → Web
2. Buscar tu app: tu_usuario.pythonanywhere.com
3. Clic en botón verde "Reload tu_usuario.pythonanywhere.com"
4. Esperar 10-15 segundos
```

---

## ✅ **PASO 8: VERIFICACIÓN**

### **8.1. Verificar Homepage**

```
1. Abrir: https://tu_usuario.pythonanywhere.com/
2. Debería cargar sin errores
3. Verificar que no sale error 500
```

### **8.2. Verificar Login**

```
1. Ir a: /accounts/login/
2. Iniciar sesión con cuenta existente
3. Verificar que funciona
4. Ver dashboard
```

### **8.3. Verificar Suscriptores Existentes**

```bash
# En Console
cd /home/tu_usuario/egarage/
python manage.py shell

>>> from django.contrib.auth.models import User
>>> User.objects.count()  # Mismo número que antes
>>> 
>>> from taller.models.empresa import Empresa
>>> Empresa.objects.count()  # Mismo número que antes
>>>
>>> # Verificar primer usuario
>>> user = User.objects.first()
>>> print(f"{user.username} - {user.email}")
>>>
>>> # Verificar empresa
>>> empresa = Empresa.objects.first()
>>> print(f"{empresa.nombre_taller} - {empresa.suscripcion_activa}")
>>> exit()
```

### **8.4. Verificar Registro Nuevo**

```
1. Abrir navegador de incógnito
2. Ir a: /cl/ o /us/
3. Intentar registrar usuario nuevo
4. Verificar que pide confirmación de email
5. (Usar email de prueba real)
```

---

## 🚨 **PASO 9: SI ALGO SALE MAL (Rollback)**

### **9.1. Restaurar Base de Datos**

```bash
cd /home/tu_usuario/egarage/

# Detener todo
# (No hay que detener en PythonAnywhere, solo reload después)

# Restaurar backup
cp backups/db_backup_20251026_*.sqlite3 db.sqlite3

# Recargar app
```

### **9.2. Restaurar Código**

```bash
# Si guardaste todo en Git (recomendado)
git reset --hard HEAD~1

# Si no, restaurar manualmente desde backup
# Contactarme para ayuda de emergencia
```

---

## 📝 **CHECKLIST FINAL**

### **Antes de Actualizar:**
```
□ Backup de base de datos descargado a PC
□ Backup de media/ descargado a PC
□ Backup de settings.py descargado a PC
□ Lista de usuarios actuales anotada
□ Paquete de actualización preparado
□ FileZilla configurado y conectado
```

### **Durante Actualización:**
```
□ Archivos subidos a carpeta temporal
□ Descomprimido en servidor
□ Settings.py actualizado manualmente
□ Archivos copiados selectivamente
□ Migraciones ejecutadas sin errores
□ Estáticos recolectados
□ App recargada
```

### **Después de Actualizar:**
```
□ Homepage carga sin errores
□ Login funciona
□ Número de usuarios igual que antes
□ Dashboard de usuario existente funciona
□ Registro nuevo funciona
□ Emails se envían (si configurado)
□ No hay errores en logs
```

---

## ⏰ **MEJOR MOMENTO PARA ACTUALIZAR**

```
✅ MEJOR: Madrugada (2-4 AM) - Menos usuarios activos
✅ BUENO: Fines de semana temprano
❌ MALO: Horario laboral (9 AM - 6 PM)
❌ PEOR: Viernes tarde (si falla, todo el fin de semana mal)
```

---

## 🔒 **MEDIDAS DE SEGURIDAD EXTRA**

### **1. Modo Mantenimiento (Opcional)**

```python
# Crear: templates/maintenance.html
# Activar temporalmente mientras actualizas

# En settings.py
MAINTENANCE_MODE = True

# Middleware que muestra "En mantenimiento"
```

### **2. Notificar a Usuarios**

```
Si tienes muchos usuarios activos:
1. Enviar email 24h antes: "Mantenimiento programado"
2. Poner banner en dashboard: "Actualización mañana a las 3 AM"
3. Estimar downtime: "Aproximadamente 30 minutos"
```

---

## 📞 **SI NECESITAS AYUDA**

### **Logs a Revisar:**
```bash
# Error logs de PythonAnywhere
# Dashboard → Web → Log files → Error log

# Ver últimas 50 líneas
tail -50 /var/log/tu_usuario.pythonanywhere.com.error.log

# Ver en tiempo real (si estás actualizando)
tail -f /var/log/tu_usuario.pythonanywhere.com.error.log
```

### **Información a Tener Lista:**
```
- Mensaje de error exacto
- Qué paso estabas ejecutando
- Output del comando que falló
- Número de usuarios antes de actualizar
- Backups disponibles
```

---

## 🎯 **RESUMEN EJECUTIVO**

### **Actualización Segura en 9 Pasos:**

1. **Backup** → db.sqlite3, media/, settings.py
2. **Preparar** → Crear paquete actualización en PC
3. **Subir** → FileZilla a carpeta temporal
4. **Instalar** → Copiar archivos selectivamente
5. **Migrar** → python manage.py migrate
6. **Estáticos** → collectstatic
7. **Reiniciar** → Reload app
8. **Verificar** → Probar todo
9. **Rollback** → Si algo falla

### **Tiempo Estimado:**
- Backup: 10 minutos
- Preparar: 15 minutos
- Subir: 10 minutos (depende internet)
- Instalar: 20 minutos
- Migrar: 5 minutos
- Verificar: 10 minutos
**Total: 70 minutos aproximadamente**

---

## ✅ **VENTAJAS DE ESTE MÉTODO**

- ✅ **Seguro**: Backups completos antes de tocar nada
- ✅ **Reversible**: Puedes volver atrás si falla
- ✅ **Selectivo**: Solo actualizas lo necesario
- ✅ **Verificable**: Chequeas cada paso
- ✅ **Sin pérdida de datos**: Base de datos intacta

---

**NUNCA actualices producción sin backup. NUNCA.**

¿Tienes preguntas antes de comenzar? 🎯

