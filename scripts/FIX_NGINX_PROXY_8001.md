# Fix Nginx: socket → puerto 8001

Cuando el vhost usa el socket viejo (`/run/gunicorn/gunicorn.sock`) y Gunicorn corre en **127.0.0.1:8001**, Nginx debe apuntar al puerto.

## Cómo ejecutar el fix (script opcional)

El archivo **FIX_NGINX_PROXY_8001.md** es solo documentación. Para automatizar el cambio en el servidor puedes usar:

1. **Subir el script al servidor** (desde tu PC, si tienes el repo):
   ```bash
   scp scripts/fix_nginx_proxy_8001.sh usuario@tu-servidor:/tmp/
   ```
2. **En el servidor**, ejecutar (por defecto usa `/etc/nginx/sites-enabled/egarage`):
   ```bash
   sudo bash /tmp/fix_nginx_proxy_8001.sh
   ```
   Si tu vhost tiene otro nombre:
   ```bash
   sudo bash /tmp/fix_nginx_proxy_8001.sh /etc/nginx/sites-enabled/egarage.cl
   ```

El script hace backup del vhost, aplica los reemplazos, ejecuta `nginx -t` y `systemctl reload nginx`.

---

## 1. Editar el vhost (manual)

Archivo típico: `/etc/nginx/sites-enabled/egarage` o `/etc/nginx/sites-enabled/egarage.cl`.

**Cambiar estas 2 cosas:**

- Reemplazar:
  ```nginx
  proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
  ```
  por:
  ```nginx
  proxy_pass http://127.0.0.1:8001;
  ```

- Añadir (si no está) dentro del `location /`:
  ```nginx
  proxy_set_header X-Forwarded-Proto $scheme;
  ```

## 2. Bloque mínimo correcto

El `location /` debe quedar así (como mínimo):

```nginx
location / {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://127.0.0.1:8001;
}
```

## 3. Aplicar cambios

```bash
sudo nginx -t
sudo systemctl reload nginx
```

(Con `reload` basta; no hace falta `restart`.)

## 4. Verificación

```bash
curl -I http://127.0.0.1/ -H "Host: egarage.cl"
```

Y comprobar que Gunicorn recibe el request:

```bash
tail -n 20 /srv/egarage/logs/gunicorn_access.log
```

## Nota: un solo upstream

- **Socket:** si quieres usar socket, configura `egarage-gunicorn` con `--bind unix:/run/egarage/gunicorn.sock` y en Nginx `proxy_pass http://unix:/run/egarage/gunicorn.sock;`.
- **Puerto (recomendado ahora):** deja Gunicorn en `127.0.0.1:8001` y elimina cualquier referencia a `/run/gunicorn/gunicorn.sock` en el vhost.

Referencia completa del vhost: `scripts/nginx_egarage_example.conf`.
