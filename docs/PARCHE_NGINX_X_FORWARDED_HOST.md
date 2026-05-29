# Parche Nginx: X-Forwarded-Host y 502/500

## Causa

El proyecto usa **`USE_X_FORWARDED_HOST = True`** en:

- `gestion_taller/settings.py`
- `gestion_taller/settings_prod.py` (y prod.py, production.py, compacto)

Y hay código que depende del host correcto:

- **`taller/middleware/country_context.py`** → `request.get_host().lower()` (línea 199)
- **`taller/views_extra/account_adapter.py`** → `request.get_host()` y `request.META` (redirects/seguridad)
- Múltiples vistas que usan **`request.build_absolute_uri(...)`** (PDFs, WhatsApp, pagos, documentos)

Si Nginx no envía `X-Forwarded-Host`, Django puede recibir `Host` incorrecto o vacío y devolver 500 al construir URLs o al validar redirects.

---

## 1. Ver el vhost actual (en el servidor)

```bash
sudo sed -n '1,140p' /etc/nginx/sites-enabled/egarage
```

En el bloque `location /` debe quedar algo como:

```nginx
location / {
    include proxy_params;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://unix:/run/gunicorn/gunicorn.sock:/;
}
```

Si falta `X-Forwarded-Host`, aplicar el parche siguiente.

---

## 2. Parche rápido (añadir headers en el servidor)

**Respaldo y parche con Python:**

```bash
sudo cp /etc/nginx/sites-enabled/egarage /etc/nginx/sites-enabled/egarage.pre_xfh

sudo python3 - <<'PY'
from pathlib import Path
p = Path('/etc/nginx/sites-enabled/egarage')
text = p.read_text()
old = """location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock:/;
"""
new = """location / {
        include proxy_params;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock:/;
"""
if old in text:
    text = text.replace(old, new)
else:
    print("No encontré el bloque exacto; revisa manualmente el archivo.")
p.write_text(text)
PY

sudo nginx -t
sudo systemctl restart nginx
curl -I https://www.egarage.cl
```

Si el bloque tiene otra indentación (p. ej. 4 espacios en vez de 8), ajusta `old` en el script para que coincida exactamente con lo que muestra `sed -n '1,140p' /etc/nginx/sites-enabled/egarage`.

---

## 3. Si sigue fallando: log de Nginx

```bash
sudo tail -n 80 /var/log/nginx/error.log
```

O si hay `error_log` por sitio:

```bash
sudo grep -R "error_log" /etc/nginx/sites-enabled /etc/nginx/conf.d -n
```

---

## Pendiente después de estabilizar

| Tema | Acción |
|------|--------|
| **Migración 0074** | `table "taller_checklistingreso" already exists` → sanear migraciones (fake o merge). |
| **.env.prod** | systemd se queja: `Ignoring invalid environment assignment '#...'` → quitar o comentar líneas que empiecen con `#` en el archivo que se carga como EnvironmentFile, o no usar ese archivo para comentarios. |

---

## Referencia: código que usa host / build_absolute_uri

Búsqueda en repo (Django que depende de X-Forwarded-Host / Host):

- **Settings:** `USE_X_FORWARDED_HOST` en `gestion_taller/settings*.py`
- **Middleware:** `taller/middleware/country_context.py` → `request.get_host()`
- **Auth/redirects:** `taller/views_extra/account_adapter.py` → `request.get_host()`, `request.META`
- **URLs/redirects:** `taller/auth/decorators.py`, `taller/urls_extra/usa.py` → `request.get_host()`
- **PDFs/links:** `taller/reportes/views.py`, `taller/documentos/views.py`, `taller/views_extra/payment_views.py`, `taller/whatsapp/`, `taller/services/document_output_service.py`, etc. → `request.build_absolute_uri(...)`

Con el parche de Nginx (proxy_set_header X-Forwarded-Host y X-Forwarded-Proto), ese código debería recibir el host correcto y dejar de provocar 500.
