# Solución al Error 413 Request Entity Too Large

## ¿Qué es el error 413?

El error **413 Request Entity Too Large** ocurre cuando intentas subir un archivo (como un logo o imagen) que excede el límite de tamaño configurado en tu servidor web (Nginx).

Por defecto, Nginx tiene un límite muy bajo para la subida de archivos (generalmente **1MB**). Cuando el archivo excede ese límite, el servidor corta la conexión y devuelve el mensaje 413.

## Soluciones

### 1. Solución Rápida: Optimizar la Imagen ⚡

**Antes de tocar el servidor**, verifica el tamaño de tu logo. Los logos para sitios web usualmente **no deberían pesar más de 200 KB - 500 KB**.

Si tu imagen pesa varios MB, utiliza una herramienta para reducir su peso:

- **TinyPNG**: https://tinypng.com/ (comprime PNG y JPG sin pérdida visible de calidad)
- **Squoosh**: https://squoosh.app/ (herramienta de Google para optimizar imágenes)
- **Photoshop**: Guarda para web con calidad optimizada
- **ImageMagick**: Herramienta de línea de comandos

**Formatos recomendados:**
- `.png` para logos con transparencia
- `.webp` para mejor compresión (soporte moderno)
- `.jpg` para fotos (sin transparencia)

Intenta subir la versión optimizada; es muy probable que así el error desaparezca.

### 2. Solución Técnica: Configurar Nginx 🔧

Si necesitas subir archivos grandes o si el logo optimizado sigue fallando, debes aumentar el límite en tu servidor Ubuntu. **Necesitarás acceso SSH**.

#### ⚠️ IMPORTANTE: Encontrar el archivo correcto

**El problema más común es editar el archivo incorrecto.** Nginx usa archivos específicos por sitio, no el archivo general `nginx.conf`.

#### Paso 1: Identificar el archivo de configuración activo

1. **Lista los archivos de configuración activos:**
   ```bash
   ls -la /etc/nginx/sites-enabled/
   ```

2. **Verifica qué archivo está realmente en uso:**
   ```bash
   sudo nginx -T | grep -A 5 "server_name.*egarage"
   ```

3. **O busca todos los archivos que contienen tu dominio:**
   ```bash
   sudo grep -r "egarage.cl" /etc/nginx/sites-enabled/
   ```

**El archivo correcto suele estar en:**
- `/etc/nginx/sites-enabled/egarage.cl` (o similar)
- **NO** en `/etc/nginx/nginx.conf` (ese es el archivo general)

#### Paso 2: Editar el archivo correcto

Una vez identificado el archivo, edítalo:

```bash
sudo nano /etc/nginx/sites-enabled/egarage.cl
```

O si prefieres editar en `sites-available` y luego crear el symlink:

```bash
sudo nano /etc/nginx/sites-available/egarage.cl
sudo ln -s /etc/nginx/sites-available/egarage.cl /etc/nginx/sites-enabled/
```

#### Paso 3: Modificar `client_max_body_size`

**🔴 CRÍTICO:** El `client_max_body_size` debe estar dentro del bloque `server` que maneja tu dominio, **NO** en el bloque `http` general.

