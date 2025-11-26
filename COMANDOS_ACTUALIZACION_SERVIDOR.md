# 🚀 COMANDOS PARA ACTUALIZAR EGARAGE EN EL SERVIDOR

**Fecha de preparación:** 2025-11-23 17:53:53  
**Servidor:** PythonAnywhere (atlantareciclajes)  
**Ruta del proyecto:** `/home/atlantareciclajes/apps/egarage/current`

---

## 📋 PREPARACIÓN EN TU PC

### 1. Ejecutar script de preparación

```bash
# Desde la raíz del proyecto
cd E:\projecto\e_garage
python scripts/preparar_actualizacion_servidor.py
```

Esto creará:
- ✅ Carpeta `deploy_atlantareciclajes/` con todos los archivos
- ✅ Archivo ZIP: `egarage_update_atlantareciclajes.zip`

### 2. Verificar contenido

Revisa que la carpeta `deploy_atlantareciclajes/` contenga:
- ✅ `templates/` (estructura completa actualizada)
- ✅ `taller/` (código Python actualizado)
- ✅ `gestion_taller/` (configuración)
- ✅ `core/`, `ubicacion/`, `manage.py`
- ✅ `INFO_ACTUALIZACION.txt` (resumen de cambios)

---

## 📤 SUBIR ARCHIVOS AL SERVIDOR (FileZilla)

### Conexión FileZilla

```
Host: atlantareciclajes.pythonanywhere.com
Puerto: 22 (SFTP)
Usuario: atlantareciclajes
Password: [tu password]
```

### Pasos:

1. **Crear carpeta de actualización** (si no existe):
   - Navegar a: `/home/atlantareciclajes/`
   - Crear carpeta: `egarage_update`

2. **Subir el archivo ZIP**:
   - Origen: `E:\projecto\e_garage\egarage_update_atlantareciclajes.zip`
   - Destino: `/home/atlantareciclajes/egarage_update/egarage_update_atlantareciclajes.zip`
   - ⏱️ Tiempo estimado: 5-10 minutos (depende del tamaño)

3. **Verificar que el archivo se subió correctamente**

---

## 🖥️ COMANDOS EN EL SERVIDOR (PythonAnywhere Console)

### Paso 1: Conectar a la consola

1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Clic en pestaña **"Consoles"**
3. Abrir o crear una **Bash console**

### Paso 2: Navegar y verificar scripts

```bash
# Ir a directorio de scripts
cd /home/atlantareciclajes/scripts_deploy/

# Verificar que existen los scripts
ls -la *_FIXED.sh

# Si no tienen permisos, darlos:
chmod +x *_FIXED.sh
chmod +x 0_detectar_ruta.sh
```

### Paso 3: HACER BACKUP (OBLIGATORIO)

```bash
# Ejecutar script de backup
./1_backup_FIXED.sh
```

**⏱️ Tiempo:** 2-3 minutos

**📝 IMPORTANTE:** Anota el nombre del backup que se crea:
- Ejemplo: `backup_completo_20250115_143022.tar.gz`

**📥 Descargar backup a tu PC:**
- Con FileZilla, descargar el archivo `.tar.gz` a: `E:\backups_egarage_pythonanywhere\`

### Paso 4: ACTUALIZAR

```bash
# Verificar que el ZIP está en el servidor
ls -lh /home/atlantareciclajes/egarage_update/egarage_update_atlantareciclajes.zip

# IMPORTANTE: Usar el script de estructura completa para cambios estructurales
# Dar permisos primero (si es necesario)
chmod +x 2_actualizar_ESTRUCTURA_COMPLETA.sh

# Ejecutar script de actualización (ESTRUCTURA COMPLETA)
./2_actualizar_ESTRUCTURA_COMPLETA.sh

# O si prefieres el script básico (solo cambios específicos):
# ./2_actualizar_FIXED.sh
```

**📝 NOTA:** El script `2_actualizar_ESTRUCTURA_COMPLETA.sh` copia toda la estructura de templates actualizada, mientras que `2_actualizar_FIXED.sh` solo copia archivos específicos. Para cambios estructurales importantes, usa el script de estructura completa.

**⏱️ Tiempo:** 5-7 minutos

**⚠️ ATENCIÓN:** El script te pedirá editar `settings.py` manualmente. Sigue las instrucciones en pantalla.

**Cambios necesarios en settings.py:**
```python
# 1. Buscar y cambiar:
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")

# 2. Buscar y cambiar:
ACCOUNT_EMAIL_REQUIRED = True

