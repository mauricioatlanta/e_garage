# Sistema de rutas y URLs – eGarage (multi-país)

Documento técnico para desarrolladores. Describe la arquitectura de URLs, namespaces y redirecciones de eGarage para reducir tiempo de debugging en login, redirects y enlaces incorrectos.

---

## 1. Resumen ejecutivo

- **Prefijos de país:** `/cl/` (Chile), `/us/` (USA), `/ar/`, `/uy/`, etc.
- **Prefijos de idioma (solo USA):** `/us/en/`, `/us/es/`.
- **Namespaces Django:** Cada combinación país (y en USA, país+idioma) tiene su propio namespace. El tag `country_url` resuelve URLs según la ruta actual.
- **Punto de fallo frecuente:** En USA con idioma (`/us/en/`, `/us/es/`) muchas vistas están bajo el namespace `taller`, no en la raíz del país. Ej.: `company_settings` es `us_en:taller:company_settings`, no `us_en:company_settings`.

---

## 2. Mapa de prefijos y namespaces

| Prefijo ruta   | Namespace Django | Incluye (archivo)              | Ejemplo URL principal      |
|----------------|------------------|--------------------------------|-----------------------------|
| `/cl/es/`      | `chile`          | `taller.urls_extra.chile`       | `/cl/es/settings/`          |
| `/us/`         | `usa`            | `taller.urls_extra.usa`         | `/us/settings/`, `/us/login/` |
| `/us/en/`      | `us_en`          | `taller.urls`                   | `/us/en/settings/`, `/us/en/centro-operaciones/` |
| `/us/es/`      | `us_es`          | `taller.urls`                   | `/us/es/settings/`          |
| `/ar/`, `/ar/es/` | `argentina`   | `taller.urls_extra.argentina`   | —                           |
| `/pe/es/`      | `peru`           | `taller.urls_extra.peru`        | —                           |
| `/co/es/`      | `colombia`       | `taller.urls_extra.colombia`    | —                           |
| Otros          | `peru`, `colombia`, etc. | `taller.urls_extra.<país>` | —                           |

**Importante:** En `gestion_taller/urls.py` el orden de los `path()` importa. Las rutas más específicas (p. ej. `us/en/`, `us/es/`) deben declararse **antes** que la ruta genérica `us/`, para que Django las empareje correctamente.

---

## 3. Inconsistencia USA: raíz vs. idioma

- **`/us/` (namespace `usa`):** Definido en `taller/urls_extra/usa.py`. Aquí rutas como `settings/`, `login/`, `clientes/`, etc. están **en la raíz** del namespace → nombres `usa:company_settings`, `usa:account_login`, etc.
- **`/us/en/` y `/us/es/` (namespaces `us_en`, `us_es`):** Definidos en `gestion_taller/urls.py` como `include(("taller.urls", "taller"))`. Todas las rutas vienen de `taller/urls.py`, donde la app se llama `taller` → nombres `us_en:taller:company_settings`, `us_es:taller:centro_operaciones`, etc.

Por tanto:

- Para **Chile** y **USA raíz**: `country_url` con `app_namespace='direct'` suele bastar: `chile:company_settings`, `usa:company_settings`.
- Para **USA con idioma**: hace falta el sub-namespace `taller`: `us_en:taller:company_settings`, `us_es:taller:company_settings`.

El tag `country_url` ya contempla un fallback para `company_settings` cuando falla el nombre directo (ver sección 6).

---

## 4. Archivos clave de configuración de URLs

| Archivo | Rol |
|---------|-----|
| `gestion_taller/urls.py` | URLconf raíz. Define prefijos `/cl/`, `/us/`, `/us/en/`, `/us/es/`, redirects de compatibilidad, allauth, login global. |
| `taller/urls.py` | Rutas del “taller” (settings, centro-operaciones, clientes, documentos, etc.) bajo un namespace `taller`. Se incluye bajo `us/en/` y `us/es/`. |
| `taller/urls_extra/chile.py` | Rutas para Chile: `cl/es/` → namespace `chile`. Incluye `settings/`, `centro-operaciones/`, allauth, etc. |
| `taller/urls_extra/usa.py` | Rutas para USA sin idioma: `us/` → namespace `usa`. Incluye `settings/`, `login/`, `clientes/`, documentos, etc. |
| `taller/templatetags/country_url.py` | Tag `country_url` que, a partir de `request.path`, elige namespace y construye el nombre de URL para `reverse()`. |

---

## 5. Redirecciones importantes (orden aproximado en urlpatterns)

- **Login:**  
  - `/accounts/login/` → manejado por middleware y/o vista para redirigir a `/cl/.../accounts/login/` o `/us/.../accounts/login/` según `next` o `from`.  
  - `/us/login/` y `/us/accounts/login/` están en `usa`; `/us/en/accounts/` y `/us/es/accounts/` incluyen `allauth.urls`.
- **Settings:**  
  - `/us/centro-operaciones/` → `/us/en/centro-operaciones/`  
  - `/taller/settings/` → `/cl/es/settings/`  
  - `/us/taller/settings/` → `/us/settings/`  
  - `/compat/settings/` → `/cl/es/settings/#financial`
- **País/idioma:**  
  - `/cl/` → `/cl/es/bienvenida/`  
  - `/cl/vehiculos/` → `/cl/es/vehiculos/`  
  - `/us/vehiculos/` → `/us/en/vehiculos/`
- **Documentos:**  
  - `/cl/es/documentos/` → `/cl/documentos/` (namespace `documentos_cl_es`).  
  Hay más redirects para documentos y AJAX en el mismo archivo.