**Ubicación correcta:** Dentro del bloque `server` (antes del bloque `location /`)

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name egarage.cl www.egarage.cl;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/egarage.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/egarage.cl/privkey.pem;
    
    # ============================================================================
    # ⚠️ AGREGAR ESTA LÍNEA AQUÍ (dentro del bloque server)
    # ============================================================================
    client_max_body_size 20M;  # Para logos e imágenes pequeñas
    # client_max_body_size 50M;  # Para archivos más grandes
    # client_max_body_size 100M; # Para archivos muy grandes
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # ... resto de la configuración
    }
}
```

**Valores recomendados:**
- `20M`: Para logos e imágenes pequeñas (recomendado)
- `50M`: Para archivos más grandes (fotos de vehículos, documentos)
- `100M`: Para archivos muy grandes (solo si es necesario)

**⚠️ Nota importante:** Si tienes múltiples bloques `server` o `location`, el valor más restrictivo es el que se aplica. Asegúrate de que no haya otro `client_max_body_size` más pequeño en otro lugar.

#### Paso 4: Verificar la configuración activa

**Antes de reiniciar**, verifica que tu cambio esté en la configuración que Nginx realmente usa:

```bash
# Ver toda la configuración activa y buscar client_max_body_size
sudo nginx -T | grep client_max_body_size
```

Deberías ver algo como:
```
client_max_body_size 20M;
```

Si no aparece o muestra un valor diferente, significa que:
- Editaste el archivo incorrecto, o
- Hay otra configuración que está sobrescribiendo la tuya

#### Paso 5: Verificar sintaxis y reiniciar Nginx

1. **Verifica que la sintaxis sea correcta:**
   ```bash
   sudo nginx -t
   ```
   
   Deberías ver:
   ```
   nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
   nginx: configuration file /etc/nginx/nginx.conf test is successful
   ```

2. **Si hay errores**, corrígelos antes de continuar. Los errores te dirán exactamente qué línea tiene el problema.

3. **Reinicia Nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

4. **Verifica el estado:**
   ```bash
   sudo systemctl status nginx
   ```

5. **Verifica nuevamente que el cambio esté activo:**
   ```bash
   sudo nginx -T | grep client_max_body_size
   ```

### 3. Configurar Límites en Django (si es necesario) 🐍

Si aumentaste el límite en Nginx, también debes asegurarte de que Django permita archivos de ese tamaño.

Los límites están configurados en:
- `gestion_taller/settings/prod.py`
- `gestion_taller/settings/production.py`

**Configuración actual:**
```python
# Límites de subida de archivos (debe coincidir con client_max_body_size en Nginx)
FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
```

**Nota:** Django guarda archivos grandes automáticamente en disco temporal, así que estos límites son para archivos que se procesan en memoria.

### 4. Verificar la aplicación en el puerto 8001 🔍

Tu Nginx actúa como proxy hacia una aplicación que corre en el puerto 8001 (probablemente Django/Gunicorn). Es importante verificar que esa aplicación también permita archivos grandes.

#### Identificar qué corre en el puerto 8001

```bash
# Ver qué proceso está usando el puerto 8001
sudo lsof -i :8001

# O con netstat
sudo netstat -tlnp | grep 8001

# O con ss
sudo ss -tlnp | grep 8001
```

**Resultado esperado:** Deberías ver algo como:
```
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
gunicorn 1234 user   5u  IPv4  12345      0t0  TCP *:8001 (LISTEN)
```

#### Si es Django/Gunicorn

Gunicorn no tiene límites propios de tamaño de archivo, pero Django sí (ver sección 3). Si es otra tecnología (Node.js, etc.), revisa su configuración de límites de body.

## Verificación

Después de hacer los cambios:

1. **Verifica que el cambio esté activo:**
   ```bash
   sudo nginx -T | grep client_max_body_size
   ```
   
   Deberías ver tu nuevo valor (ej: `client_max_body_size 20M;`)

2. **Reinicia Nginx:**
   ```bash
   sudo systemctl restart nginx
   sudo systemctl status nginx
   ```

3. **Verifica que la aplicación backend esté corriendo:**
   ```bash
   sudo lsof -i :8001
   ```

4. **Prueba subir un archivo** del tamaño que necesitas.

5. **Revisa los logs en tiempo real** si sigue fallando:
   ```bash
   # En una terminal, mientras intentas subir el archivo
   sudo tail -f /var/log/nginx/error.log
   ```

## Configuración Actual del Proyecto

### Nginx
- **Archivo de configuración:** `scripts/nginx_egarage_example.conf`
- **Límite actual:** `client_max_body_size 50M;`

### Django
- **Archivos de settings:**
  - `gestion_taller/settings/prod.py`
  - `gestion_taller/settings/production.py`
- **Límite actual:** `20MB` (20971520 bytes)

### Modelos
- **Logo de empresa:** Máximo `10MB` (validación en `taller/models/company_settings.py`)

## Resumen de Límites

| Componente | Límite Actual | Ubicación |
|------------|---------------|-----------|
| Nginx | 50MB | `scripts/nginx_egarage_example.conf` |
| Django (memoria) | 20MB | `gestion_taller/settings/prod.py` |
| Django (validación logo) | 10MB | `taller/models/company_settings.py` |

## Diagnóstico Completo

Si el error persiste, ejecuta este diagnóstico completo:

```bash
# 1. Ver todos los archivos de configuración activos
echo "=== Archivos activos en sites-enabled ==="
ls -la /etc/nginx/sites-enabled/

