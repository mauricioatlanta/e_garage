# Troubleshooting: jQuery y formulario de documentos

## Causa raíz

En `/us/documentos/form/` aparecen:

```
Uncaught ReferenceError: $ is not defined
Uncaught ReferenceError: jQuery is not defined
select2.full.js:32 Uncaught ReferenceError: jQuery is not defined
autocomplete_light.min.js:1 Uncaught ReferenceError: jQuery is not defined
```

**Causa:** El archivo `static/vendor/jquery/jquery-3.6.0.min.js` era un **placeholder** (solo un comentario), no la librería real. El navegador cargaba ese "script" vacío, por lo que `$` y `jQuery` nunca se definían.

## Efectos en cascada

1. Falla JS inline que usa `$`
2. Falla Select2 (depende de jQuery)
3. Falla DAL (django-autocomplete-light)
4. El formulario queda esperando DAL indefinidamente

## Solución aplicada

Se modificó `templates/base.html` para cargar jQuery desde el **CDN oficial** en lugar del archivo local placeholder:

```html
<script src="https://code.jquery.com/jquery-3.6.0.min.js" integrity="sha256-..." crossorigin="anonymous"></script>
```

Orden de carga (correcto):
1. jQuery (CDN)
2. `{% block extra_js %}` (scripts del template)
3. `form.media` (Select2 + DAL)

## Reemplazar placeholder por archivo real (opcional)

Si prefieres servir jQuery localmente (ej. producción sin CDN):

```bash
cd /srv/egarage/static/vendor/jquery
curl -o jquery-3.6.0.min.js https://code.jquery.com/jquery-3.6.0.min.js
```

Luego en `base.html` puedes volver a:

```html
<script src="{% static 'vendor/jquery/jquery-3.6.0.min.js' %}"></script>
```

Y ejecutar:

```bash
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

## Verificación

Tras el fix, la consola del navegador **no** debe mostrar:
- `$ is not defined`
- `jQuery is not defined`
- Errores de Select2/DAL por jQuery

El autocomplete de cliente y demás campos DAL deben funcionar en `/us/documentos/form/` y `/us/es/vehiculos/crear/`.
