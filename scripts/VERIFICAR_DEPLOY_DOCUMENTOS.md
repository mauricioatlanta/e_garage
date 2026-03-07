# Verificar deploy – formulario documentos (jQuery, 403, Tax, Service Worker)

Los errores **jQuery is not defined**, **Unexpected token 'catch'**, **HTTP 403** y **tax en 0** suelen deberse a que el servidor o el navegador siguen usando código/caché antiguo.

> **Si en tu servidor no existe `/srv/egarage` o no tienes `sudo`**, usa la ruta real del proyecto y el método de reinicio de tu hosting. Ver [docs/DEPLOY_TROUBLESHOOTING.md](../docs/DEPLOY_TROUBLESHOOTING.md).

## 1. En el servidor (tras subir código)

```bash
cd /srv/egarage   # o la ruta real del proyecto en tu servidor (ej. ~/e_garage)

# ¿jQuery está primero en base.html?
grep -A1 "<head>" templates/base.html
# Debe verse: <script src="...jquery..."></script> justo después de <head>

# ¿marketplace_tooltip usa .then/.catch (no try/catch)?
grep -n "\.then\|\.catch\|try {" static/marketplace_tooltip.js | head -20

# ¿Service Worker tiene versión nueva?
grep "CACHE_NAME" static/service-worker.js
# Debe ser egarage-v2.1.5 (o superior)

# Recolectar estáticos y reiniciar
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

## 2. Caché del navegador y Service Worker

Tras desplegar:

1. **Opción A – Forzar actualización**
   - Abre la página del formulario de documentos.
   - **Chrome/Edge:** `Ctrl+Shift+R` (Windows) o `Cmd+Shift+R` (Mac), o F12 → pestaña Application → Application → Storage → **Clear site data**.
   - **Firefox:** `Ctrl+Shift+Delete` → marcar “Caché” → Limpiar.

2. **Opción B – Desregistrar Service Worker**
   - F12 → pestaña **Application** (Chrome) o **Almacenamiento** (Firefox).
   - Service Workers → **Unregister** para egarage.cl.
   - Recarga la página (F5 o Ctrl+R).

3. **Opción C – Probar en ventana de incógnito**
   - Abre una ventana de incógnito/privada y entra a la URL del formulario de documentos. Ahí no debería usarse caché antigua.

## 3. Comprobar que los fixes están activos

En la consola del navegador (F12 → Console), tras cargar el formulario:

- No debería aparecer `jQuery is not defined` ni `Unexpected token 'catch'`.
- En el objeto de configuración del form (donde hace log de “Document form inicializado”), `URL_NEXT_NUMBER` debería ser una URL que contenga **`/documentos/api/`** (no solo `/us/api/`).
- Si hay tax configurado (ej. 9%), en la sección Totals debería verse la línea “Tax (9%)” y el total debería incluir ese importe.

## 4. Si sigue fallando

- Confirma que en el servidor los archivos que editaste son los que está sirviendo Django (misma ruta del proyecto, mismo `STATIC_ROOT` si usas `collectstatic`).
- Revisa en F12 → Network si `jquery`, `select2`, `marketplace_tooltip.js` y `service-worker.js` se piden con 200 y sin servir desde “disk cache” o “ServiceWorker” con fecha antigua.
