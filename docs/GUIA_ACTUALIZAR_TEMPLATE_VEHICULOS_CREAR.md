# 📤 GUÍA: Actualizar Template crear.html en el Servidor

## 🎯 Objetivo
Actualizar el archivo `templates/cl/es/vehiculos/crear.html` en el servidor para que la página https://www.egarage.cl/cl/es/vehiculos/crear/ muestre la versión más reciente.

---

## 📋 INFORMACIÓN DEL SERVIDOR

```
Usuario: atlantareciclajes
Host: atlantareciclajes.pythonanywhere.com
Puerto: 22 (SFTP/SSH)
Ruta en servidor: /home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/crear.html
Archivo local: E:\projecto\e_garage\templates\cl\es\vehiculos\crear.html
```

---

## ⚡ MÉTODO 1: FileZilla (Recomendado - Más Fácil)

### Paso 1: Abrir FileZilla
1. Abre FileZilla (si no lo tienes, descárgalo de https://filezilla-project.org/)
2. Ve a **Archivo → Gestor de sitios** (o presiona `Ctrl+S`)

### Paso 2: Configurar Conexión
1. Click en **Nuevo sitio**
2. Configura:
   - **Host:** `atlantareciclajes.pythonanywhere.com`
   - **Protocolo:** `SFTP - SSH File Transfer Protocol`
   - **Tipo de acceso:** `Normal`
   - **Usuario:** `atlantareciclajes`
   - **Contraseña:** [tu contraseña de PythonAnywhere]
   - **Puerto:** `22`
3. Click en **Conectar**

### Paso 3: Navegar a la Carpeta
**Panel REMOTO (derecha):**
- Navega a: `/home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/`

**Panel LOCAL (izquierda):**
- Navega a: `E:\projecto\e_garage\templates\cl\es\vehiculos\`

### Paso 4: Subir el Archivo
1. En el panel **LOCAL**, selecciona el archivo `crear.html`
2. **Arrastra y suelta** el archivo al panel **REMOTO**
   - O click derecho → **Subir**
3. Cuando pregunte si quieres sobrescribir, selecciona **Sí**

### Paso 5: Verificar Permisos
1. Click derecho en `crear.html` en el panel remoto
2. Selecciona **Permisos de archivo**
3. Asegúrate que tenga permisos `644` (rw-r--r--)
4. Si no, cambia a `644` y confirma

### Paso 6: Verificar en el Navegador
1. Abre: https://www.egarage.cl/cl/es/vehiculos/crear/
2. Verifica que los cambios se reflejen correctamente
3. Si no ves cambios, presiona `Ctrl+F5` para forzar recarga

---

## ⚡ MÉTODO 2: SCP desde PowerShell

### Paso 1: Abrir PowerShell
1. Abre PowerShell
2. Navega al directorio del proyecto:
```powershell
cd E:\projecto\e_garage
```

### Paso 2: Subir el Archivo
```powershell
# Reemplaza TU_CONTRASEÑA con tu contraseña real
$env:SSH_PASSWORD = "TU_CONTRASEÑA"

# Subir el archivo
scp templates/cl/es/vehiculos/crear.html atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/crear.html
```

**Nota:** Si te pide contraseña, escríbela cuando se solicite.

### Paso 3: Verificar Permisos (SSH)
Si tienes acceso SSH, puedes verificar/ajustar permisos:
```bash
ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
cd /home/atlantareciclajes/apps/egarage/current
chmod 644 templates/cl/es/vehiculos/crear.html
ls -la templates/cl/es/vehiculos/crear.html
```

---

## ⚡ MÉTODO 3: rsync desde WSL/Git Bash

### Paso 1: Abrir WSL o Git Bash
1. Abre WSL (Windows Subsystem for Linux) o Git Bash
2. Navega al directorio del proyecto:
```bash
cd /e/projecto/e_garage
# O si usas Git Bash:
cd /e/projecto/e_garage
```

### Paso 2: Subir el Archivo
```bash
rsync -avz --progress \
  templates/cl/es/vehiculos/crear.html \
  atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/crear.html
```

### Paso 3: Verificar Permisos
```bash
ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
chmod 644 /home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/crear.html
```

---

## ✅ VERIFICACIÓN POST-ACTUALIZACIÓN

### 1. Verificar que el archivo se subió correctamente
```bash
# Desde SSH o FileZilla, verifica:
ls -la /home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/crear.html
```

Deberías ver algo como:
```
-rw-r--r-- 1 atlantareciclajes atlantareciclajes [tamaño] [fecha] crear.html
```

### 2. Verificar en el navegador
1. Abre: https://www.egarage.cl/cl/es/vehiculos/crear/
2. Presiona `Ctrl+F5` para forzar recarga (sin caché)
3. Verifica que los cambios se reflejen

### 3. Verificar tamaño del archivo
Compara el tamaño del archivo local vs remoto:
- **Local:** `E:\projecto\e_garage\templates\cl\es\vehiculos\crear.html`
- **Remoto:** `/home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/crear.html`

Deben tener el mismo tamaño (aproximadamente).

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Problema: "Permiso denegado" al subir
**Solución:**
```bash
# Verificar permisos de la carpeta destino
ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
ls -la /home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/

# Si no tienes permisos de escritura, contacta al administrador
```

### Problema: Los cambios no se ven en el navegador
**Soluciones:**
1. **Limpiar caché del navegador:**
   - Presiona `Ctrl+Shift+Delete`
   - Selecciona "Imágenes y archivos en caché"
   - Click en "Borrar datos"

2. **Forzar recarga:**
   - Presiona `Ctrl+F5` o `Ctrl+Shift+R`

3. **Verificar que el archivo se subió:**
   - Compara la fecha de modificación del archivo local vs remoto
   - Verifica el tamaño del archivo

4. **Verificar que Django está usando el template correcto:**
   ```bash
   # En el servidor, verifica la configuración de templates
   ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
   cd /home/atlantareciclajes/apps/egarage/current
   grep -r "TEMPLATES" gestion_taller/settings.py
   ```

### Problema: "Archivo no encontrado" en el servidor
**Solución:**
1. Verifica que la ruta existe:
   ```bash
   ssh atlantareciclajes@atlantareciclajes.pythonanywhere.com
   ls -la /home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/
   ```

2. Si la carpeta no existe, créala:
   ```bash
   mkdir -p /home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/
   ```

### Problema: Error de conexión SFTP/SSH
**Soluciones:**
1. Verifica que tienes conexión a internet
2. Verifica las credenciales (usuario y contraseña)
3. Verifica que el puerto 22 no esté bloqueado por firewall
4. Intenta desde otra red (por si hay restricciones)

---

## 📝 RESUMEN RÁPIDO

**Para actualizar rápidamente:**

1. **FileZilla (Más fácil):**
   - Conectar a `atlantareciclajes.pythonanywhere.com`
   - Arrastrar `crear.html` de local a remoto
   - Verificar permisos (644)

2. **SCP (PowerShell):**
   ```powershell
   scp templates/cl/es/vehiculos/crear.html atlantareciclajes@atlantareciclajes.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/templates/cl/es/vehiculos/crear.html
   ```

3. **Verificar:**
   - Abrir: https://www.egarage.cl/cl/es/vehiculos/crear/
   - Presionar `Ctrl+F5` para recargar

---

## 💡 CONSEJOS

1. **Siempre haz backup antes de actualizar:**
   ```bash
   # En el servidor, antes de subir:
   cp templates/cl/es/vehiculos/crear.html templates/cl/es/vehiculos/crear.html.backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Verifica el archivo local antes de subir:**
   - Asegúrate de que el archivo local tiene los cambios que quieres

3. **Usa FileZilla para la primera vez:**
   - Es más visual y te permite ver la estructura del servidor

4. **Mantén un registro:**
   - Anota la fecha y hora de cada actualización
   - Guarda backups de versiones importantes

---

## ✅ CHECKLIST

Antes de actualizar:
- [ ] Archivo local tiene los cambios correctos
- [ ] Tengo las credenciales del servidor
- [ ] Tengo conexión a internet estable

Después de actualizar:
- [ ] Archivo se subió correctamente (verificar tamaño/fecha)
- [ ] Permisos son correctos (644)
- [ ] Cambios se ven en el navegador (Ctrl+F5)
- [ ] No hay errores en la consola del navegador (F12)

---

**¡Actualización completada!** 🎉











