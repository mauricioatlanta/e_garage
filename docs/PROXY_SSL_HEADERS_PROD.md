# Arreglo recomendado (prod): proxy headers Nginx + Django

Tu sitio ya está operativo. Este ajuste evita redirecciones 301/302 incorrectas a `https://127.0.0.1:8001` y deja la configuración correcta detrás del proxy (Nginx + Cloudflare).

---

## 1) Encontrar el Nginx real que sirve egarage.cl

Ejecuta en el **servidor**:

```bash
# Ver inicio de la config efectiva
sudo nginx -T | sed -n '1,200p' | cat

# Buscar el archivo y línea del server_name egarage.cl
sudo nginx -T | grep -n "server_name egarage.cl"
```

El segundo comando suele mostrar algo como `/etc/nginx/sites-enabled/egarage` (o `egarage.cl`). Abre ese archivo y localiza el bloque `location / { ... }` que hace `proxy_pass http://127.0.0.1:8001;`.

---

## 2) Asegurar proxy headers dentro de `location /`

Dentro del **`location /`** que hace `proxy_pass http://127.0.0.1:8001;`, deja **sí o sí** estas líneas (en este orden):

- `proxy_set_header Host $host;`
- `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`
- `proxy_set_header X-Forwarded-Proto $scheme;`

Con **Cloudflare** (tu caso), suma:

- `proxy_set_header X-Forwarded-Host $host;`

**Bloque `location /` limpio final** (copiar/pegar y ajustar si hace falta):

```nginx
location / {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

Luego validar y recargar:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 3) Django: confirmar SECURE_PROXY_SSL_HEADER

En este repo el settings de producción es **`gestion_taller.settings_prod`** (el override de systemd usa `DJANGO_SETTINGS_MODULE=gestion_taller.settings_prod`). Ese archivo ya tiene:

- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
- `SECURE_SSL_REDIRECT = True` (o vía env)

Para **confirmar en el servidor** que el módulo que se carga es el correcto y que el header está activo:

```bash
sudo -u egarage -g www-data bash -lc 'cd /srv/egarage && source venv/bin/activate && python - <<PY
import os
print("DJANGO_SETTINGS_MODULE =", os.environ.get("DJANGO_SETTINGS_MODULE"))
from django.conf import settings
print("SECURE_PROXY_SSL_HEADER =", getattr(settings, "SECURE_PROXY_SSL_HEADER", None))
print("SECURE_SSL_REDIRECT =", getattr(settings, "SECURE_SSL_REDIRECT", None))
PY'
```

- Si `DJANGO_SETTINGS_MODULE` no es `gestion_taller.settings_prod`, revisa el override de systemd (`/etc/systemd/system/egarage-gunicorn.service.d/override.conf` o similar).
- Si `SECURE_PROXY_SSL_HEADER` sale `None`, agrégalo en el settings que realmente esté cargando (el que muestre `DJANGO_SETTINGS_MODULE`).

Reiniciar la app:

```bash
sudo systemctl restart egarage-gunicorn
```

**Nota:** La unit puede tener `Environment=DJANGO_SETTINGS_MODULE=gestion_taller.settings` y el override lo pisa con `gestion_taller.settings_prod`. Está bien; solo asegúrate de que **ese** settings (el que cargue en prod) tenga `SECURE_PROXY_SSL_HEADER`.

---

## 4) Pruebas

**A) Backend con header de proxy (no debe redirigir a 127.0.0.1):**

```bash
curl -I -H "X-Forwarded-Proto: https" http://127.0.0.1:8001/
```

Esperado: `200` o `302` a una URL pública; **no** `Location: https://127.0.0.1:8001/...`.

**B) Sitio público:**

```bash
curl -I https://egarage.cl/
```

Esperado: `200`.

---

## Referencia en el repo

- Bloque completo de ejemplo: `scripts/nginx_egarage_example.conf`
- Settings prod: `gestion_taller/settings_prod.py` (SECURE_PROXY_SSL_HEADER en línea 70)
