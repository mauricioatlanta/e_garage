# 🚀 SCRIPTS DE ACTUALIZACIÓN AUTOMÁTICA - EGARAGE

**Para**: atlantareciclajes @ PythonAnywhere  
**Fecha**: 26 de octubre de 2025

---

## 📋 **ÍNDICE DE SCRIPTS**

```
scripts_deploy/
├── 1_backup.sh           → Hacer backup completo
├── 2_actualizar.sh       → Instalar actualización
├── 3_verificar.sh        → Verificar instalación
├── 4_rollback.sh         → Restaurar backup si algo falla
└── README_SCRIPTS.md     → Este archivo
```

---

## 🎯 **USO RÁPIDO**

### **Preparación en tu PC:**

```bash
# 1. Subir scripts con FileZilla
Conectar a: atlantareciclajes.pythonanywhere.com (puerto 22, SFTP)
Crear carpeta: /home/atlantareciclajes/scripts_deploy/
Subir todos los archivos .sh
```

### **Ejecución en PythonAnywhere:**

```bash
# 1. Abrir Console Bash en PythonAnywhere
cd /home/atlantareciclajes/scripts_deploy/

# 2. Dar permisos de ejecución
chmod +x *.sh

# 3. Ejecutar en orden:

# PASO 1: Backup
./1_backup.sh

# PASO 2: Subir archivos de actualización con FileZilla
# (Subir egarage_update_atlantareciclajes.zip a /home/atlantareciclajes/egarage_update/)

# PASO 3: Actualizar
./2_actualizar.sh

# PASO 4: Reload en Web panel
# (Ir a https://www.pythonanywhere.com/user/atlantareciclajes/ → Web → Reload)

# PASO 5: Verificar
./3_verificar.sh

# SI ALGO FALLA:
./4_rollback.sh
```

---

## 📖 **DESCRIPCIÓN DETALLADA**

### **Script 1: 1_backup.sh**

**Qué hace:**
- ✅ Crea carpeta de backup con fecha/hora
- ✅ Copia db.sqlite3
- ✅ Copia carpeta media/
- ✅ Copia settings.py
- ✅ Copia urls.py
- ✅ Cuenta usuarios actuales
- ✅ Crea archivo .tar.gz comprimido

**Tiempo:** 2-3 minutos

**Resultado:**
```
/home/atlantareciclajes/backups_20251026_153045/
├── db.sqlite3
├── media/
├── settings.py
├── urls.py
└── usuarios_count.txt

/home/atlantareciclajes/backup_completo_20251026_153045.tar.gz
```

**Uso:**
```bash
cd /home/atlantareciclajes/scripts_deploy/
./1_backup.sh
```

---

### **Script 2: 2_actualizar.sh**

**Qué hace:**
- ✅ Descomprime egarage_update_atlantareciclajes.zip
- ✅ Copia templates de email (7 archivos)
- ✅ Copia templates de auth y landing
- ✅ Copia views_extra (signup, payment, webhook)
- ✅ Copia models (pago.py actualizado)
- ✅ Copia forms y signals
- ✅ Copia management commands
- ✅ Copia URLs (hace backup automático)
- ⚠️ Pide confirmar edición manual de settings.py
- ✅ Ejecuta migraciones
- ✅ Recolecta archivos estáticos

**Tiempo:** 5-7 minutos

**Pre-requisitos:**
- Archivo en: `/home/atlantareciclajes/egarage_update/egarage_update_atlantareciclajes.zip`
- Settings.py editado manualmente (el script te guía)

**Uso:**
```bash
cd /home/atlantareciclajes/scripts_deploy/
./2_actualizar.sh

# El script te pedirá confirmar que editaste settings.py
# Sigue las instrucciones en pantalla
```