# 2. Ver la configuración completa activa
echo "=== Configuración completa de Nginx ==="
sudo nginx -T

# 3. Buscar TODAS las instancias de client_max_body_size
echo "=== Todas las configuraciones de client_max_body_size ==="
sudo grep -r "client_max_body_size" /etc/nginx/

# 4. Ver qué proceso está en el puerto 8001
echo "=== Proceso en puerto 8001 ==="
sudo lsof -i :8001

# 5. Ver logs recientes
echo "=== Últimos errores de Nginx ==="
sudo tail -20 /var/log/nginx/error.log
```

**Guarda la salida de estos comandos** para diagnosticar el problema.

## Troubleshooting

### El error persiste después de cambiar Nginx

1. **Verifica que editaste el archivo correcto:**
   ```bash
   # Ver qué archivos están activos
   ls -la /etc/nginx/sites-enabled/
   
   # Ver la configuración activa completa
   sudo nginx -T | grep -B 5 -A 5 client_max_body_size
   ```

2. **Verifica que el cambio esté en la configuración activa:**
   ```bash
   sudo nginx -T | grep client_max_body_size
   ```
   
   Si no aparece tu valor o aparece un valor más pequeño, significa que:
   - Editaste el archivo incorrecto
   - Hay otra configuración que lo está sobrescribiendo
   - El archivo no está enlazado correctamente en `sites-enabled`

3. **Busca todas las configuraciones de client_max_body_size:**
   ```bash
   # Buscar en todos los archivos de configuración
   sudo grep -r "client_max_body_size" /etc/nginx/
   ```
   
   **El valor más restrictivo es el que se aplica.** Si hay un `1M` en algún lugar, ese será el límite.

4. **Asegúrate de haber reiniciado Nginx:**
   ```bash
   sudo systemctl restart nginx
   sudo systemctl status nginx
   ```

5. **Revisa los logs de error en tiempo real:**
   ```bash
   # Mientras intentas subir el archivo, ejecuta esto en otra terminal
   sudo tail -f /var/log/nginx/error.log
   ```

6. **Verifica que la aplicación en el puerto 8001 esté funcionando:**
   ```bash
   sudo lsof -i :8001
   curl -I http://127.0.0.1:8001
   ```

### El archivo se sube pero Django lo rechaza

- Verifica los límites en `settings/prod.py`
- Revisa las validaciones en los modelos (ej: `validate_logo_size`)

### Error 502 Bad Gateway después de cambiar Nginx

- Verifica la sintaxis: `sudo nginx -t`
- Revisa que Gunicorn/Django esté corriendo
- Revisa los logs: `sudo journalctl -u gunicorn -n 50`

## Problema: El archivo se sube pero la imagen no se muestra

Si después de solucionar el error 413 el archivo se sube correctamente pero la imagen no se despliega (solo aparece el nombre o un icono de imagen rota), el problema ha pasado del servidor web a la lógica de tu aplicación o a los permisos de carpetas.

### Causas más probables

#### 1. Ruta de archivos estáticos (Nginx) ⚠️ MÁS COMÚN

Como tu aplicación corre en el puerto 8001, Nginx actúa como puente. A veces, la aplicación guarda la imagen en una carpeta (ej. `/media/`), pero Nginx no sabe que debe buscar los archivos físicos en ese disco.

**Solución:** Asegúrate de que en tu configuración de Nginx exista un bloque que sirva esos archivos:

```nginx
location /media/ {
    alias /ruta/a/tu/app/media/;  # La ruta real en tu servidor
    expires 7d;
    add_header Cache-Control "public";
    access_log off;
}
```

**⚠️ IMPORTANTE:** La ruta en `alias` debe ser la **ruta absoluta real** donde Django guarda los archivos (coincide con `MEDIA_ROOT` en Django).

**Para encontrar la ruta correcta:**

1. **En Django (settings/prod.py):**
   ```python
   MEDIA_ROOT = os.path.join(BASE_DIR, "media")
   ```

2. **En el servidor, verifica dónde está realmente:**
   ```bash
   # Si tu app está en /srv/egarage/, entonces MEDIA_ROOT sería:
   # /srv/egarage/media/
   
   # Verifica que la carpeta existe:
   ls -la /srv/egarage/media/
   ```

3. **Actualiza Nginx con la ruta correcta:**
   ```bash
   sudo nano /etc/nginx/sites-enabled/egarage.cl
   ```

   Agrega o actualiza el bloque `location /media/`:
   ```nginx
   location /media/ {
       alias /srv/egarage/media/;  # ⚠️ Ajusta esta ruta según tu instalación
       expires 7d;
       add_header Cache-Control "public";
       access_log off;
   }
   ```

4. **Verifica y reinicia Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

#### 2. Permisos de Carpeta 🔒

Es muy común que la aplicación guarde el archivo, pero Nginx o el navegador no tengan permiso para "leerlo".

**Solución:** Da permisos de lectura a la carpeta donde se suben los logos:

```bash
# Cambia 'www-data' por el usuario que corre Nginx (puede ser 'nginx' o 'www-data')
# Cambia '/srv/egarage/media/' por tu ruta real de MEDIA_ROOT

