# Auditoría de seguridad del login (eGarage)

Sistema multi-tenant detrás de **Cloudflare → Nginx → Gunicorn → Django → django-allauth**. Estas tres configuraciones suelen faltar o estar mal afinadas y exponen a ataques cuando escalas a muchos talleres (100–500+).

---

## 1. ALLOWED_HOSTS (sin wildcard en producción)

**Riesgo:** Con `ALLOWED_HOSTS = ["*"]` o leyendo de env sin validar, un atacante puede enviar peticiones con `Host: evil.com` y que Django las acepte, facilitando cache poisoning y redirecciones maliciosas.

**Estado en eGarage:**

| Entorno | Ubicación | Estado |
|--------|-----------|--------|
| Producción | `gestion_taller/settings/prod.py` | ✅ Lista explícita: `egarage.cl`, `www.egarage.cl` (y env) |
| Compacto | `gestion_taller/compacto/settings.py` | ⚠️ `env_list("DJANGO_ALLOWED_HOSTS", "*")` — en prod no usar `*` |

**Recomendación:** En producción asegurar siempre:

```bash
DJANGO_ALLOWED_HOSTS=egarage.cl,www.egarage.cl
```

Y en código, no usar `"*"` como valor por defecto cuando `DEBUG=False`.

---

## 2. Cookies de sesión: HttpOnly y SameSite

**Riesgo:** Si la cookie de sesión no es `HttpOnly`, JavaScript puede leerla (XSS) y robar la sesión. Si no tiene `SameSite`, aumenta el riesgo de CSRF desde otros sitios.

**Estado en eGarage:**

| Setting | prod.py | compacto/settings.py |
|--------|---------|----------------------|
| `SESSION_COOKIE_SECURE` | ✅ True | ✅ Por env (not DEBUG) |
| `SESSION_COOKIE_HTTPONLY` | ✅ True | ❌ No definido (Django por defecto = True) |
| `SESSION_COOKIE_SAMESITE` | ✅ `"Lax"` | ❌ No definido |

**Recomendación:** En el módulo de settings que use producción, definir explícitamente:

```python
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
```

Así no dependes del valor por defecto de Django y queda documentado.

---

## 3. Rate limit de login (allauth) y cache

**Riesgo:** Sin rate limit efectivo en login, un atacante puede hacer fuerza bruta sobre contraseñas. Allauth ya aplica rate limit por defecto, pero depende de la IP del cliente; si la IP se obtiene mal o se puede falsear, el límite se puede eludir.

**Estado en eGarage:**

- **IP del cliente:** Resuelta con `CountryAwareAccountAdapter.get_client_ip()` usando `X-Forwarded-For` / `X-Real-IP` / `REMOTE_ADDR`.
- **ACCOUNT_RATE_LIMITS:** Solo se define `confirm_email`. Los límites por defecto de allauth para login son:
  - `login`: `"30/m/ip"`
  - `login_failed`: `"10/m/ip,5/5m/key"` (bloqueo tras demasiados fallos).

**Recomendación:**

1. Hacer explícito el rate limit de login en producción para poder afinarlo y documentarlo:

```python
# En settings de producción
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "1/m",
    "login": "20/m/ip",           # más estricto que el default 30/m si lo deseas
    "login_failed": "5/m/ip,3/5m/key",
}
```

2. **Cache:** El rate limit de allauth usa la cache de Django. En producción no usar `DummyCache`; usar Redis, Memcached o al menos `LocMemCache` para que el límite sea efectivo entre workers y peticiones.

3. **Admin:** El rate limit de allauth no protege el login de `/admin/`. Si el admin está expuesto, valorar protección adicional (IP, 2FA, o proxy que limite intentos).

---

## 4. (Opcional) Endurecer la IP detrás de Cloudflare

**Riesgo:** Si Nginx reenvía `X-Forwarded-For` tal cual desde el cliente, un atacante puede enviar `X-Forwarded-For: 1.2.3.4` y falsear la IP; el rate limit se aplicaría a esa IP, no a la real.

**Mitigación:** Cuando el tráfico pasa por Cloudflare, es preferible usar la IP que Cloudflare considera “cliente real”:

- Cloudflare envía **`CF-Connecting-IP`** con la IP del cliente.
- Nginx debe reenviar ese header al backend (por ejemplo `proxy_set_header CF-Connecting-IP $http_cf_connecting_ip;`).
- En el adapter, priorizar `HTTP_CF_CONNECTING_IP` cuando exista, y solo si no, usar `X-Forwarded-For` / `X-Real-IP` / `REMOTE_ADDR`.