# 3. Buscar y cambiar:
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
```

**Comando para editar:**
```bash
nano /home/atlantareciclajes/apps/egarage/current/gestion_taller/settings.py
```

**Guardar:** `Ctrl+O`, `Enter`  
**Salir:** `Ctrl+X`

### Paso 5: RELOAD DE LA APP (Web Panel)

1. Ir a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Pestaña: **"Web"**
3. Buscar: `atlantareciclajes.pythonanywhere.com`
4. Clic en botón verde: **"Reload atlantareciclajes.pythonanywhere.com"**
5. ⏱️ Esperar 15-20 segundos

### Paso 6: VERIFICAR

```bash
# Ejecutar script de verificación
cd /home/atlantareciclajes/scripts_deploy/
./3_verificar_FIXED.sh
```

**⏱️ Tiempo:** 1-2 minutos

**✅ Verificaciones:**
- Archivos copiados correctamente
- Migraciones aplicadas
- Número de usuarios (debe ser igual al backup)
- Archivos estáticos recolectados
- `python manage.py check` sin errores

### Paso 7: PRUEBAS MANUALES (Navegador)

Abrir en navegador y probar:

1. **Homepage:**
   - https://atlantareciclajes.pythonanywhere.com/

2. **Landing Chile:**
   - https://atlantareciclajes.pythonanywhere.com/cl/

3. **Login:**
   - https://atlantareciclajes.pythonanywhere.com/accounts/login/

4. **Dashboard (si tienes acceso):**
   - https://atlantareciclajes.pythonanywhere.com/taller/dashboard/

**✅ Verificar:**
- ✅ Páginas cargan sin errores
- ✅ Templates nuevos se muestran correctamente
- ✅ Estructura de templates funciona
- ✅ No hay errores 404 o 500
- ✅ Login funciona

---

## 🆘 SI ALGO FALLA - ROLLBACK

### Ejecutar rollback inmediato:

```bash
cd /home/atlantareciclajes/scripts_deploy/
./4_rollback.sh
```

**Te pedirá:**
1. Confirmar (escribir `SI`)
2. Fecha del backup a restaurar (ejemplo: `20250115_143022`)

**Luego:**
- Reload en Web panel
- Verificar que todo volvió a funcionar

---

## 📊 RESUMEN DE COMANDOS (Copy-Paste)

```bash
# === EN PYTHONANYWHERE CONSOLE ===

# 1. Ir a scripts
cd /home/atlantareciclajes/scripts_deploy/

# 2. Dar permisos (si es necesario)
chmod +x *_FIXED.sh

# 3. BACKUP
./1_backup_FIXED.sh
# ⏱️ 2-3 min
# 📝 Anotar nombre del backup

# 4. ACTUALIZAR (ESTRUCTURA COMPLETA)
chmod +x 2_actualizar_ESTRUCTURA_COMPLETA.sh
./2_actualizar_ESTRUCTURA_COMPLETA.sh
# ⏱️ 7-10 min (más tiempo por estructura completa)
# ⚠️ Editar settings.py cuando lo pida

# 5. RELOAD (en Web panel del navegador)
# https://www.pythonanywhere.com/user/atlantareciclajes/ → Web → Reload

# 6. VERIFICAR
./3_verificar_FIXED.sh
# ⏱️ 1-2 min

# 7. PROBAR en navegador
# https://atlantareciclajes.pythonanywhere.com/cl/
```

---

## ⏱️ TIEMPO TOTAL ESTIMADO

```
Preparación en PC:        5 min
Subir con FileZilla:     10 min
Backup:                   3 min
Actualización:            7 min
Reload:                   1 min
Verificación:             2 min
Pruebas manuales:         5 min
---
TOTAL:                   33 minutos
```

---

## ✅ CHECKLIST FINAL

### Antes de empezar:
- [ ] Script de preparación ejecutado en PC
- [ ] ZIP creado y verificado
- [ ] FileZilla configurado y conectado
- [ ] Scripts de despliegue en servidor con permisos

### Durante actualización:
- [ ] Backup ejecutado exitosamente
- [ ] Backup descargado a PC
- [ ] ZIP subido al servidor
- [ ] Script de actualización ejecutado
- [ ] Settings.py editado correctamente
- [ ] Reload ejecutado en Web panel
- [ ] Verificación completada sin errores

### Después de actualización:
- [ ] Homepage carga correctamente
- [ ] Landing Chile funciona
- [ ] Login funciona
- [ ] Templates nuevos se muestran
- [ ] No hay errores en logs
- [ ] Número de usuarios correcto

---

## 📞 SOPORTE

**Si hay errores:**
1. Ejecutar `./4_rollback.sh` inmediatamente
2. Guardar logs de error
3. Revisar: `/var/log/atlantareciclajes.pythonanywhere.com.error.log`
4. Contactar con logs para ayuda

**Archivos importantes:**
- Error log: En Web panel → Web → Error log
- Backup: `/home/atlantareciclajes/backups_*/`
- Scripts: `/home/atlantareciclajes/scripts_deploy/`

---

**¡Actualización lista!** 🚀