# Opción 1: Dar permisos al usuario de Nginx
sudo chown -R www-data:www-data /srv/egarage/media/
sudo chmod -R 755 /srv/egarage/media/

# Opción 2: Si el usuario de Django es diferente, dar permisos de lectura a todos
sudo chmod -R 755 /srv/egarage/media/

# Opción 3: Si necesitas que ambos (Django y Nginx) puedan escribir
sudo chown -R tu_usuario_django:www-data /srv/egarage/media/
sudo chmod -R 775 /srv/egarage/media/
```

**Para identificar el usuario correcto:**

```bash
# Ver qué usuario corre Nginx
ps aux | grep nginx

# Ver qué usuario corre Gunicorn/Django
ps aux | grep gunicorn
# o
ps aux | grep python | grep manage.py
```

#### 3. Error en la URL generada 🌐

Si ves el nombre del archivo en el HTML, inspecciona el código (clic derecho en el navegador > Inspeccionar).

**¿La URL es relativa o absoluta?**

- ✅ **Correcto:** `src="/media/logos/empresa_123/logo.png"` o `src="https://egarage.cl/media/logos/empresa_123/logo.png"`
- ❌ **Incorrecto:** `src="logo.png"` (relativa sin `/media/`)
- ❌ **Incorrecto:** `src="http://localhost:8001/media/logo.png"` (apunta a localhost, no funcionará para usuarios externos)

**Solución:** La aplicación debe generar URLs usando el dominio `egarage.cl`, no `localhost:8001`.

**En Django, verifica:**

1. **Settings (prod.py):**
   ```python
   MEDIA_URL = "/media/"  # ✅ Correcto (relativa)
   # O si necesitas absoluta:
   # MEDIA_URL = "https://egarage.cl/media/"
   ```

2. **En templates, usa:**
   ```django
   {% if config.logo %}
       <img src="{{ config.logo.url }}" alt="Logo">
   {% endif %}
   ```

   Django automáticamente genera la URL correcta usando `MEDIA_URL`.

#### 4. Configuración del Framework (Django) 🐍

Dado que usas Django con un proxy en el puerto 8001:

**Verifica que en `urls.py` NO estés sirviendo archivos media en producción:**

```python
# gestion_taller/urls.py

# ✅ CORRECTO: Solo servir media en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**En producción (DEBUG=False), Django NO debe servir archivos media.** Nginx debe hacerlo.

### Cómo diagnosticarlo rápido 🔍

