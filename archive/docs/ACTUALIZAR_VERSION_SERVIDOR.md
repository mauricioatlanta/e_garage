# 🚀 Actualizar Versión eGarage 2.1.1 al Servidor

**Fecha:** 2025-11-25  
**Versión:** 2.1.1  
**Servidor:** PythonAnywhere (atlantareciclajes)

---

## 📋 RESUMEN DE CAMBIOS

### Versión Actualizada
- **Versión anterior:** 2.1.0 (2025-11-08)
- **Versión nueva:** 2.1.1 (2025-11-25)

### Cambios Principales
- ✅ Actualización de versión a 2.1.1
- 🧹 Limpieza de archivos temporales y documentación obsoleta
- 🔧 Mejoras en formularios y vistas
- 📦 Preparación para despliegue

---

## 🔄 OPCIÓN 1: ACTUALIZACIÓN AUTOMÁTICA (Recomendada)

### Paso 1: Commit y Push desde tu PC

```powershell
# Agregar todos los cambios (incluyendo archivos eliminados)
git add -A

# Hacer commit
git commit -m "chore: actualizar versión a 2.1.1 y limpieza de archivos"

# Push a GitHub
git push origin main
```

### Paso 2: En el Servidor (PythonAnywhere Console)

1. **Conectarte a la consola:**
   - Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/
   - Pestaña: **"Consoles"**
   - Abre una **Bash console**

2. **Ejecutar comandos de actualización:**

```bash
# Ir al directorio del proyecto
cd /home/atlantareciclajes/apps/egarage/current

# Activar entorno virtual
workon venv_egarage310

# Obtener últimos cambios
git pull origin main

# Limpiar caché de Python
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Aplicar migraciones (si hay nuevas)
python manage.py migrate

# Verificar versión
python manage.py version
```

3. **Recargar la aplicación:**
   - Ve al dashboard: https://www.pythonanywhere.com/user/atlantareciclajes/
   - Pestaña: **"Web"**
   - Clic en: **"Reload atlantareciclajes.pythonanywhere.com"**

---

## 🔄 OPCIÓN 2: ACTUALIZACIÓN CON SCRIPT DE PREPARACIÓN

Si prefieres usar el script de preparación completo:

### Paso 1: Preparar paquete de actualización

```powershell
# Desde la raíz del proyecto
python scripts/preparar_actualizacion_servidor.py
```

Esto creará:
- ✅ Carpeta `deploy_atlantareciclajes/` con todos los archivos
- ✅ Archivo ZIP: `egarage_update_atlantareciclajes.zip`

### Paso 2: Subir archivo al servidor (FileZilla)

1. **Conectar con FileZilla:**
   ```
   Host: atlantareciclajes.pythonanywhere.com
   Puerto: 22 (SFTP)
   Usuario: atlantareciclajes
   ```

2. **Subir el ZIP:**
   - Origen: `E:\projecto\e_garage\egarage_update_atlantareciclajes.zip`
   - Destino: `/home/atlantareciclajes/egarage_update/`

### Paso 3: Ejecutar scripts en el servidor

```bash
# Ir a scripts de despliegue
cd /home/atlantareciclajes/scripts_deploy/

# Hacer backup primero
./1_backup_FIXED.sh

# Actualizar (estructura completa)
./2_actualizar_ESTRUCTURA_COMPLETA.sh

# Verificar
./3_verificar_FIXED.sh
```

### Paso 4: Reload en Web Panel

- Dashboard → Web → Reload

---

## ✅ VERIFICACIÓN POST-ACTUALIZACIÓN

### 1. Verificar versión en el servidor

```bash
cd /home/atlantareciclajes/apps/egarage/current
python manage.py version
```

**Debe mostrar:** `2.1.1`

### 2. Verificar que el sitio funciona

- ✅ Homepage: https://atlantareciclajes.pythonanywhere.com/
- ✅ Login: https://atlantareciclajes.pythonanywhere.com/accounts/login/
- ✅ Dashboard: https://atlantareciclajes.pythonanywhere.com/taller/dashboard/

### 3. Verificar logs

En el dashboard de PythonAnywhere:
- Web → Error log
- Verificar que no hay errores nuevos

---

## 🆘 SI ALGO FALLA - ROLLBACK

```bash
cd /home/atlantareciclajes/scripts_deploy/
./4_rollback.sh
```

Seguir las instrucciones en pantalla para restaurar el backup.

---

## 📝 NOTAS IMPORTANTES

- ⚠️ **Siempre hacer backup antes de actualizar**
- ⚠️ **Verificar que no hay procesos de Git corriendo** (eliminar `.git/index.lock` si existe)
- ✅ **Los cambios en templates se reflejan inmediatamente** (no necesitan migración)
- ✅ **Los archivos estáticos requieren `collectstatic`**
- ✅ **Las migraciones solo se ejecutan si hay cambios en modelos**

---

## ⏱️ TIEMPO ESTIMADO

- **Opción 1 (Git Pull):** 5-10 minutos
- **Opción 2 (Script completo):** 15-20 minutos

---

**¡Listo para actualizar!** 🚀

