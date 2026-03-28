# /workspace/ → Not Found (404)

## Qué hace `/workspace/`

La ruta raíz **`/workspace/`** redirige al “centro de trabajo” según el país del usuario:

- Usuario con empresa en **Chile** → redirige a **`/cl/es/workspace/`**
- Usuario con empresa en **USA** → redirige a **`/us/en/workspace/`**
- Sin sesión o sin empresa → redirige a **`/cl/es/workspace/`**

Si ves **“The requested resource was not found on this server”** en `https://www.egarage.cl/workspace/`, suele ser porque el servidor tiene una versión antigua del código o una configuración de URLs distinta.

## Solución inmediata (usuario)

Usa la URL con prefijo de país en lugar de la raíz:

- **Chile:** https://www.egarage.cl/cl/es/workspace/
- **USA:** https://www.egarage.cl/us/en/workspace/

Esas rutas son las canónicas; `/workspace/` solo hace el redirect a una de ellas.

## Solución en el servidor (desarrollador)

1. **Actualizar el código**  
   Asegúrate de tener en el servidor la versión que incluye la ruta raíz `/workspace/` en `gestion_taller/urls.py` (y en `gestion_taller/compacto/urls.py` si usas esa URLconf).

2. **Comprobar que la ruta existe**  
   En el servidor:
   ```bash
   cd /srv/egarage   # o la ruta del proyecto
   source venv/bin/activate
   python manage.py show_urls 2>/dev/null | grep -i workspace || python -c "
   from django.urls import get_resolver
   r = get_resolver()
   for p in r.url_patterns:
       if hasattr(p, 'pattern') and 'workspace' in str(p.pattern):
           print('OK', p.pattern)
   "
   ```
   Deberías ver algo como `workspace/`.

3. **Reiniciar la aplicación**  
   Tras desplegar los cambios:
   ```bash
   sudo systemctl restart gunicorn
   # o el servicio que uses (uwsgi, etc.)
   ```

4. **Nginx**  
   No hace falta una `location` específica para `/workspace/`. Si tienes `location / { proxy_pass ... }`, las peticiones a `/workspace/` ya llegan a Django. No añadas un `location /workspace/` que devuelva 404.

## Dónde está definido en el código

- **Ruta raíz `/workspace/`:**  
  - `gestion_taller/urls.py` → `path("workspace/", country_aware_workspace_redirect, ...)` (al inicio de `urlpatterns`)
  - `gestion_taller/compacto/urls.py` → mismo patrón por si se usa esa URLconf
- **Vista real del centro de trabajo:**  
  - Chile: `taller/urls_extra/chile.py` → `path("workspace/", centro_trabajo, ...)` bajo el prefijo `cl/es/`
  - USA: `taller/urls_extra/usa.py` → `path("workspace/", centro_trabajo, ...)` bajo el prefijo `us/en/`

Si tras actualizar y reiniciar sigue el 404, revisa que `ROOT_URLCONF` en tu settings apunte a `gestion_taller.urls` (o a la URLconf que incluye estas rutas).