1. **Abre tu web en Chrome/Edge**
2. **Presiona F12** y ve a la pestaña **Network (Red)**
3. **Recarga la página** y busca el archivo de imagen del logo
4. **Mira el Status Code:**
   - **404 Not Found:** Nginx no encuentra el archivo donde dice la URL
     - ✅ Verifica que la ruta en `location /media/` en Nginx coincida con `MEDIA_ROOT` de Django
     - ✅ Verifica que el archivo realmente existe en esa ruta
   - **403 Forbidden:** El archivo está ahí, pero el servidor no tiene permiso para leerlo
     - ✅ Verifica permisos con `ls -la /ruta/media/`
     - ✅ Da permisos con `chmod` y `chown`
   - **200 OK pero imagen rota:** El archivo se descarga pero no es una imagen válida
     - ✅ Verifica que el archivo no esté corrupto
     - ✅ Verifica el Content-Type en los headers de respuesta

### Diagnóstico completo paso a paso

```bash
# 1. Verificar que la carpeta media existe
echo "=== Verificando carpeta media ==="
ls -la /srv/egarage/media/  # Ajusta la ruta según tu instalación

# 2. Verificar permisos
echo "=== Permisos de la carpeta media ==="
ls -ld /srv/egarage/media/
stat /srv/egarage/media/

# 3. Verificar configuración de Nginx
echo "=== Configuración de Nginx para /media/ ==="
sudo nginx -T | grep -A 5 "location /media/"

# 4. Verificar que el archivo existe (reemplaza con el nombre real de tu logo)
echo "=== Buscando archivos de logo ==="
find /srv/egarage/media/ -name "*logo*" -type f

# 5. Verificar MEDIA_ROOT en Django
echo "=== Verificando MEDIA_ROOT en Django ==="
python manage.py shell -c "from django.conf import settings; print('MEDIA_ROOT:', settings.MEDIA_ROOT); print('MEDIA_URL:', settings.MEDIA_URL)"

# 6. Probar acceso directo al archivo
echo "=== Probando acceso directo ==="
# Reemplaza con la ruta real de un logo
curl -I http://localhost/media/logos/empresa_123/logo.png

# 7. Ver logs de Nginx en tiempo real
echo "=== Últimos errores de Nginx ==="
sudo tail -20 /var/log/nginx/error.log
```

### Solución rápida (checklist)

- [ ] **Nginx tiene bloque `location /media/`** configurado
- [ ] **La ruta en `alias` de Nginx coincide con `MEDIA_ROOT` de Django**
- [ ] **La carpeta media existe y tiene permisos correctos** (`755` o `775`)
- [ ] **El usuario de Nginx puede leer la carpeta** (verificar con `sudo -u www-data ls /ruta/media/`)
- [ ] **Django NO está sirviendo archivos media en producción** (solo en DEBUG)
- [ ] **Las URLs generadas son correctas** (inspeccionar en el navegador)
- [ ] **El archivo realmente existe** en el disco (verificar con `ls`)

### Ejemplo de configuración completa de Nginx

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name egarage.cl www.egarage.cl;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/egarage.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/egarage.cl/privkey.pem;
    
    # Tamaño máximo de subida
    client_max_body_size 50M;
    
    # Proxy a Django/Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ⚠️ CRÍTICO: Servir archivos media directamente desde Nginx
    location /media/ {
        alias /srv/egarage/media/;  # ⚠️ Ajusta esta ruta según tu instalación
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
    }

    # Archivos estáticos
    location /static/ {
        alias /srv/egarage/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
}
```

### Comandos útiles

```bash
# Verificar configuración activa de Nginx
sudo nginx -T | grep -A 10 "location /media/"

# Verificar que un archivo específico existe
ls -la /srv/egarage/media/logos/empresa_123/logo.png

# Probar acceso como usuario de Nginx
sudo -u www-data cat /srv/egarage/media/logos/empresa_123/logo.png

# Ver logs de Nginx en tiempo real
sudo tail -f /var/log/nginx/error.log

# Reiniciar Nginx después de cambios
sudo nginx -t && sudo systemctl restart nginx
```

## Referencias

- [Documentación oficial de Nginx - client_max_body_size](http://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size)
- [Documentación de Django - FILE_UPLOAD_MAX_MEMORY_SIZE](https://docs.djangoproject.com/en/stable/ref/settings/#file-upload-max-memory-size)
- [Documentación de Django - MEDIA_ROOT y MEDIA_URL](https://docs.djangoproject.com/en/stable/ref/settings/#media-root)
- [Guía de optimización de imágenes web](https://web.dev/fast/#optimize-your-images)
