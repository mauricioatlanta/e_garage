# Diagnóstico: página sin estilos (fondo blanco, CSS no carga)

Si `/cl/es/servicios/` (u otras rutas) se ven sin estilos, suele ser que los estáticos no se sirven bien.

## 1. Comprobar que los archivos existen en el servidor

```bash
# En el servidor
ls -la /srv/egarage/staticfiles/css/dashboard.css
ls -la /srv/egarage/staticfiles/css/galaxy_theme.css
ls -la /srv/egarage/staticfiles/css/output.css
```

Si no existen, ejecutar:

```bash
cd /srv/egarage
python manage.py collectstatic --noinput
```

## 2. Nginx: quitar try_files del bloque /static/

**Causa habitual:** con `alias` + `try_files $uri =404`, Nginx resuelve mal la ruta y devuelve 404 para los CSS.

Editar la config de Nginx (ej. `/etc/nginx/sites-enabled/egarage.cl`):

- En `location /static/` **eliminar** la línea `try_files $uri =404;`.
- Dejar solo:

```nginx
location /static/ {
    alias /srv/egarage/staticfiles/;
    expires 5m;
    add_header Cache-Control "public, max-age=300" always;
    access_log off;
}
```

Comprobar y recargar:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 3. Probar que los estáticos responden

```bash
# Desde el servidor (debe devolver 200 y contenido CSS)
curl -sI https://egarage.cl/static/css/dashboard.css
curl -sI https://egarage.cl/static/css/galaxy_theme.css
```

Si ves **404**, el fallo está en Nginx (alias/try_files) o en que no se ha hecho `collectstatic`.

## 4. Ver qué URLs de CSS genera la página

Abrir en el navegador:

- https://egarage.cl/cl/es/servicios/
- F12 → pestaña Red/Network → recargar.
- Revisar las peticiones a `*.css`: si salen como `/static/css/...` y devuelven 200, los estilos deberían cargar. Si salen 404, seguir pasos 1–2.

## Referencia: config de ejemplo corregida

Ver `scripts/nginx_egarage_example.conf`: bloque `location /static/` sin `try_files`.
