# Troubleshooting: country_url y Uruguay

## Causa raíz confirmada

El problema estaba en `taller/templatetags/country_url.py`.

Para requests de Uruguay como `/uy/documentos/ver/3/`, el helper `_country_ns_from_path()` no contemplaba el prefijo `/uy/` y caía en el fallback `return "chile"`. Como resultado:

- `country_ns = chile`
- Todas las URLs generadas por `country_url` apuntaban a Chile: `/cl/es/documentos/`, `/cl/es/documentos/form/3/`, etc.
- Los namespaces `desarme:*` fallaban con `NoReverseMatch` porque intentaba resolverlos dentro de `chile`, donde no existían.

## Síntomas

- En una página de detalle de documento en Uruguay (`/uy/documentos/ver/<id>/`), los botones (Volver a lista, Editar, Exportar PDF, Seguimiento) llevaban a URLs de Chile `/cl/es/...`.
- Navegación rota: el usuario en Uruguay era redirigido a rutas de Chile.
- `NoReverseMatch: 'desarme' is not a registered namespace inside 'chile'` al intentar acceder a desarme desde Uruguay.

## Solución aplicada

Se añadió soporte explícito para Uruguay en `country_url.py`:

1. **`_country_ns_from_path()`**: detecta `/uy/es/` y `/uy/` y devuelve `uruguay_es` o `uruguay`.
2. **`_extract_lang_from_path()`**: extrae `es` para rutas `/uy/es/`.
3. **Lógica principal de `country_url`**: trata `uruguay` y `uruguay_es` igual que `chile`, con `desarme:*` como `{country_ns}:taller:desarme:*`.

## Comportamiento después del fix

Para `/uy/documentos/ver/3/`:

- `country_ns = uruguay`
- `country_url('documentos:lista_documentos')` → `/uy/documentos/`
- `country_url('documentos:documento_editar', 3)` → `/uy/documentos/form/3/`
- `country_url('documentos:descargar_pdf', 3)` → `/uy/documentos/3/pdf/`
- `country_url('documentos:crear_seguimiento_publico', 3)` → `/uy/documentos/3/crear-seguimiento/`
- `country_url('desarme:index')` → `/uy/desarme/`

## Cómo reproducir el error (antes del fix)

En el shell de Django:

```bash
cd /srv/egarage
python manage.py shell -c '
from django.test import RequestFactory
from taller.templatetags.country_url import country_url, _country_ns_from_path

rf = RequestFactory()
req = rf.get("/uy/documentos/ver/3/")

print("country_ns =", _country_ns_from_path(req.path))
print(country_url({"request": req}, "documentos:lista_documentos"))
'
```

**Antes del fix:** `country_ns = chile` y la URL era `/cl/es/documentos/`.  
**Después del fix:** `country_ns = uruguay` y la URL es `/uy/documentos/`.

## Validación en producción

1. Reiniciar Gunicorn: `sudo systemctl restart gunicorn`
2. Iniciar sesión en Uruguay.
3. Ir a `/uy/documentos/ver/<id>/`.
4. Comprobar que todos los enlaces (lista, editar, PDF, seguimiento, desarme) apunten a `/uy/...` y no a `/cl/...`.

## Notas

- Los `DisallowedHost` en logs (159.223.200.106, 0.0.0.0, etc.) son escaneos externos y no están relacionados con este problema.
- El 302 a `/accounts/login/?next=/uy/documentos/ver/3/` es redirección normal cuando la ruta exige autenticación.
