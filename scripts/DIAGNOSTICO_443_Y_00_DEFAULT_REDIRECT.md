# Diagnóstico 443 y conflicto 00-default-redirect

## Tu configuración actual (ya correcta)

### Django (`gestion_taller/settings_prod.py`)
- ✅ `SECURE_SSL_REDIRECT = True` (o vía `DJANGO_SECURE_SSL_REDIRECT`)
- ✅ `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
- ✅ `USE_X_FORWARDED_HOST = True`

### Nginx (headers en `scripts/nginx_egarage_example.conf`)
El bloque `location /` de ejemplo ya tiene los headers necesarios:
```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $host;
```

**⚡ Por qué X-Forwarded-Proto es crítico**

Flujo con proxy TLS:
```
Cliente → HTTPS → Nginx
Nginx → HTTP → Gunicorn (socket)
```

Sin `X-Forwarded-Proto: https`, Django cree que la petición es HTTP. Con `SECURE_SSL_REDIRECT=True` redirige de nuevo a HTTPS → loop / 301 raros.  
`SECURE_PROXY_SSL_HEADER` existe precisamente para confiar en ese header.

**Nota:** Si usas socket en vez de puerto, cambia `proxy_pass http://127.0.0.1:8001` por:
```nginx
proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
```

---

## Arreglo 2 (recomendado): Server 80 limpio sin 404

Si el server 80 termina en `return 404;`, reemplázalo por un redirect simple.

### 1) Backup

```bash
sudo cp -a /etc/nginx/sites-available/egarage /etc/nginx/sites-available/egarage.bak_$(date +%F_%H%M)
```

### 2) Re-escribir el archivo completo (heredoc + tee)

```bash
sudo tee /etc/nginx/sites-available/egarage >/dev/null <<'NGINX'
server {
    listen 80;
    server_name egarage.cl www.egarage.cl;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name egarage.cl www.egarage.cl;

    location /static/ {
        alias /srv/egarage/staticfiles/;
    }

    location /media/ {
        alias /srv/egarage/media/;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
    }

    ssl_certificate /etc/letsencrypt/live/egarage.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/egarage.cl/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
NGINX
```

### 3) Recarga y test

```bash
sudo nginx -t && sudo systemctl reload nginx

curl -I http://egarage.cl/us/settings/ --resolve egarage.cl:80:127.0.0.1
curl -kI https://egarage.cl/us/settings/ --resolve egarage.cl:443:127.0.0.1
```

Para ver solo las líneas relevantes del test HTTPS:
```bash
curl -kI https://egarage.cl/us/settings/ --resolve egarage.cl:443:127.0.0.1 | egrep -i "HTTP/|Location:|Server:"
```

Esperado: `200` o `302` (login), sin loops 301.

---

## Posible problema: 00-default-redirect toma el 443

Si `00-default-redirect` hace `listen 443 ssl` **y** está en `sites-enabled` antes que el vhost de egarage, puede estar capturando todo el tráfico 443.

### 1. Ejecutar diagnóstico en el servidor

```bash
sudo bash scripts/diagnostico_443_nginx.sh
```

O manualmente:
```bash
sudo ls -lah /etc/nginx/sites-enabled
sudo sed -n '1,220p' /etc/nginx/sites-available/00-default-redirect
sudo sed -n '1,260p' /etc/nginx/sites-available/default
```

### 2. Comprobar qué server_name usa 00-default-redirect

- Si usa `server_name _` o `default_server` en 443, ese bloque gana para todo lo que no coincida con otro vhost.
- El vhost de egarage debe tener `server_name egarage.cl www.egarage.cl` y estar enabled.

### 3. Solución típica

**Opción A – Deshabilitar 00-default-redirect en 443**  
Si solo necesitas redirect HTTP → HTTPS genérico, que 00-default-redirect escuche solo en 80, no en 443.

**Opción B – Orden de precedencia**  
Nginx usa el primer `server` que coincida por `server_name`. Si 00-default-redirect tiene `default_server` en 443, captura todo. Asegura que el vhost de egarage exista y esté en `sites-enabled` con `server_name egarage.cl www.egarage.cl`.

**Opción C – Quitar 00-default-redirect de sites-enabled**  
Si no lo necesitas:
```bash
sudo rm /etc/nginx/sites-enabled/00-default-redirect
sudo nginx -t && sudo systemctl reload nginx
```

### 4. Test HTTPS local con SNI correcto

```bash
curl -kI https://egarage.cl/us/settings/ --resolve egarage.cl:443:127.0.0.1
curl -kI https://www.egarage.cl/us/settings/ --resolve www.egarage.cl:443:127.0.0.1
```

Esperado: `200` o `302` (login), sin loops de redirect raros.

---

## Después de cambiar Nginx

```bash
sudo nginx -t && sudo systemctl reload nginx
```