**Cambios en settings.py:**
```python
# ANTES:
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "none" if DEBUG else "mandatory")
ACCOUNT_EMAIL_REQUIRED = False

# DESPUÉS:
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
ACCOUNT_EMAIL_REQUIRED = True

# ANTES:
ACCOUNT_CONFIRM_EMAIL_ON_GET = env_bool("ACCOUNT_CONFIRM_EMAIL_ON_GET", False if not DEBUG else True)

# DESPUÉS:
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
```

---

### **Script 3: 3_verificar.sh**

**Qué hace:**
- ✅ Verifica que archivos críticos existen
- ✅ Verifica migraciones aplicadas
- ✅ Cuenta usuarios (compara con backup)
- ✅ Ejecuta `python manage.py check`
- ✅ Verifica archivos estáticos
- ✅ Muestra resumen y checklist manual

**Tiempo:** 1-2 minutos

**Uso:**
```bash
cd /home/atlantareciclajes/scripts_deploy/
./3_verificar.sh
```

**Salida esperada:**
```
✅ Archivos: TODOS COPIADOS CORRECTAMENTE
✅ Migraciones: Aplicadas
✅ Usuarios: 15 (mismo número que antes)
✅ Estáticos: Recolectados
```

---

### **Script 4: 4_rollback.sh**

**Qué hace:**
- ⚠️ Restaura db.sqlite3 del backup
- ⚠️ Restaura media/ del backup
- ⚠️ Restaura settings.py del backup
- ⚠️ Restaura urls.py del backup
- ℹ️ Revierte a estado anterior

**Tiempo:** 1-2 minutos

**Cuándo usar:**
- ❌ La actualización causó errores
- ❌ El sitio no carga
- ❌ Datos incorrectos
- ❌ Decisión de no actualizar

**Uso:**
```bash
cd /home/atlantareciclajes/scripts_deploy/
./4_rollback.sh

# Te pedirá confirmar (escribir SI)
# Te pedirá la fecha del backup a restaurar
```

---

## 🔄 **FLUJO COMPLETO**

### **Antes de Empezar:**
```
□ FileZilla instalado y configurado
□ Scripts subidos a /home/atlantareciclajes/scripts_deploy/
□ Permisos de ejecución dados: chmod +x *.sh
□ Archivos de actualización preparados en tu PC
```

### **Paso a Paso:**

```bash
# === EN PYTHONANYWHERE CONSOLE ===

# 1. BACKUP (OBLIGATORIO)
cd /home/atlantareciclajes/scripts_deploy/
./1_backup.sh
# ⏱️ 2-3 minutos
# ✅ Anota el nombre del backup creado

# === EN TU PC CON FILEZILLA ===

# 2. DESCARGAR BACKUP
# Descargar: backup_completo_20251026_*.tar.gz
# Guardar en: E:\backups_egarage_pythonanywhere\

# 3. SUBIR ACTUALIZACIÓN
# Subir a: /home/atlantareciclajes/egarage_update/
# Archivo: egarage_update_atlantareciclajes.zip

# === EN PYTHONANYWHERE CONSOLE ===

# 4. ACTUALIZAR
./2_actualizar.sh
# ⏱️ 5-7 minutos
# ⚠️ Seguir instrucciones para settings.py

# === EN NAVEGADOR ===

# 5. RELOAD WEB APP
# Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
# Pestaña: Web
# Clic: Reload atlantareciclajes.pythonanywhere.com
# ⏱️ Esperar 10-15 segundos

# === EN PYTHONANYWHERE CONSOLE ===

# 6. VERIFICAR
./3_verificar.sh
# ⏱️ 1-2 minutos
# ✅ Revisar que todo esté OK

# === EN NAVEGADOR ===

# 7. PRUEBAS MANUALES
# Homepage: https://atlantareciclajes.pythonanywhere.com/
# Landing: https://atlantareciclajes.pythonanywhere.com/cl/
# Login: https://atlantareciclajes.pythonanywhere.com/accounts/login/
```

### **Si Todo Está OK:**
```
✅ ¡Actualización completada!
✅ Guardar backups por 30 días
✅ Monitorear logs por 24 horas
```

