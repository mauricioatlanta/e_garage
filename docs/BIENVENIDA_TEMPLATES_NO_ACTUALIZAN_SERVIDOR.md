# Por qué los templates de bienvenida no se actualizan en el servidor

Si actualizaste los `bienvenida.html` de todos los países en el servidor y **siguen viéndose los diseños viejos**, suele deberse a una de estas causas.

---

## 1. Los templates **no son archivos estáticos**

- `collectstatic` **no** copia ni actualiza la carpeta `templates/`.
- Los templates se sirven desde la ruta del proyecto (p. ej. `templates/ar/es/onboarding/bienvenida.html`).
- **Qué hacer:** Asegurarte de que el **código del proyecto** (incluida `templates/`) se haya desplegado bien (p. ej. `git pull`, rsync, etc.), no solo `collectstatic`.

---

## 2. Los templates no se desplegaron realmente

Puede que solo hayas actualizado estáticos o reiniciado servicios, pero **no** los HTML.

**Comprobar en el servidor:**

```bash
cd /srv/egarage   # o la ruta donde esté el proyecto

# Ver que los bienvenida existen y tienen la fecha reciente
ls -la templates/ar/es/onboarding/bienvenida.html
ls -la templates/us/es/onboarding/bienvenida.html
# etc.

# Buscar "eGarage Argentina" o "futuristic-glow" (propio del refactor)
grep -l "futuristic-glow" templates/*/es/onboarding/bienvenida.html
```

Si las fechas son viejas o no encuentras esas cadenas, **los templates no se actualizaron** en ese directorio.

**Solución:** Volver a desplegar el repo (o al menos `templates/`) y asegurarte de que no se excluya esa carpeta en tu script de deploy.

---

## 3. Gunicorn no se reinició

Aunque Django lee los templates desde disco en cada petición, siempre es buena práctica reiniciar la app tras un deploy.

```bash
sudo systemctl restart egarage-gunicorn
# o
sudo systemctl restart gunicorn
```

Comprobar que el servicio está activo:

```bash
sudo systemctl status egarage-gunicorn
```

---

## 4. Caché externa (Cloudflare, Nginx, etc.)

Si usas **Cloudflare** (u otro CDN) o **Nginx** con `proxy_cache`:

- Pueden estar cacheando el **HTML** de las bienvenidas.
- Aunque el servidor ya sirva el template nuevo, se sigue devolviendo la versión cacheada.

**Qué hacer:**

- **Cloudflare:** Entra al dashboard → Caching → Purge Cache (Purge Everything o solo las URLs de bienvenida).
- **Nginx:** Si tienes `proxy_cache` para esas rutas, borrar la caché de Nginx o desactivarla para `/ar/`, `/cl/`, etc., y recargar:

  ```bash
  sudo nginx -t && sudo systemctl reload nginx
  ```

---

## 5. Caché del navegador

El navegador puede estar usando una versión antigua de la página.

**Qué hacer:** Hard refresh:

- Windows/Linux: `Ctrl + Shift + R` o `Ctrl + F5`
- Mac: `Cmd + Shift + R`

O abrir la URL en **modo incógnito** para probar sin caché.

---

## Checklist rápido en el servidor

Ejecuta en el servidor (ajusta `DJANGO_SETTINGS_MODULE` y ruta del proyecto si usas otras):

```bash
cd /srv/egarage
source venv/bin/activate   # si usas venv

# 1. Confirmar que Django ve los templates actualizados
python manage.py shell -c "
from pathlib import Path
from django.conf import settings
td = Path(settings.BASE_DIR) / 'templates'
for p in ['ar/es/onboarding/bienvenida.html', 'us/es/onboarding/bienvenida.html']:
    f = td / p
    exists = f.exists()
    content = f.read_text(encoding='utf-8', errors='ignore') if exists else ''
    has_new = 'futuristic-glow' in content or 'glass-card' in content
    print(f'{p}: exists={exists}, has_refactor={has_new}')
"

# 2. Reiniciar la app
sudo systemctl restart egarage-gunicorn

# 3. Probar una bienvenida (desde el propio servidor)
curl -sI -H "Host: egarage.cl" http://127.0.0.1:8001/ar/es/bienvenida/ | head -5
curl -sI -H "Host: egarage.cl" http://127.0.0.1:8001/us/es/bienvenida/ | head -5
```

Si `has_refactor=True` y `curl` devuelve 200, el servidor está sirviendo los templates nuevos. Si en el navegador sigues viendo el diseño viejo, el problema está en **caché (Cloudflare, Nginx o navegador)**.

---

## Resumen

| Causa | Comprobación | Acción |
|-------|--------------|--------|
| Templates no desplegados | `ls -la`, `grep` en `templates/` | Volver a desplegar `templates/` |
| Gunicorn sin reiniciar | `systemctl status egarage-gunicorn` | `sudo systemctl restart egarage-gunicorn` |
| Caché Cloudflare/Nginx | Ver configuración de caché | Purge cache / limpiar `proxy_cache` |
| Caché navegador | Probar en incógnito o otro navegador | Hard refresh o purgar caché del sitio |

Con esto deberías poder identificar por qué no se actualizan los bienvenidos y corregirlo.
