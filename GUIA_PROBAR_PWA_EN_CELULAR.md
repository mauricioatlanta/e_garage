# 📱 Guía: Probar PWA en Celular (Antes de Subir al Servidor)

## 🚀 Método Rápido (Recomendado)

### Opción 1: Usar el Script Automático (Windows)

1. **Ejecuta el script:**
   ```bash
   # Si tienes PowerShell
   .\start_mobile.ps1
   
   # O si prefieres CMD
   start_mobile.bat
   ```

2. **El script te mostrará:**
   - Tu IP local (ejemplo: `192.168.1.100`)
   - La URL para acceder desde tu celular: `http://192.168.1.100:8000`

3. **En tu celular:**
   - Conéctate a la misma red WiFi que tu computadora
   - Abre el navegador (Chrome, Safari, etc.)
   - Ingresa la URL que te mostró el script: `http://TU_IP:8000`

### Opción 2: Manual

1. **Obtén tu IP local:**
   ```bash
   # En Windows (CMD o PowerShell)
   ipconfig
   
   # Busca "Dirección IPv4" o "IPv4 Address"
   # Ejemplo: 192.168.1.100
   ```

2. **Inicia el servidor Django:**
   ```bash
   # IMPORTANTE: Usa 0.0.0.0:8000 (no 127.0.0.1:8000)
   python manage.py runserver 0.0.0.0:8000
   ```

3. **En tu celular:**
   - Conéctate a la misma red WiFi
   - Abre el navegador
   - Ingresa: `http://TU_IP:8000`
   - Ejemplo: `http://192.168.1.100:8000`

## ⚠️ Requisitos Importantes

### 1. Misma Red WiFi
- Tu computadora y celular deben estar en la misma red WiFi
- No funcionará si el celular está usando datos móviles

### 2. Firewall
- Windows puede pedirte permiso para permitir el puerto 8000
- Si el script no configura el firewall automáticamente, hazlo manualmente:
  - Windows Defender Firewall → Configuración avanzada
  - Nueva regla de entrada → Puerto TCP 8000 → Permitir

### 3. HTTPS en Producción
- ⚠️ **IMPORTANTE**: En desarrollo local (HTTP) algunas funciones PWA pueden no funcionar completamente
- El prompt de instalación puede no aparecer en HTTP (requiere HTTPS)
- Para probar completamente la PWA, necesitarás HTTPS (usar ngrok o similar)

## 🔍 Verificar que Funciona

1. **En tu computadora:**
   - Deberías ver en la consola: `Starting development server at http://0.0.0.0:8000/`

2. **En tu celular:**
   - Abre el navegador
   - Ingresa la URL con tu IP
   - Deberías ver eGarage cargando

3. **Probar PWA:**
   - En Android/Chrome: El banner de instalación debería aparecer después de 5 segundos
   - En iOS/Safari: El banner con instrucciones debería aparecer después de 7 segundos
   - ⚠️ Nota: En HTTP, el `beforeinstallprompt` puede no funcionar. Necesitas HTTPS para probarlo completamente.

## 🛠️ Solución de Problemas

### No puedo acceder desde el celular

1. **Verifica la IP:**
   ```bash
   ipconfig
   ```
   - Asegúrate de usar la IP correcta (no 127.0.0.1)

2. **Verifica el firewall:**
   - Windows puede estar bloqueando el puerto 8000
   - Ejecuta PowerShell como Administrador y ejecuta:
   ```powershell
   New-NetFirewallRule -DisplayName "Django Development Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```

3. **Verifica que el servidor esté corriendo:**
   - Debe decir: `Starting development server at http://0.0.0.0:8000/`
   - Si dice `127.0.0.1:8000`, detén el servidor y reinícialo con `0.0.0.0:8000`

4. **Verifica la red:**
   - Ambos dispositivos deben estar en la misma WiFi
   - Prueba hacer ping desde el celular (si tienes una app de ping)

### El prompt de instalación no aparece

- **En HTTP (localhost):** El `beforeinstallprompt` puede no funcionar porque requiere HTTPS
- **Solución temporal:** Usa ngrok para crear un túnel HTTPS:
  ```bash
  # Instala ngrok: https://ngrok.com/
  ngrok http 8000
  # Usa la URL HTTPS que te da ngrok en tu celular
  ```

### Error de CORS o recursos no cargan

- Verifica que `ALLOWED_HOSTS` en `settings.py` incluya tu IP:
  ```python
  ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'TU_IP_AQUI']
  ```

## 📝 Notas Importantes

1. **Solo para desarrollo:** Este método es solo para probar en desarrollo. No uses `0.0.0.0` en producción.

2. **HTTPS requerido para PWA completa:** Para probar todas las funciones PWA (especialmente el prompt de instalación), necesitas HTTPS. Considera usar:
   - ngrok (gratis, fácil)
   - localtunnel (gratis)
   - Tu propio certificado SSL

3. **Seguridad:** No expongas tu servidor de desarrollo a internet sin protección.

## 🎯 Próximos Pasos

Una vez que hayas probado en tu celular y todo funcione:

1. ✅ Verifica que el banner de instalación aparece
2. ✅ Prueba la instalación en Android (si tienes)
3. ✅ Prueba las instrucciones en iOS (si tienes)
4. ✅ Verifica que el mensaje de éxito aparece después de instalar
5. ✅ Prueba el funcionamiento offline (si el service worker está activo)

Cuando todo esté probado y funcionando, puedes subir los cambios al servidor de producción.

---

**¿Necesitas ayuda?** Revisa los logs del servidor Django para ver errores específicos.