Si un enlace “no lleva al template correcto”, suele deberse a que la URL generada no coincide con la ruta que realmente tiene la vista (p. ej. usar `us_en:company_settings` en lugar de `us_en:taller:company_settings`).

---

## 6. Tag `country_url` – Uso y fallback para Ajustes

**Ubicación:** `taller/templatetags/country_url.py`

**Lógica resumida:**

1. Obtiene el namespace del país desde `request.path` (`_country_ns_from_path`):
   - `/us/en/` → `us_en`
   - `/us/es/` → `us_es`
   - `/us/` → `usa`
   - `/cl/` o `/cl/es/` → `chile`
2. Construye el nombre de URL:
   - Con `app_namespace='direct'`: `{country_ns}:{view_path}` (p. ej. `chile:company_settings`).
   - Con `app_namespace='taller'` (por defecto): `{country_ns}:taller:{view_path}` (p. ej. `usa:taller:clientes:lista_clientes`).
3. Llama a `reverse(full_name, ...)`. Si falla:
   - Para nombres con sub-namespace, intenta sin `taller`: `{country_ns}:{view_path}`.
   - **Para `company_settings` con `app_namespace='direct'`:** intenta `{country_ns}:taller:company_settings` (corrige el caso USA con idioma).

**Ejemplos de uso en templates:**

```django
{% load country_url %}
{# Ajustes: puede requerir fallback en us_en/us_es #}
<a href="{% country_url 'company_settings' app_namespace='direct' %}">Ajustes</a>

{# Rutas con sub-namespace (clientes, documentos, etc.) #}
<a href="{% country_url 'clientes:lista_clientes' %}">Clientes</a>
<a href="{% country_url 'centro_operaciones' app_namespace='direct' %}">Centro</a>
```

Si se añaden nuevas vistas “directas” en `us_en`/`us_es` bajo `taller`, puede ser necesario un fallback similar al de `company_settings` en `country_url`.

---

## 7. Middlewares que afectan login y redirects

Documentación detallada en **`docs/MIDDLEWARE_Y_LOGIN_403.md`**. Resumen:

| Middleware | Efecto en rutas/login |
|------------|------------------------|
| `ForceAccountsToCLMiddleware` | Redirige **GET** a `/accounts/login/` → `/cl/accounts/login/` (o al país inferido por `next`/`from`). No debe tocar POST para no romper el login. |
| `FixLoginCountryRedirectMiddleware` | Reescribe respuestas de redirect que envían a `/accounts/login/` para que vayan a `/<cc>/accounts/login/` o `/<cc>/<lang>/accounts/login/` según el path o `next`. |
| `CountryDetectionMiddleware` | Establece `request.country` (y similar) según el path. |
| `SimpleCountryRedirectMiddleware` | Redirecciones de coherencia país/empresa (p. ej. usuario con empresa US en `/cl/` → redirigir a `/us/`). |
| `VerificarSuscripcionMiddleware` | Puede redirigir a suscripción bloqueada; las rutas de login están exentas vía `is_login_exempt_path()`. |

Problemas típicos:

- **403 en POST login:** Revisar CSRF, `action` del formulario y que la ruta de login no sea redirigida en POST (ver `MIDDLEWARE_Y_LOGIN_403.md`).
- **Redirect a país/idioma equivocado:** Revisar que `next` y el path de login tengan el prefijo correcto (`/us/en/`, `/cl/es/`, etc.) y que los middlewares no sobrescriban de forma incorrecta el `Location`.

---

## 8. Dónde está cada “Settings / Ajustes”

| Ruta | Namespace:nombre | Vista | Template |
|------|------------------|--------|----------|
| `/cl/es/settings/` | `chile:company_settings` | `company_settings_view` | `taller/settings/centro_ajustes.html` |
| `/us/settings/` | `usa:company_settings` | `company_settings_view` | `taller/settings/centro_ajustes.html` |
| `/us/en/settings/` | `us_en:taller:company_settings` | `company_settings_view` | `taller/settings/centro_ajustes.html` |
| `/us/es/settings/` | `us_es:taller:company_settings` | `company_settings_view` | `taller/settings/centro_ajustes.html` |

Todas usan la misma vista y el mismo template; solo cambia el nombre de la URL según el namespace.

---

## 9. Recomendaciones para evitar bugs

1. **Enlaces en templates:** Preferir `{% country_url 'nombre' %}` o `{% country_url 'nombre' app_namespace='direct' %}` en lugar de URLs fijas, para que funcionen en todos los países/idiomas.
2. **Nuevas vistas “directas” en USA con idioma:** Si se registran en `taller.urls` (bajo `us_en`/`us_es`), el nombre será `us_en:taller:nombre`. Si en el template se usa `country_url` con `app_namespace='direct'`, puede ser necesario un fallback en `country_url.py` como el de `company_settings`.
3. **Tests:** Incluir pruebas que resuelvan las URLs de Ajustes (y otras críticas) para los namespaces `chile`, `usa`, `us_en` y `us_es`.
4. **Estandarizar namespaces (futuro):** Unificar si las vistas “globales” del taller viven siempre en `{country_ns}:taller:...` o siempre en `{country_ns}:...` para no depender de fallbacks ad hoc en el tag.

---

## 10. Referencias rápidas

- **Corrección del botón Ajustes:** Ver informe “Corrección de enlaces a Ajustes / Settings” (fallback en `country_url` para `company_settings`).
- **Login 403 y middlewares:** `docs/MIDDLEWARE_Y_LOGIN_403.md`.
- **URLconf raíz:** `gestion_taller/urls.py`.
- **Tag de URLs por país:** `taller/templatetags/country_url.py`.
