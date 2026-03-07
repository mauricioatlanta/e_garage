# Fix: Loop de redirección /us/en/workspace → ERR_TOO_MANY_REDIRECTS

## Causa exacta del loop

**Origen:** Conflicto entre dos redirecciones en direcciones opuestas:

1. **`gestion_taller/urls.py`** (líneas 421-429, antes del fix):  
   `/us/en/workspace/` → 302 → `/us/workspace/`  
   (perdía el segmento de idioma)

2. **`taller/middleware/simple_country_redirect.py`** (`SimpleCountryRedirectMiddleware`):  
   Para un usuario autenticado en USA, si la URL no tiene idioma (`/us/workspace/`), añade el idioma por defecto:  
   `/us/workspace/` → 302 → `/us/en/workspace/`

**Efecto:** `/us/workspace/` ↔ `/us/en/workspace/` → bucle infinito → `ERR_TOO_MANY_REDIRECTS`.

## Archivo y funciones responsables

| Archivo | Función / Lógica |
|---------|------------------|
| `gestion_taller/urls.py` | Redirects de `us/en/workspace/` y `us/es/workspace/` → `/us/workspace/` |
| `taller/middleware/simple_country_redirect.py` | `process_request`: añade idioma por defecto cuando falta en el path |
| `taller/auth/decorators.py` | `country_login_required`: redirección a login sin conservar idioma en login y `next` |
| `taller/urls.py` | Falta de `workspace` en `taller.urls`, solo existía en usa/chile |

## Patch aplicado

### 1. Canonical URL de workspace

- **Antes:** `/us/en/workspace/` y `/us/es/workspace/` redirigían a `/us/workspace/`.
- **Después:** `/us/workspace/` redirige a `/us/en/workspace/` (canónica).
- **Servicio de workspace:** Añadido `path("workspace/", centro_trabajo)` en `taller/urls.py` para que `/us/en/workspace/` y `/us/es/workspace/` sirvan la vista directamente.

### 2. Login y `next` con idioma

- **`taller/auth/decorators.py`:** Uso de `prefix_from_path` para rutas con prefijo país+idioma (`/us/en/`, `/cl/es/`).  
  Si el path tiene prefijo con idioma → `login_url = /{prefix}/accounts/login/` y `next` se mantiene con el mismo prefijo.

### 3. Post-login redirect

- **`taller/views_extra/account_adapter.py`:** Redirect post-login para USA → `/us/en/workspace/`.
- **`taller/urls_extra/usa.py`:** `success_url` de login USA → `reverse("us_en:centro_trabajo")` = `/us/en/workspace/`.

### 4. Cambios en `gestion_taller/urls.py`

- `/us/workspace/` → 302 → `/us/en/workspace/`
- `/us/workspace/buscar/` → 302 → `/us/en/workspace/buscar/`

## Rutas finales esperadas

| Ruta | Resultado |
|------|-----------|
| `/us/en/workspace/` | Sirve `centro_trabajo` directamente |
| `/us/es/workspace/` | Sirve `centro_trabajo` directamente |
| `/us/workspace/` | 302 → `/us/en/workspace/` |
| `/us/en/accounts/login/` | Allauth login (formulario) |
| `next` al requerir login desde `/us/en/workspace/` | `/us/en/workspace/` |
| Post-login redirect (sin `next`) | `/us/en/workspace/` |

## Flujo completo post-fix

1. Usuario visita `/us/en/workspace/` → vista `centro_trabajo`.
2. Si no está autenticado: redirect a `/us/en/accounts/login/?next=/us/en/workspace/`.
3. Tras login: redirect a `next=/us/en/workspace/` o a `/us/en/workspace/` si no hay `next`.
4. Usuario visita `/us/workspace/` → redirect a `/us/en/workspace/` → vista `centro_trabajo`.
5. `SimpleCountryRedirectMiddleware`: `/us/en/workspace/` ya tiene idioma → no redirige.  
   No hay bucle.
