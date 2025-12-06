# 📥 GUÍA: Sincronizar 100% del Servidor a tu PC

## 🎯 Objetivo
Actualizar tu copia local de eGarage con **todos** los archivos del servidor PythonAnywhere.

---

## ⚡ MÉTODO RÁPIDO (Recomendado)

### Opción 1: Usar el Script Automático

```powershell
# En PowerShell, desde la raíz del proyecto:
cd E:\projecto\e_garage
.\scripts\sync_from_server_completo.ps1
```

El script te guiará paso a paso:
1. ✅ Verifica configuración
2. ✅ Hace backup de cambios locales
3. ✅ Te muestra opciones de sincronización
4. ✅ Genera scripts si es necesario

---

## 📋 MÉTODO MANUAL (FileZilla)

### Paso 1: Conectar con FileZilla

1. Abre **FileZilla** (o descárgalo de https://filezilla-project.org/)
2. **Archivo** → **Gestor de sitios** → **Nuevo sitio**
3. Configura:
   ```
   Protocolo: SFTP - SSH File Transfer Protocol
   Host: atlantareciclajes.pythonanywhere.com
   Puerto: 22
   Tipo de acceso: Normal
   Usuario: atlantareciclajes
   Contraseña: [tu contraseña de PythonAnywhere]
   ```
4. Clic en **Conectar**

### Paso 2: Navegar a las Carpetas

**Panel REMOTO (izquierda):**
- Navegar a: `/home/atlantareciclajes/apps/egarage/current`
- O si no existe: `/home/atlantareciclajes/egarage/`

**Panel LOCAL (derecha):**
- Navegar a: `E:\projecto\e_garage`

### Paso 3: Descargar Archivos

1. En el panel REMOTO, selecciona **TODAS** las carpetas y archivos:
   - `core/`
   - `gestion_taller/`
   - `taller/`
   - `templates/`
   - `static/`
   - `ubicacion/`
   - `manage.py`
   - `requirements.txt`
   - Y todos los demás archivos/carpetas

2. **Arrastra** al panel LOCAL (o clic derecho → **Descargar**)

3. Cuando pregunte por sobrescribir, elige **"Sobrescribir"** o **"Sí a todo"**

### Paso 4: ⚠️ NO Descargar Estas Carpetas

**NO descargues del servidor:**
- ❌ `media/` - Archivos subidos por usuarios (muy pesado)
- ❌ `staticfiles/` - Se regenera con `collectstatic`
- ❌ `__pycache__/` - Cache de Python (se regenera)
- ❌ `db.sqlite3` - Base de datos del servidor (usa la tuya local)
- ❌ `.env` - Variables de entorno del servidor

---

## 🔧 MÉTODO AVANZADO (WSL/Git Bash con rsync)

Si tienes **WSL** o **Git Bash** instalado:

```bash
# Desde WSL o Git Bash:
cd /e/projecto/e_garage

# Sincronizar (excluyendo archivos innecesarios)
rsync -avz --progress \
  --exclude='db.sqlite3' \
  --exclude='media/' \
  --exclude='staticfiles/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='*.log' \
  --exclude='venv/' \
  --exclude='node_modules/' \
  atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/ \
  ./
```

---

## ✅ VERIFICACIÓN DESPUÉS DE SINCRONIZAR

### 1. Verificar Cambios en Git

```powershell
cd E:\projecto\e_garage
git status
```

Deberías ver los archivos que cambiaron.

### 2. Revisar Cambios Importantes

```powershell
# Ver resumen de cambios
git diff --stat

# Ver cambios en un archivo específico
git diff gestion_taller/settings.py
```

### 3. Hacer Commit de los Cambios

```powershell
# Agregar todos los cambios
git add -A

# Commit
git commit -m "sync: Actualización completa desde servidor - $(Get-Date -Format 'yyyy-MM-dd')"
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "Permission denied" en FileZilla
- Verifica que tienes la contraseña correcta
- Asegúrate de usar **SFTP** (puerto 22), no FTP

### Error: "No se puede conectar al servidor"
- Verifica que el host es: `atlantareciclajes.pythonanywhere.com`
- Verifica que el puerto es: `22`
- Verifica tu conexión a internet

### Archivos no se actualizan
- Asegúrate de elegir **"Sobrescribir"** cuando FileZilla pregunte
- Cierra cualquier editor que tenga los archivos abiertos
- Verifica que tienes permisos de escritura en la carpeta local

### Quiero restaurar mis cambios locales
Si hiciste backup con el script, los cambios están en:
```
E:\projecto\e_garage\.sync_backup_YYYYMMDD_HHMMSS\
```

O si usaste Git stash:
```powershell
git stash list
git stash pop stash@{0}
```

---

## 📊 INFORMACIÓN DEL SERVIDOR

```
Usuario: atlantareciclajes
Host: atlantareciclajes.pythonanywhere.com
Puerto: 22 (SFTP)
Ruta proyecto: /home/atlantareciclajes/apps/egarage/current
           o: /home/atlantareciclajes/egarage/
```

---

## ⏱️ TIEMPO ESTIMADO

- **FileZilla (manual)**: 10-30 minutos (depende de velocidad de internet)
- **rsync (WSL)**: 5-15 minutos
- **Script automático**: 2-5 minutos (más tiempo de descarga)

---

## ✅ CHECKLIST FINAL

Después de sincronizar, verifica:

- [ ] Archivos descargados correctamente
- [ ] `manage.py` existe y es reciente
- [ ] `gestion_taller/settings.py` actualizado
- [ ] `templates/` tiene los archivos del servidor
- [ ] `taller/` tiene los módulos actualizados
- [ ] Git muestra los cambios: `git status`
- [ ] Cambios commiteados (si es necesario)
- [ ] Proyecto funciona localmente: `python manage.py runserver`

---

## 🎯 SIGUIENTE PASO

Una vez sincronizado, puedes:
1. Revisar los cambios: `git diff`
2. Probar localmente: `python manage.py runserver`
3. Hacer commit: `git commit -m "sync: desde servidor"`
4. Continuar trabajando con la versión actualizada

---

**¿Necesitas ayuda?** Revisa los logs o ejecuta el script con `-Verbose`:
```powershell
.\scripts\sync_from_server_completo.ps1 -Verbose
```







