# Error 500 en https://www.egarage.cl/ – Diagnóstico

## 1. Obtener el error real (en el servidor)

En el servidor donde está desplegado eGarage:

```bash
cd /srv/egarage   # o la ruta real del proyecto
source venv/bin/activate
```

**Opción A – Logs de Gunicorn (lo más rápido)**

```bash
sudo journalctl -u gunicorn -n 100 --no-pager
```

Busca líneas con `Error`, `Exception`, `Traceback` o `ModuleNotFoundError`. Ahí suele estar la causa del 500.

**Opción B – Reproducir el fallo con Django**

```bash
python manage.py shell -c "
from django.test import Client
c = Client()
r = c.get('/')
print('Status:', r.status_code)
if r.status_code >= 400:
    print('Content (first 2000 chars):', (r.content or b'')[:2000])
"
```

Si el 500 ocurre al **cargar las URLs** (antes de llegar a la vista), el `get('/')` puede fallar con una excepción. Ejecuta en su lugar:

```bash
python manage.py check
```

Si sale `ModuleNotFoundError: No module named 'taller.models.pieza_desarme'`, el fallo es el del módulo Desarme.

**Opción C – Probar solo la carga de URLs**

```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()
from django.urls import get_resolver
get_resolver().url_patterns
print('URLs cargaron OK')
"
```

Si este script explota con `ModuleNotFoundError` (o similar), el error está al cargar la URLconf.

---

## 2. Causa más probable: import de Desarme

Si en los logs o al ejecutar lo anterior aparece:

```text
ModuleNotFoundError: No module named 'taller.models.pieza_desarme'
```

es que en esa rama/despliegue **no existe** el módulo Desarme, pero `taller/urls_desarme.py` (o las vistas de desarme) intentan importarlo y rompen todo el arranque.

**Solución:** usar la versión de `taller/urls_desarme.py` que **no rompe** cuando el modelo no existe:

- El archivo debe tener un `try/except ImportError`: si falla `from taller.models.pieza_desarme import PiezaDesarme`, debe asignar `urlpatterns = []` y `app_name = "desarme"` en el `except`, sin importar las vistas.

Contenido correcto (resumen): ver el bloque en `taller/urls_desarme.py` en este repo (con el `try`/`except ImportError` y `urlpatterns = []` en el except).

**Pasos en el servidor:**

1. Editar `taller/urls_desarme.py` y pegarlo con la versión que tiene el fallback.
2. Comprobar:

   ```bash
   python manage.py check
   sudo systemctl restart gunicorn
   sudo journalctl -u gunicorn -n 30 --no-pager
   ```

3. Probar de nuevo https://www.egarage.cl/

---

## 3. Otras causas posibles de 500

- **Template faltante:** si el error es `TemplateDoesNotExist: landing/seleccionar_pais.html`, revisar que `templates/landing/seleccionar_pais.html` esté desplegado y que `TEMPLATES` en settings apunte a esa carpeta.
- **Base de datos:** excepciones tipo `OperationalError`, `ProgrammingError` al arrancar o al cargar la home → revisar migraciones, conexión y variables de entorno de la BD.
- **Middleware o context processors:** si el 500 sale al procesar la request, revisar los logs (Gunicorn) para ver el traceback; desactivar de forma temporal middleware o context processors recientes para acotar el fallo.

---

## 4. Resumen rápido

| Síntoma en logs / al ejecutar              | Acción |
|-------------------------------------------|--------|
| `ModuleNotFoundError ... pieza_desarme`   | Actualizar `taller/urls_desarme.py` con el fallback (try/except) y reiniciar Gunicorn. |
| `TemplateDoesNotExist`                    | Revisar que los templates estén desplegados y `TEMPLATES` en settings. |
| Error de base de datos                    | Revisar migraciones, conexión y env de la BD. |
| Otro traceback                            | Usar el traceback completo de Gunicorn para localizar vista/middleware y corregir. |