Así la IP usada para rate limit y logs es la que fija Cloudflare y no se puede falsear desde el cliente.

---

## Resumen de acciones

| # | Configuración | Acción |
|---|----------------|--------|
| 1 | ALLOWED_HOSTS | En prod no usar `*`; usar lista explícita vía env. |
| 2 | Session cookie | Definir en prod `SESSION_COOKIE_HTTPONLY = True` y `SESSION_COOKIE_SAMESITE = "Lax"`. |
| 3 | Rate limit login | Hacer explícito `ACCOUNT_RATE_LIMITS` para `login` y `login_failed`; usar cache real (no DummyCache). |
| 4 | IP detrás Cloudflare | Opcional: preferir `CF-Connecting-IP` en el adapter cuando esté presente. |

Con esto el login queda alineado con buenas prácticas para un SaaS multi-tenant en Cloudflare + Django + Allauth.

---

## 5. 403 CSRF en `/us/login/` (login USA)

**Síntoma:** Al hacer POST en `https://egarage.cl/us/login/` aparece "CSRF verification failed. Request aborted."

**Causas habituales:**

1. **Página de login cacheada** (Cloudflare o navegador): se sirve una versión antigua con token CSRF ya no válido.
2. **Cookie CSRF no compartida** entre `egarage.cl` y `www.egarage.cl`: si el usuario entra por una y el POST va a la otra, la cookie no se envía.

**Cambios aplicados:**

- **Vista USA** (`taller/urls_extra/usa.py`): se envían cabeceras `Cache-Control: no-store, no-cache`, `Pragma: no-cache`, `Expires: 0` en las respuestas GET y en el render de error de login, para que la página de login no se cachee y el token CSRF sea siempre actual.
- **Producción** (`gestion_taller/settings/prod.py`): se puede definir `DJANGO_CSRF_COOKIE_DOMAIN=.egarage.cl` en el `.env` para que la cookie CSRF sea válida en `egarage.cl` y `www.egarage.cl`. Opcional; descomentar en `.env.prod` si sigue habiendo 403 al alternar www/no-www.

**Para diagnosticar el motivo exacto:** activar temporalmente en settings de producción:

```python
CSRF_FAILURE_VIEW = "taller.views_extra.csrf_debug.csrf_failure"
```

Repetir el POST y revisar los logs: la vista registra `reason`, `referer` y `origin`.

---

## 6. Redirección post-login USA → Chile (prioridad país)

**Síntoma:** Suscriptores USA que entran por `https://egarage.cl/us/login/` terminan en `/cl/es/dashboard/` en vez de `/us/dashboard/`.

**Causa:** Resolución de país con prioridad equivocada y fallbacks duros a Chile (URL no prioritaria, sesión no usada en `/accounts/login/`, excepciones siempre a CL).

**Regla correcta:** Si el usuario entra por `/us/...`, el sistema debe mantener US en todo el flujo. Prioridad: **(1) URL actual** → **(2) sesión** → **(3) empresa/perfil** → **(4) request.country** → **(5) GET** → **(6) fallback CL**.

### Cambios aplicados

| Archivo | Cambio |
|--------|--------|
| **taller/views_extra/account_adapter.py** | Orden de resolución: path primero (`/us/` → US), luego sesión, luego empresa/perfil. En el `except` final no caer siempre en Chile: si path empieza por `/us/` o sesión es us/usa, devolver `/us/dashboard/`. |
| **taller/middleware/force_accounts_to_cl.py** | `_country_from_login_request`: antes del default `"cl"`, considerar `request.session.get("country")`; si es `"us"` o `"usa"`, devolver `"us"` para enviar a `/us/.../accounts/login/`. |

### Checklist de revisión (otros archivos)

- **taller/middleware/login_country_fix.py**: Solo reescribe Location a `/accounts/login/` y `/cl/accounts/login/`; no toca redirects a `/us/dashboard/`. OK.
- **taller/views_extra/login_redirector.py**: Redirige *hacia* la página de login (chile/usa) según path y sesión; no es el post-login. Fallback a Chile solo cuando path no es /us/ ni /cl/ y sesión no indica USA.
- **taller/views/country_aware_auth.py**: Detecta país por path primero; `get_template_names()` elige template por país. No modifica el redirect post-login (lo hace el adapter).

### Fase 2 (pendiente): hardcodes Chile en dashboard/templates

Rutas tipo `/cl/en/vehiculos/crear/`, `/cl/taller/documentos/crear/`, `/cl/taller/reportes/` en templates deben sustituirse por helpers `country_url` / `reverse` por país actual, nunca fijas a `/cl/...`.
