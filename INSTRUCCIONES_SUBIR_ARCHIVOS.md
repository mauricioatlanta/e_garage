# 📤 Cómo Subir los Iconos PWA al Servidor

Los archivos están listos en tu Windows, ahora necesitas subirlos al servidor Linux.

---

## Método 1: Script PowerShell con SCP (Más Rápido)

### Requisitos:
- OpenSSH Client instalado en Windows

### Pasos:

1. **Edita el script `subir_iconos_servidor.ps1`:**
   - Abre el archivo
   - Reemplaza `TU_SERVIDOR_IP_O_DOMINIO` con tu IP/dominio real

2. **Ejecuta el script:**
   ```powershell
   .\subir_iconos_servidor.ps1
   ```

3. **Ingresa tu contraseña cuando te la pida**

---

## Método 2: FileZilla / WinSCP (Visual)

### Con FileZilla:

1. **Conectar al servidor:**
   - Servidor: `sftp://tu-servidor-ip-o-dominio`
   - Usuario: `atlantareciclajes`
   - Contraseña: tu contraseña
   - Puerto: `22`

2. **Navegar en el servidor a:**
   ```
   /home/atlantareciclajes/apps/egarage/current/
   ```

3. **Subir estos archivos desde tu Windows:**

   **Desde `E:\projecto\e_garage\static\images\`** → **A `/home/.../current/static/images/`:**
   - `egarage_icon_192x192.png` ✅
   - `egarage_icon_512x512.png` ✅
   - `egarage_icon_1024x1024.png` ✅
   - `egarage_default_logo.svg` ✅
   - `egarage_default_logo.png` ✅

   **Desde `E:\projecto\e_garage\static\`** → **A `/home/.../current/static/`:**
   - `manifest.json` ✅
   - `service-worker.js` ✅

   **Desde `E:\projecto\e_garage\templates\`** → **A `/home/.../current/templates/`:**
   - `base.html` ✅
   
   **Desde `E:\projecto\e_garage\templates\taller\common\`** → **A `/home/.../current/templates/taller/common/`:**
   - `base.html` ✅

### Con WinSCP:

Similar a FileZilla:
1. Nueva Sesión → SFTP
2. Llenar datos de conexión
3. Arrastrar y soltar archivos

---

## Método 3: Comando SCP Manual

Si tienes OpenSSH instalado:

```powershell
# Iconos PNG
scp static\images\egarage_icon_192x192.png atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/static/images/
scp static\images\egarage_icon_512x512.png atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/static/images/
scp static\images\egarage_icon_1024x1024.png atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/static/images/

# SVG y PNG default
scp static\images\egarage_default_logo.svg atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/static/images/
scp static\images\egarage_default_logo.png atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/static/images/

# Manifest y Service Worker
scp static\manifest.json atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/static/
scp static\service-worker.js atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/static/

# Templates
scp templates\base.html atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/templates/
scp templates\taller\common\base.html atlantareciclajes@TU_SERVIDOR:/home/atlantareciclajes/apps/egarage/current/templates/taller/common/
```

Reemplaza `TU_SERVIDOR` con tu IP o dominio.

---

## ✅ Después de Subir los Archivos

Conéctate al servidor por SSH y ejecuta:

```bash
cd ~/apps/egarage/current

# Verificar que los archivos están
ls -lh static/images/egarage_icon_*.png

# Recolectar estáticos
python manage.py collectstatic --no-input

# Reiniciar la aplicación
# (desde tu panel de control del hosting o comando específico)
```

---

## 📱 En el Celular

Una vez que los archivos estén en el servidor y hayas reiniciado:

### Chrome Android:

1. Abre: `chrome://serviceworker-internals/`
2. Busca tu dominio
3. Presiona "Unregister" en todos los service workers
4. Cierra Chrome COMPLETAMENTE (desliza en apps recientes)
5. Reabre Chrome
6. Ve a tu sitio
7. Menú (⋮) → "Agregar a pantalla de inicio"

### Safari iOS:

1. Abre Safari
2. Ve a tu sitio
3. Botón Compartir → "Agregar a pantalla de inicio"
4. ¡Verás el nuevo ícono futurista!

---

## 🔍 Verificar que Funcionó

En el servidor, después de `collectstatic`:

```bash
# Verificar que los iconos están en staticfiles
ls -lh staticfiles/images/egarage_icon_*.png

# Deberías ver:
# egarage_icon_192x192.png   (19.5 KB)
# egarage_icon_512x512.png   (66.5 KB)
# egarage_icon_1024x1024.png (158 KB)
```

Desde tu navegador:
```
https://tu-dominio.com/static/images/egarage_icon_192x192.png
https://tu-dominio.com/static/images/egarage_icon_512x512.png
https://tu-dominio.com/static/manifest.json
https://tu-dominio.com/static/service-worker.js
```

Todos deberían cargar correctamente.

---

## ⚠️ Problemas Comunes

### "0 static files copied"
- Los archivos no están en la ubicación correcta en el servidor
- Verifica que subiste a `/home/atlantareciclajes/apps/egarage/current/static/`

### "Permission denied"
- Verifica que tienes permisos de escritura
- Los archivos deben pertenecer a tu usuario `atlantareciclajes`

### "Service worker not updating"
- Aumenta la versión en `service-worker.js` (ya está en 2.0.0)
- Limpia completamente el cache del navegador
- Desregistra el service worker antiguo

---

## 🎉 ¡Listo!

Una vez completados todos los pasos, verás el nuevo ícono futurista de eGarage cuando instales la PWA en tu celular.


