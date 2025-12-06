# 🚀 GUÍA RÁPIDA DE ACTUALIZACIÓN - EGARAGE

## ✅ PASO 1: PREPARAR ACTUALIZACIÓN (YA COMPLETADO)

El script `preparar_actualizacion.ps1` ya se ejecutó y creó:
- **Archivo ZIP**: `egarage_update\egarage_update_atlantareciclajes.zip` (3.09 MB)
- **Archivos copiados**: 14 componentes

---

## 📤 PASO 2: SUBIR ARCHIVO AL SERVIDOR

### 2.1. Abrir FileZilla

1. Abre **FileZilla** (o cualquier cliente SFTP)
2. Configura la conexión:
   - **Host**: `atlantareciclajes.pythonanywhere.com`
   - **Puerto**: `22` (SFTP)
   - **Protocolo**: SFTP - SSH File Transfer Protocol
   - **Usuario**: `atlantareciclajes`
   - **Contraseña**: [tu contraseña de PythonAnywhere]

### 2.2. Subir el archivo ZIP

1. **En tu PC**: Navega a `E:\projecto\e_garage\egarage_update\`
2. **En el servidor**: Navega a `/home/atlantareciclajes/egarage_update/`
   - Si la carpeta no existe, créala
3. **Arrastra** el archivo `egarage_update_atlantareciclajes.zip` desde tu PC al servidor
4. Espera a que termine la subida (puede tardar 5-10 minutos dependiendo de tu conexión)

---

## 🔧 PASO 3: EJECUTAR SCRIPTS EN EL SERVIDOR

### 3.1. Abrir Console en PythonAnywhere

1. Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Inicia sesión con tus credenciales
3. Ve a la pestaña **"Consoles"**
4. Haz clic en **"Bash"** (o abre una consola bash existente)

### 3.2. Ejecutar Scripts de Actualización

En la consola bash, ejecuta estos comandos en orden:

```bash
# 1. Ir al directorio de scripts
cd /home/atlantareciclajes/scripts_deploy/

# 2. Dar permisos de ejecución (si es necesario)
chmod +x *.sh

# 3. HACER BACKUP (OBLIGATORIO)
./1_backup_FIXED.sh

# Anota el nombre del backup que se crea
# Ejemplo: backup_completo_20251106_013500.tar.gz
```

**IMPORTANTE**: Descarga el backup a tu PC con FileZilla antes de continuar.

```bash
# 4. ACTUALIZAR ARCHIVOS
./2_actualizar_ESTRUCTURA_COMPLETA.sh

# El script te pedirá:
# - Confirmar que editaste settings.py (sigue las instrucciones)
# - Ejecutará migraciones
# - Recolectará archivos estáticos
```

---

## ⚙️ PASO 4: EDITAR SETTINGS.PY (SI ES NECESARIO)

El script `2_actualizar_ESTRUCTURA_COMPLETA.sh` te indicará si necesitas editar `settings.py`.

Si es necesario, ejecuta:

```bash
nano /home/atlantareciclajes/apps/egarage/current/gestion_taller/settings.py
```

Busca y cambia estas líneas (si existen):

```python
# ANTES:
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "none" if DEBUG else "mandatory")
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_CONFIRM_EMAIL_ON_GET = env_bool("ACCOUNT_CONFIRM_EMAIL_ON_GET", False if not DEBUG else True)

# DESPUÉS:
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
```

**Guardar**: `Ctrl+O`, `Enter`  
**Salir**: `Ctrl+X`

---

## 🔄 PASO 5: RELOAD DE LA APLICACIÓN

1. Ve a: https://www.pythonanywhere.com/user/atlantareciclajes/
2. Ve a la pestaña **"Web"**
3. Busca tu aplicación: `atlantareciclajes.pythonanywhere.com`
4. Haz clic en el botón verde: **"Reload atlantareciclajes.pythonanywhere.com"**
5. Espera 15-20 segundos hasta que aparezca "reloaded successfully"

---

## ✅ PASO 6: VERIFICAR ACTUALIZACIÓN

### 6.1. En la Consola

```bash
cd /home/atlantareciclajes/scripts_deploy/
./3_verificar_FIXED.sh
```

Este script verificará:
- ✅ Archivos copiados correctamente
- ✅ Migraciones aplicadas
- ✅ Número de usuarios (debe ser igual al backup)
- ✅ Archivos estáticos recolectados

### 6.2. En el Navegador

Prueba estas URLs:

- **Homepage**: https://atlantareciclajes.pythonanywhere.com/
- **Landing Chile**: https://atlantareciclajes.pythonanywhere.com/cl/
- **Login**: https://atlantareciclajes.pythonanywhere.com/accounts/login/

---

## 🆘 SI ALGO FALLA: ROLLBACK

Si algo sale mal, puedes restaurar el backup:

```bash
cd /home/atlantareciclajes/scripts_deploy/
./4_rollback.sh

# Te pedirá la fecha del backup
# Ingresa: 20251106_013500 (o la fecha que tengas)
```

Luego haz **Reload** en el Web panel.

---

## 📊 RESUMEN DE TIEMPOS

```
1. Preparar actualización:      ✅ COMPLETADO
2. Subir con FileZilla:          5-10 minutos
3. Backup en servidor:           2-3 minutos
4. Actualizar archivos:          5-7 minutos
5. Reload:                       15 segundos
6. Verificar:                    1-2 minutos
---
TOTAL:                          15-25 minutos
```

---

## 📝 CHECKLIST FINAL

Antes de terminar, verifica:

- [ ] Backup descargado a tu PC
- [ ] Archivo ZIP subido al servidor
- [ ] Script de backup ejecutado
- [ ] Script de actualización ejecutado
- [ ] Settings.py editado (si fue necesario)
- [ ] Reload ejecutado en Web panel
- [ ] Verificación ejecutada sin errores
- [ ] URLs probadas en navegador
- [ ] Número de usuarios correcto

---

## 🎉 ¡ACTUALIZACIÓN COMPLETADA!

Si todos los pasos se completaron correctamente, tu servidor está actualizado con la última versión de eGarage.

**Archivos actualizados:**
- Templates completos
- Código Python (taller)
- Configuración Django
- Otras apps (core, ubicacion)

---

**¿Necesitas ayuda?** Revisa los logs de error en el Web panel de PythonAnywhere.






