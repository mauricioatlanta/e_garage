# Auth – Arquitectura canónica (versión final aprobada)

Documento de referencia para la implementación de auth en eGarage. Decisiones cerradas; este documento es la base para aplicar cambios archivo por archivo sin re-discutir el diseño.

---

## 1. Principios de diseño

| Principio | Regla |
|-----------|--------|
| **No depender del orden de rutas** | Nada de "mi path gana porque está antes". Redirects explícitos, no colisiones con allauth. |
| **allauth solo auxiliar** | logout, password reset, email confirm, etc. No es entrada principal de login/signup. |
| **Tres capas** | Canónica (única fuente) → Legacy (redirects) → Auxiliares (allauth) |
| **Una implementación por flujo** | Sin `account_login_alt`, sin `TemplateView` de login, sin mezcla. |
| **POST siempre a canónica** | GET y POST entran a la misma vista; no "form renderiza aquí, postea allá". |

---

## 2. Política canónica (definitiva)

### Login

| País | Ruta canónica | Vista |
|------|---------------|-------|
| Chile | `/cl/es/accounts/login/` | `country_aware_login` |
| USA | `/us/login/` | `usa_login_view` |
| Global (fallback) | `/accounts/login/` | `country_aware_login` |

### Signup

| País | Ruta canónica | Vista |
|------|---------------|-------|
| Chile | `/accounts/signup/?from=cl` | `CustomSignupView` |
| USA | `/us/signup/` | `usa_signup_view` |
| Global (fallback) | `/accounts/signup/` | `CustomSignupView` |

### Auxiliares (allauth global)

- `/accounts/logout/`
- `/accounts/password/reset/`
- `/accounts/password/change/`
- `/accounts/confirm-email/`
- etc.

---

## 3. Rutas legacy → redirects explícitos (302)

**Importante:** Las rutas legacy existen solo para compatibilidad y redirección. Los formularios deben apuntar siempre a la ruta canónica (action del form, enlaces internos). Nunca usar rutas legacy como endpoint real de POST.

### Chile

| Legacy | Redirect a |
|--------|------------|
| `/cl/login/` | `/cl/es/accounts/login/` |
| `/cl/es/login/` | `/cl/es/accounts/login/` |
| `/cl/accounts/login/` | `/cl/es/accounts/login/` |

### USA

| Legacy | Redirect a |
|--------|------------|
| `/us/accounts/login/` | `/us/login/` |
| `/us/en/accounts/login/` | `/us/login/` |
| `/us/es/accounts/login/` | `/us/login/` |
| `/us/accounts/signup/` | `/us/signup/` |
| `/us/en/accounts/signup/` | `/us/signup/` |
| `/us/es/accounts/signup/` | `/us/signup/` |

---

## 4. Decisiones de arquitectura (cerradas)

### A. Logout y password reset

**Decisión cerrada:** Rutas globales reales + redirects desde país.

- Canónicas: `/accounts/logout/`, `/accounts/password/reset/`, `/accounts/password/change/`
- `/us/accounts/logout/` → redirect 302 → `/accounts/logout/`
- `/cl/es/accounts/password/reset/` → redirect 302 → `/accounts/password/reset/`
- etc.

**Ventaja:** Un solo ecosistema auth auxiliar; no mini-ecosistemas por país.

---

### B. Signup a largo plazo

**Opción A — Centralizado global**

- Todos los países usan `/accounts/signup/?from=xx`
- Una sola implementación real (`CustomSignupView`)
- Chile y USA: signup es redirect a global.

**Opción B — Canónico por país**

- Chile: redirect a global con `?from=cl`
- USA: `/us/signup/` como canónica propia (`usa_signup_view`)
- Permite UX y flujos distintos por país.

**Decisión cerrada:** Opción B. USA mantiene `/us/signup/` como canónica propia; Chile usa redirect a global con `?from=cl`. Coherente con la identidad diferenciada de USA (idioma, contexto comercial, onboarding).

---

## 5. Cambios por archivo (checklist ejecutable)

### `gestion_taller/urls.py`

