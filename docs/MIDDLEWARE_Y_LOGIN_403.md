# MIDDLEWARE y diagnóstico 403 en POST login

## Estado actual

| Área | Estado |
|------|--------|
| Error BD por `sales_tax_rate` faltante | Resuelto |
| Grafo de migraciones | Destrabado |
| Redirect country-aware al login | Funcionando |
| Nginx como causa del 403 | Descartado |
| **403 en POST `/cl/es/accounts/login/`** | **Pendiente** |

Hipótesis principal y mejor sustentada: **CSRF**. Los middlewares de tenant/empresa/suscripción no explican ese 403 en login no autenticado.

---

## Recomendación operativa (orden de ejecución)

1. **Paso 1 — Instrumentar CSRF_FAILURE_VIEW temporalmente y repetir el POST.**  
   Es lo que falta para salir de la duda y obtener el motivo exacto (token, referer, origin, etc.).  
   → Ver sección *Confirmar el motivo exacto del 403* más abajo.

2. **Paso 2 — Aplicar el helper `is_login_exempt_path()` en empresa_middleware, verificar_suscripcion y tenant_isolation (si se vuelve a activar).**  
   ✅ **Hecho:** los tres middlewares ya usan `taller.utils.login_exempt.is_login_exempt_path()`.

3. **Paso 3 — Cambiar el template del login a `action="{{ request.get_full_path }}"`.**  
   ✅ **Hecho:** templates de login actualizados.

4. **Paso 4 — Una vez identificado el motivo exacto del CSRF, retirar la vista de debug temporal** (quitar o comentar `CSRF_FAILURE_VIEW`).

---

## 0. ERR_TOO_MANY_REDIRECTS en /accounts/login/ (egarage.cl)

**Causa:** `ForceAccountsToCLMiddleware` redirigía GET `/accounts/login/` → `/cl/accounts/login/`, pero en la app `/cl/accounts/login/` está definido como `redirect_qs("/accounts/login/")`, que redirige de vuelta a `/accounts/login/` → bucle.

**Solución:** El middleware ahora redirige a la ruta que **sirve** el login: `/<cc>/<lang>/accounts/login/` (p. ej. `/cl/es/accounts/login/` para Chile), usando idioma por defecto por país (`_DEFAULT_LANG_BY_CC`). Esa ruta la sirve allauth bajo `cl/es/` y no redirige de vuelta.

---

## 1. Listado MIDDLEWARE (producción: `gestion_taller.settings.base` → `settings.prod`)

Orden de ejecución (request → response):

```
1.  django.middleware.security.SecurityMiddleware
2.  django.contrib.sessions.middleware.SessionMiddleware
3.  taller.middleware.force_accounts_to_cl.ForceAccountsToCLMiddleware  (GET /accounts/login/ → /cc/lang/accounts/login/)
4.  django.middleware.common.CommonMiddleware
5.  django.middleware.locale.LocaleMiddleware
6.  django.middleware.csrf.CsrfViewMiddleware          ← devuelve 403 si falla CSRF
7.  django.contrib.auth.middleware.AuthenticationMiddleware
8.  [allauth.account.middleware.AccountMiddleware]     (insertado dinámicamente)
9.  taller.middleware.login_country_fix.FixLoginCountryRedirectMiddleware
10. django.contrib.messages.middleware.MessageMiddleware
11. django.middleware.clickjacking.XFrameOptionsMiddleware
12. taller.middleware.country_detection.CountryDetectionMiddleware
13. taller.middleware.empresa_middleware.EmpresaMiddleware
14. taller.middleware.simple_country_redirect.SimpleCountryRedirectMiddleware
15. taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware
```

Si en el servidor usas **`gestion_taller.settings`** (raíz) en lugar de base, el orden puede incluir además:

- `taller.middleware.fix_allowed_hosts.FixAllowedHostsMiddleware`
- `taller.middleware.rate_limiting.RateLimitMiddleware` (devuelve **429**, no 403)

**Importante:** `TenantIsolationMiddleware` (tenant_isolation.py) **no está** en ninguna lista de MIDDLEWARE; no se ejecuta en producción.

---

## 2. tenant_isolation.py

