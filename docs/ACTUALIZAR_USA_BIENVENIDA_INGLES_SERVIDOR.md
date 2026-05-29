# Actualizar: USA → Bienvenida en Inglés (servidor)

Para que al hacer clic en **USA** en https://www.egarage.cl/ se abra la bienvenida en **inglés** (`/us/en/bienvenida/`), hay que subir estos archivos y reiniciar.

---

## 1. Archivos a subir

Sube los que correspondan a la **estructura que use tu servidor** (raíz del proyecto o `deploy_atlantareciclajes`).

### Si el servidor usa la raíz del proyecto (`templates/`, `taller/`)

| Archivo | Reemplazar en el servidor por |
|---------|------------------------------|
| `templates/landing/seleccionar_pais.html` | El de tu copia local actualizado |
| `taller/middleware/lang_policy.py` | El de tu copia local actualizado |

### Si el servidor usa `deploy_atlantareciclajes/`

| Archivo | Reemplazar en el servidor por |
|---------|------------------------------|
| `deploy_atlantareciclajes/templates/landing/seleccionar_pais.html` | El de tu copia local actualizado |
| `deploy_atlantareciclajes/templates/templates/landing/seleccionar_pais.html` | El de tu copia local actualizado |
| `deploy_atlantareciclajes/taller/middleware/lang_policy.py` | El de tu copia local actualizado |

---

## 2. Reiniciar la aplicación (obligatorio)

`lang_policy.py` es código Python: **el proceso tiene que recargarse** o seguirá usando la versión anterior.

### DigitalOcean
```bash
# En la consola de DigitalOcean, o vía:
touch /var/www/egarage/ tmp/restart.txt
# (ajusta la ruta a la de tu proyecto)
```

En la pestaña **Web** → **Reload** (o **Reload e.garage.cl**).

### Gunicorn / systemd / Nginx + uWSGI
```bash
sudo systemctl restart gunicorn
# o
sudo systemctl restart egarage
# (según el nombre de tu servicio)
```

### Otros
Reinicia el proceso/workers que ejecutan Django (uWSGI, Gunicorn, etc.).

---

## 3. Caché

- **Navegador**: prueba en ventana de incógnito o borra cookies de `egarage.cl` / `www.egarage.cl`.
- **Cloudflare / CDN**: si usas Cloudflare, purga la caché para `/` y `/us/en/bienvenida/` (o haz un Purge Everything de prueba).
- **Django**: si tienes `Template`/`Memcached`/`Redis` para templates o vistas, no suele afectar a `seleccionar_pais`; si tienes caché de vistas para `/`, invalídala o reinicia el backend de caché.

---

## 4. Comprobar

1. Abre https://www.egarage.cl/ en incógnito.
2. Haz clic en **USA**.
3. La URL debe ser `https://www.egarage.cl/us/en/bienvenida/` y el contenido en **inglés** (p. ej. “Welcome to eGarage USA”, “Start Free”, “Login”).

---

## 5. Si sigue en español

- Confirma que **los archivos subidos son los que editaste** (sobre todo `lang_policy.py` y `seleccionar_pais.html`).
- Comprueba que **reiniciaste bien** el servicio/workers (a veces se reinicia solo el front, no el proceso Python).
- Revisa **qué `settings` usa el servidor** (`DJANGO_SETTINGS_MODULE` o `--settings`): que `taller.middleware.lang_policy.LanguagePolicyMiddleware` esté en `MIDDLEWARE`.
- Si el servidor corre desde **`deploy_atlantareciclajes`**, asegúrate de haber subido los 3 archivos de la tabla de esa sección.
