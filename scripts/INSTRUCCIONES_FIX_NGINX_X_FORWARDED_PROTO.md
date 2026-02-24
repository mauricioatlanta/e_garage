# 🔧 Fix: Configurar X-Forwarded-Proto en Nginx

## Problema
Django está redirigiendo a `https://127.0.0.1:8001/...` en lugar de mantener el dominio correcto `https://egarage.cl/...`, causando errores 502.

## Causa
Nginx no está enviando el header `X-Forwarded-Proto` a Django, por lo que Django no sabe que la conexión original era HTTPS.

## Solución

### 1. Verificar configuración actual

Ejecuta en el servidor:

```bash
# Subir el script al servidor primero
scp scripts/fix_nginx_x_forwarded_proto.sh usuario@servidor:/tmp/

# Luego ejecutar en el servidor
ssh usuario@servidor
sudo bash /tmp/fix_nginx_x_forwarded_proto.sh
```

O manualmente:

```bash
# Buscar archivo de configuración
sudo grep -R "proxy_pass.*8001" -n /etc/nginx/sites-enabled /etc/nginx/sites-available | head -n 20

# Ver logs de error
sudo tail -n 80 /var/log/nginx/error.log
```

### 2. Editar configuración de Nginx

Abre el archivo que encontraste (normalmente `/etc/nginx/sites-available/egarage` o similar):

```bash
sudo nano /etc/nginx/sites-available/egarage
# o
sudo nano /etc/nginx/sites-enabled/egarage
```

### 3. Agregar headers en el bloque `location /`

Busca el bloque que tiene `proxy_pass http://127.0.0.1:8001;` y asegúrate de que tenga estos headers:

```nginx
location / {
    proxy_pass http://127.0.0.1:8001;
    
    # 🔥 CRÍTICO: Estos headers deben estar presentes
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;  # ← Este es el más importante
    
    # Opcionales pero recomendados
    proxy_set_header X-Forwarded-Host $server_name;
    proxy_set_header X-Forwarded-Port $server_port;
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

**Nota importante:** Si tienes SSL en Nginx (certbot), `$scheme` será automáticamente `https` cuando la conexión llegue por el puerto 443.

### 4. Verificar y recargar Nginx

```bash
# Verificar sintaxis
sudo nginx -t

# Si todo está bien, recargar
sudo systemctl reload nginx
```

### 5. Verificar Django settings

Ya está configurado correctamente en `gestion_taller/settings.py` línea 74:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
```

✅ Esto ya está correcto, no necesita cambios.

### 6. Reiniciar Gunicorn

```bash
sudo systemctl restart egarage-gunicorn
# o el nombre de tu servicio
sudo systemctl restart gunicorn
```

### 7. Probar

Desde el servidor, simula una petición con headers como Nginx:

```bash
curl -I http://127.0.0.1:8001/cl/es/settings/ \
  -H "Host: egarage.cl" \
  -H "X-Forwarded-Proto: https"
```

**Resultado esperado:**
- ✅ NO debe redirigir a `https://127.0.0.1:8001/...`
- ✅ Debe responder 200 o redirigir dentro de `https://egarage.cl/...`

### 8. Verificar logs si persiste el problema

```bash
# Logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Logs de Gunicorn
sudo journalctl -u egarage-gunicorn -f
# o
sudo tail -f /var/log/gunicorn/error.log
```

## Ejemplo completo de configuración Nginx

Ver archivo de referencia: `scripts/nginx_egarage_example.conf`

## Checklist

- [ ] Nginx tiene `proxy_set_header X-Forwarded-Proto $scheme;` en `location /`
- [ ] Django tiene `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
- [ ] `sudo nginx -t` pasa sin errores
- [ ] Nginx recargado: `sudo systemctl reload nginx`
- [ ] Gunicorn reiniciado: `sudo systemctl restart egarage-gunicorn`
- [ ] Prueba con curl funciona correctamente
- [ ] No hay errores 502 en los logs

## Notas adicionales

- El error 500 original (taller_tecnico.user_id) ya está resuelto ✅
- Este fix resuelve el problema de redirección HTTPS incorrecta
- Evita futuros 301/302 raros a `127.0.0.1:8001`