- **¿Activo?** No (no está en MIDDLEWARE).
- **PermissionDenied:** importado pero no usado en el código actual.
- **Lógica:** Solo asigna `request.empresa` y en algunos casos redirige a `suspension`; no devuelve 403.
- **Exclusiones:** `is_public_url()` incluye `/accounts/login/`, `/account/login/`, `/us/login/`, `/cl/login/` pero **no** `/cl/es/accounts/login/` ni `/us/en/accounts/login/` (porque hace `path.startswith(url)`). Si se activara este middleware, POST a `/cl/es/accounts/login/` no se considerarían “públicas” con la lista actual.

---

## 3. empresa_middleware.py

- **¿Activo?** Sí.
- **Lógica:** Pone `request.empresa` desde `request.user.empresa`. Si `empresa.debe_bloquear` y la ruta no está exenta → `redirect("suspension")`, no 403.
- **Exención:** Usa `_strip_country_locale_prefix(path)`, así que `/cl/es/accounts/login/` → norm = `/accounts/login/` y coincide con `/accounts/login/` en exempt_bases. **Sí exenta** login con prefijo país.
- **Conclusión:** No es la causa de un 403 en POST login.

---

## 4. verificar_suscripcion.py

- **¿Activo?** Sí.
- **Lógica:** Solo entra si `request.user.is_authenticated`. En el POST de login el usuario aún no está autenticado, así que hace `return self.get_response(request)` y no bloquea.
- **EXEMPT_URLS:** Tiene `/accounts/login/`, `/cl/login/`, `/us/accounts/login/` pero **no** `/cl/es/accounts/login/`. Aun así, al no aplicar a usuarios no autenticados, no explica el 403 en login.
- **Conclusión:** No es la causa del 403 en POST login.

---

## 5. simple_country_redirect.py

- Solo actúa en `GET`/`HEAD` y con usuario autenticado. Para POST de login no hace nada. No devuelve 403.

---

## 6. rate_limiting.py

- Documentado: “NUNCA devuelve 403”; en exceso de límite devuelve **429** y `errors/rate_limit.html`. No es la causa de un 403.

---

## Causa más probable del 403 en POST login

**CsrfViewMiddleware:** si el POST a `/cl/es/accounts/login/` llega sin token CSRF correcto (o con Referer/Origin que no coinciden), Django responde **403 Forbidden**. Es lo más habitual cuando GET del login carga bien y el POST a la misma URL da 403.

Comprobar en el servidor:

- Que el formulario de login incluya `{% csrf_token %}`.
- Que no haya proxy/redirect que quite o cambie `Referer`/`Origin` y rompa la comprobación CSRF.
- Que `CSRF_TRUSTED_ORIGINS` incluya `https://egarage.cl` y `https://www.egarage.cl`.

---

## Recomendación: exentar explícitamente login con prefijo país

Para que ningún middleware futuro ni lógica que use solo `path.startswith("/accounts/login/")` afecte el login con prefijo:

- En **empresa_middleware** y **verificar_suscripcion** (y en tenant_isolation si algún día se activa) conviene tener también:
  - `/cl/es/accounts/login/`
  - `/cl/accounts/login/`
  - `/us/en/accounts/login/`
  - `/us/accounts/login/`
  (o un helper que normalice path y trate “login” como exento por prefijo país/idioma).

Así te cubres ante cambios futuros y evitas que un middleware de tenant/empresa intercepte el POST del login.

---

## Confirmar el motivo exacto del 403 (CSRF_FAILURE_VIEW)

Para salir de la zona gris en una sola prueba, activa temporalmente una vista custom de fallo CSRF que loguee la razón exacta:

1. Vista: `taller.views_extra.csrf_debug.csrf_failure` (loguea method, path, reason, referer, origin).
2. En producción (settings o .env), temporalmente:
   ```python
   CSRF_FAILURE_VIEW = "taller.views_extra.csrf_debug.csrf_failure"
   ```
3. Repite el POST a `/cl/es/accounts/login/` y revisa logs (journald o archivo). Verás si es token incorrecto, cookie ausente, origin/referer, u otra causa.

## Helper común de login exento

- Módulo: `taller.utils.login_exempt` — `strip_country_locale_prefix(path)` y `is_login_exempt_path(path)`.
- Los middlewares **empresa_middleware**, **verificar_suscripcion** y **tenant_isolation** usan `is_login_exempt_path()` para exentar cualquier ruta de login (con o sin prefijo /cc/lang/), sin mantener listas sueltas.

## Form login con action explícito

En los templates de login el form usa `action="{{ request.get_full_path }}"` para que el POST vaya siempre a la URL actual y se eviten comportamientos raros con reescrituras.