- [ ] Mantener `accounts/login/` y `accounts/signup/` globales (canónicas)
- [ ] Mantener `path("accounts/", include("allauth.urls"))` para auxiliares
- [ ] **Eliminar** `path("us/en/accounts/", include("allauth.urls"))` y `path("us/es/accounts/", include("allauth.urls"))`
- [ ] Agregar redirects Chile: `cl/login/`, `cl/es/login/`, `cl/accounts/login/` → `/cl/es/accounts/login/`
- [ ] Agregar redirects USA: `us/accounts/login/`, `us/en/accounts/login/`, `us/es/accounts/login/` → `/us/login/`
- [ ] Agregar redirects USA signup (si aplica): `us/accounts/signup/`, etc. → `/us/signup/`
- [ ] Agregar redirects auxiliares USA: `us/accounts/logout/`, `us/accounts/password/...` → rutas globales

### `taller/urls_extra/chile.py`

- [ ] **Eliminar** `path("login/", TemplateView.as_view(...), name="account_login")`
- [ ] Definir `path("accounts/login/", country_aware_login, name="account_login")` (importar desde `country_aware_auth`)
- [ ] Mantener signup redirect a `/accounts/signup/?from=cl`
- [ ] Redirects auxiliares Chile a rutas globales (logout, password reset, etc.)

### `taller/urls_extra/usa.py`

- [ ] Mantener `path("login/", usa_login_view, name="account_login")`
- [ ] Mantener `path("signup/", usa_signup_view, name="account_signup")`
- [ ] **Eliminar** `path("accounts/login/", usa_login_view, name="account_login_alt")`

### Templates

- [ ] **Regla:** Nunca usar `{% url 'account_login' %}` ni `{% url 'account_signup' %}` sin namespace.
- [ ] **Templates específicos de país** → namespace explícito: `{% url 'usa:account_login' %}`, `{% url 'chile:account_login' %}`
- [ ] **Templates compartidos multi-país** → `{% country_url 'account_login' %}`
- [ ] Archivos a corregir: `account/password_change_done.html`, `taller/registro_exitoso.html`, `account/_login_form.html`, etc.

---

## 6. Tests mínimos (antes de cerrar)

| # | Caso | Esperado |
|---|------|----------|
| 1 | GET `/cl/es/accounts/login/` | 200 |
| 2 | POST `/cl/es/accounts/login/` (credenciales válidas) | 302, autentica y redirige |
| 3 | GET `/cl/login/` | 302, Location exacta: `/cl/es/accounts/login/` |
| 4 | GET `/cl/accounts/login/` | 302, Location: `/cl/es/accounts/login/` |
| 5 | GET `/us/login/` | 200 |
| 6 | POST `/us/login/` (credenciales válidas) | 302, autentica y redirige |
| 7 | GET `/us/accounts/login/` | 302, Location exacta: `/us/login/` |
| 8 | GET `/us/en/accounts/login/` | 302, Location exacta: `/us/login/` |
| 9 | GET `/us/es/accounts/login/` | 302, Location exacta: `/us/login/` |

**Importante:** Los tests de redirect deben verificar la URL destino exacta (no solo que sea 302). Eso protege la política canónica.

---

## 7. Anti-patrones prohibidos (documentar para futuro)

- ❌ `TemplateView` para login (renderiza pero no procesa POST)
- ❌ Alias tipo `account_login_alt` sin eliminar el original
- ❌ Include de allauth que exponga login/signup en rutas país sin control
- ❌ Form que renderiza en ruta A y postea a ruta B distinta
- ❌ `{% url 'account_login' %}` o `{% url 'account_signup' %}` a secas en templates multi-país

---

## 8. Resumen ejecutivo

**Canónicas:**

- Chile login: `/cl/es/accounts/login/`
- USA login: `/us/login/`
- Signup: USA canónico `/us/signup/`; Chile redirect a global con `?from=cl` (Opción B)
- Auxiliares: allauth global; país → redirect

**Capas:**

1. Canónica = única fuente de verdad (GET + POST)
2. Legacy = solo redirects 302 a canónica
3. Auxiliares = allauth global; rutas país redirigen

**Próximo paso:** Ejecutar checklist archivo por archivo (decisiones A y B ya cerradas).

**Orden de implementación recomendado:**

1. `gestion_taller/urls.py` — redirects y eliminación de includes conflictivos
2. `taller/urls_extra/usa.py` — eliminar `account_login_alt`, dejar solo canónicas
3. `taller/urls_extra/chile.py` — eliminar TemplateView, definir canónica
4. Templates — corregir URLs sin namespace
5. Tests — redirects exactos y POST canónico

*El checklist de la sección 5 puede usarse como tablero de avance: ir marcando ítems conforme se implementen.*
