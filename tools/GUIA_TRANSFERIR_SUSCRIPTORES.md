# Guía: Transferir Suscriptores de PythonAnywhere a DigitalOcean

Esta guía te muestra cómo transferir el archivo `suscripciones_consolidadas.json` desde PythonAnywhere a DigitalOcean.

## Opción 1: Usando la interfaz web de PythonAnywhere (MÁS FÁCIL)

### Paso 1: Descargar desde PythonAnywhere

1. **Accede a PythonAnywhere** → https://www.pythonanywhere.com
2. **Ve a la pestaña "Files"**
3. **Navega a:** `/home/atlantareciclajes/apps/egarage/current/`
4. **Busca el archivo:** `suscripciones_consolidadas.json`
5. **Haz clic derecho** → **"Download"** o simplemente **haz clic** en el archivo para descargarlo
6. El archivo se descargará a tu PC

### Paso 2: Subir a DigitalOcean

**Opción A: Usando FileZilla (recomendado)**

1. **Abre FileZilla**
2. **Conecta a DigitalOcean:**
   - Host: `159.223.200.106` (o la IP de tu servidor)
   - Usuario: `root` (o tu usuario SSH)
   - Contraseña: (tu contraseña SSH)
   - Puerto: `22`
   - Protocolo: `SFTP`

3. **Navega en el servidor remoto a:** `/srv/egarage/app/`
4. **Arrastra el archivo** `suscripciones_consolidadas.json` desde tu PC a esa carpeta

**Opción B: Usando SCP desde terminal (Windows PowerShell o Linux/Mac)**

```bash
# Desde tu PC (reemplaza con tu ruta local)
scp suscripciones_consolidadas.json root@159.223.200.106:/srv/egarage/app/
```

**Opción C: Usando WinSCP (Windows)**

1. Descarga WinSCP: https://winscp.net/
2. Conecta con los mismos datos que FileZilla
3. Arrastra el archivo

### Paso 3: Verificar que el archivo llegó correctamente

**Conecta por SSH a DigitalOcean:**
```bash
ssh root@159.223.200.106
```

**Verifica el archivo:**
```bash
cd /srv/egarage/app
ls -lh suscripciones_consolidadas.json
# Deberías ver el tamaño del archivo (ej: 15K, 50K, etc.)

# Ver primeras líneas para confirmar
head -n 20 suscripciones_consolidadas.json
```

### Paso 4: Importar los suscriptores

```bash
cd /srv/egarage/app
source .venv/bin/activate  # Activar entorno virtual si existe
python tools/importar_suscripciones.py suscripciones_consolidadas.json
```

---

## Opción 2: Transferencia directa servidor a servidor (SSH)

Si tienes acceso SSH a ambos servidores, puedes transferir directamente:

### Desde PythonAnywhere (consola Bash)

```bash
cd /home/atlantareciclajes/apps/egarage/current

# Verificar que el archivo existe
ls -lh suscripciones_consolidadas.json

# Transferir directamente a DigitalOcean
scp suscripciones_consolidadas.json root@159.223.200.106:/srv/egarage/app/
```

**Nota:** Esto requiere que PythonAnywhere tenga acceso SSH a DigitalOcean. Si no funciona, usa la Opción 1.

---

## Opción 3: Usando un servicio intermedio (Google Drive, Dropbox, etc.)

1. **Sube el archivo desde PythonAnywhere** a Google Drive/Dropbox
2. **Descárgalo en tu PC**
3. **Súbelo a DigitalOcean** usando FileZilla o SCP

---

## Verificación final

Después de importar, verifica que todo funcionó:

```bash
cd /srv/egarage/app
python tools/verificar_suscripciones_migradas.py
```

Este script te mostrará:
- Total de usuarios y suscripciones
- Usuarios con/sin suscripción
- Suscripciones activas/expiradas
- Distribución por país

---

## Solución de problemas

### Error: "Permission denied"
```bash
# Asegúrate de tener permisos en el directorio
chmod 644 /srv/egarage/app/suscripciones_consolidadas.json
```

### Error: "No such file or directory"
```bash
# Verifica que el archivo existe
ls -la /srv/egarage/app/suscripciones_consolidadas.json

# Verifica que estás en el directorio correcto
pwd
```

### Error: "ModuleNotFoundError" al importar
```bash
# Asegúrate de estar en el directorio correcto y con el entorno activado
cd /srv/egarage/app
source .venv/bin/activate
python tools/importar_suscripciones.py suscripciones_consolidadas.json
```

### El archivo está vacío o corrupto
```bash
# Verifica el contenido
cat suscripciones_consolidadas.json | head -n 50

# Verifica que es JSON válido
python -c "import json; json.load(open('suscripciones_consolidadas.json'))"
```

---

## Resumen rápido

1. ✅ **Descargar** `suscripciones_consolidadas.json` desde PythonAnywhere (interfaz web)
2. ✅ **Subir** a DigitalOcean usando FileZilla/SCP/WinSCP
3. ✅ **Verificar** que el archivo llegó correctamente
4. ✅ **Importar** con `python tools/importar_suscripciones.py suscripciones_consolidadas.json`
5. ✅ **Verificar** con `python tools/verificar_suscripciones_migradas.py`