### **Si Algo Falla:**
```bash
# ROLLBACK INMEDIATO
./4_rollback.sh
# Ingresar fecha del backup
# Reload en Web panel
# Volver a estado anterior
```

---

## ⏰ **TIEMPOS ESTIMADOS**

```
1. Backup:           2-3 minutos
2. Subir archivos:   5-10 minutos (depende internet)
3. Actualizar:       5-7 minutos
4. Reload:           15 segundos
5. Verificar:        1-2 minutos
---
TOTAL:              15-25 minutos
```

---

## 🔒 **VENTAJAS DE LOS SCRIPTS**

### **Vs. Manual:**
- ✅ **Más rápido**: 15 min vs 60 min
- ✅ **Menos errores**: Automatizado
- ✅ **Reproducible**: Mismo resultado siempre
- ✅ **Reversible**: Rollback en 2 minutos
- ✅ **Auditable**: Logs de cada paso

### **Seguridad:**
- ✅ Backup automático antes de tocar nada
- ✅ Verifica archivos antes de copiar
- ✅ Backup de DB antes de migrar
- ✅ Rollback fácil si falla
- ✅ No toca db.sqlite3 ni media/ en actualización

---

## 📝 **LOGS Y DEBUGGING**

### **Durante Ejecución:**
```bash
# Los scripts muestran progreso en pantalla
# Cada paso muestra: ✅ (éxito) o ❌ (error)
```

### **Si Hay Errores:**
```bash
# Ver último comando que falló (en pantalla)
# Ver error log:
tail -50 /var/log/atlantareciclajes.pythonanywhere.com.error.log

# Ver log en Web panel:
https://www.pythonanywhere.com/user/atlantareciclajes/
→ Web → Error log
```

### **Verificar Estado:**
```bash
cd /home/atlantareciclajes/egarage/
python manage.py check
python manage.py showmigrations
```

---

## 🆘 **SOLUCIÓN DE PROBLEMAS**

### **Error: "Permission denied"**
```bash
chmod +x /home/atlantareciclajes/scripts_deploy/*.sh
```

### **Error: "File not found"**
```bash
# Verificar estructura:
ls -la /home/atlantareciclajes/egarage_update/
ls -la /home/atlantareciclajes/scripts_deploy/
```

### **Error en migraciones:**
```bash
# Restaurar DB del backup:
cp /home/atlantareciclajes/backups_*/db.sqlite3 /home/atlantareciclajes/egarage/
```

### **Sitio no carga después de Reload:**
```bash
# 1. Ver error log en Web panel
# 2. Si es crítico: ejecutar rollback
./4_rollback.sh
# 3. Reload en Web panel
```

---

## ✅ **CHECKLIST FINAL**

### **Antes:**
```
□ Scripts subidos y con permisos
□ Backup ejecutado exitosamente
□ Backup descargado a PC
□ Archivos de actualización subidos
```

### **Durante:**
```
□ Script 1: Backup OK
□ Script 2: Actualización OK
□ Settings.py editado manualmente
□ Reload ejecutado
□ Script 3: Verificación OK
```

### **Después:**
```
□ Homepage carga
□ Landing Chile nueva funciona
□ Login funciona
□ Número de usuarios igual
□ No hay errores en logs
```

---

## 🎯 **VENTANA DE MANTENIMIENTO RECOMENDADA**

```
Día: Domingo
Hora: 2:00 AM - 4:00 AM (hora Chile)
Duración: ~30 minutos
Impacto: Mínimo (menos usuarios activos)
```

---

## 📞 **SOPORTE**

**Si algo falla:**
1. Ejecutar `./4_rollback.sh` inmediatamente
2. Guardar logs de error
3. Contactar para ayuda con logs

**Archivos importantes:**
- Error log: En Web panel
- Backup: `/home/atlantareciclajes/backups_*/`
- Scripts: `/home/atlantareciclajes/scripts_deploy/`

---

**¡Actualización automatizada lista!** 🚀

