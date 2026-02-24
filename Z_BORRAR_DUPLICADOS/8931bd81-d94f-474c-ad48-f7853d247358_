# 🧪 Testing: Country Context Middleware

## 📋 Checklist de Casos de Prueba

### ✅ 1. Whitelist (No Tocar Rutas Estáticas)

```python
# Test: Rutas en whitelist NO deben ser redirigidas
test_paths = [
    "/static/css/style.css",
    "/media/uploads/image.jpg",
    "/admin/login/",
    "/favicon.ico",
    "/robots.txt",
    "/healthz",
    "/webhooks/stripe/",
]

for path in test_paths:
    request = RequestFactory().get(path)
    middleware = CountryContextMiddleware(get_response=lambda r: r)
    response = middleware.process_request(request)

    assert response is None  # No debe redirigir
    assert request.country == "CL"  # Default
    assert request._country_source == "whitelist"
```

**Resultado esperado:** ✅ Sin redirección, `country = "CL"`, `source = "whitelist"`

---

### ✅ 2. Canonicalización Legacy (/es → /cl, /en → /us)

```python
# Test: /es/* debe redirigir a /cl/* con 301
request = RequestFactory().get("/es/vehiculos/crear/")
middleware = CountryContextMiddleware(get_response=lambda r: r)
response = middleware.process_request(request)

assert response.status_code == 301  # Permanente para SEO
assert response.url == "/cl/vehiculos/crear/"

# Test: /en/* debe redirigir a /us/* con 301
request = RequestFactory().get("/en/dashboard/?foo=bar")
response = middleware.process_request(request)

assert response.status_code == 301
assert response.url == "/us/dashboard/?foo=bar"  # Preserva query string
```

**Resultado esperado:** ✅ 301 Redirect a rutas canónicas, query string preservado

---

### ✅ 3. Swap Prefix Robusto (Regex vs Slicing)

```python
# Test: _swap_prefix con diferentes formatos de ruta
from taller.middleware.country_context import CountryContextMiddleware

swap = CountryContextMiddleware._swap_prefix

# Casos normales
assert swap("/cl/vehiculos", "/cl", "/us") == "/us/vehiculos"
assert swap("/cl/", "/cl", "/us") == "/us/"
assert swap("/cl", "/cl", "/us") == "/us"

# Edge cases
assert swap("/cl/es/legacy", "/cl", "/us") == "/us/es/legacy"
assert swap("/vehiculos", "/cl", "/us") == "/us/vehiculos"  # Sin prefijo original

# Case-insensitive
assert swap("/CL/VEHICULOS", "/cl", "/us") == "/us/VEHICULOS"

# Legacy
assert swap("/es/taller", "/es", "/cl") == "/cl/taller"
assert swap("/en/dashboard", "/en", "/us") == "/us/dashboard"
```

**Resultado esperado:** ✅ Todos los casos manejan prefijos correctamente sin slicing frágil

---

### ✅ 4. Conflicto URL vs Empresa (GET → 302, POST → 307)

```python
# Setup: Usuario con empresa CL, accede a URL US
from django.contrib.auth.models import AnonymousUser
from unittest.mock import Mock

user_cl = Mock()
user_cl.is_authenticated = True
user_cl.empresa = Mock(pais="CL")

# Test GET: Redirige con 302 (temporal)
request = RequestFactory().get("/us/vehiculos/")
request.user = user_cl
middleware = CountryContextMiddleware(get_response=lambda r: r)
response = middleware.process_request(request)

assert response.status_code == 302  # Temporal
assert response.url == "/cl/vehiculos/"
assert request.country == "CL"  # Detecta país antes de redirigir

# Test POST: Redirige con 307 (mantiene método/body)
request = RequestFactory().post("/us/vehiculos/crear/", data={"marca": "Toyota"})
request.user = user_cl
response = middleware.process_request(request)

assert response.status_code == 307  # Mantiene método POST
assert response.url == "/cl/vehiculos/crear/"
```

**Resultado esperado:**
- ✅ GET → 302 (temporal)
- ✅ POST → 307 (mantiene método y body)

---

### ✅ 5. Prevención de Bucles

```python
# Test: Ya estamos en la ruta correcta, no debe redirigir
user_cl = Mock()
user_cl.is_authenticated = True
user_cl.empresa = Mock(pais="CL")

request = RequestFactory().get("/cl/vehiculos/")
request.user = user_cl
middleware = CountryContextMiddleware(get_response=lambda r: r)
response = middleware.process_request(request)

assert response is None  # NO redirige (ya está en /cl/)
assert request.country == "CL"
assert request._country_source == "url"
```

**Resultado esperado:** ✅ Sin bucles, `response = None` cuando URL y empresa coinciden

---

### ✅ 6. Jerarquía de Detección

```python
# Test 1: URL tiene prioridad sobre subdominio
request = RequestFactory().get("/us/dashboard/", HTTP_HOST="cl.myapp.com")
request.user = AnonymousUser()
middleware = CountryContextMiddleware(get_response=lambda r: r)
middleware.process_request(request)

assert request.country == "US"  # URL gana
assert request._country_source == "url"

# Test 2: Subdominio si no hay URL
request = RequestFactory().get("/dashboard/", HTTP_HOST="us.myapp.com")
request.user = AnonymousUser()
middleware.process_request(request)

assert request.country == "US"
assert request._country_source == "subdomain"

# Test 3: Empresa si no hay URL ni subdominio
user_us = Mock()
user_us.is_authenticated = True
user_us.empresa = Mock(pais="US")

request = RequestFactory().get("/dashboard/")
request.user = user_us
middleware.process_request(request)

assert request.country == "US"
assert request._country_source == "user"

# Test 4: Default si no hay nada
request = RequestFactory().get("/dashboard/")
request.user = AnonymousUser()
middleware.process_request(request)

assert request.country == "CL"  # DEFAULT_COUNTRY
assert request._country_source == "default"
```

**Resultado esperado:** ✅ Respeta jerarquía: URL > Subdomain > User > Default

---

### ✅ 7. Query String Preservado

```python
# Test: Query string se mantiene en redirecciones
request = RequestFactory().get("/es/vehiculos/?page=2&sort=asc")
middleware = CountryContextMiddleware(get_response=lambda r: r)
response = middleware.process_request(request)

assert response.status_code == 301
assert response.url == "/cl/vehiculos/?page=2&sort=asc"

# Test con conflicto de empresa
user_cl = Mock()
user_cl.is_authenticated = True
user_cl.empresa = Mock(pais="CL")

request = RequestFactory().get("/us/vehiculos/?marca=1&anio=2020")
request.user = user_cl
response = middleware.process_request(request)

assert response.url == "/cl/vehiculos/?marca=1&anio=2020"
```

**Resultado esperado:** ✅ Query string siempre preservado en redirecciones

---

### ✅ 8. Subdominio con Puerto

```python
# Test: Subdominio con puerto local
request = RequestFactory().get("/dashboard/", HTTP_HOST="us.local:8000")
request.user = AnonymousUser()
middleware = CountryContextMiddleware(get_response=lambda r: r)
middleware.process_request(request)

assert request.country == "US"
assert request._country_source == "subdomain"

# Test: Subdominio staging
request = RequestFactory().get("/dashboard/", HTTP_HOST="cl.staging.myapp.com")
middleware.process_request(request)

assert request.country == "CL"
```

**Resultado esperado:** ✅ Detecta subdominio incluso con puerto y subdominios anidados

---

### ✅ 9. Middleware de Idioma (Accept-Language Fallback)

```python
from taller.middleware.country_context import LanguageContextMiddleware

# Test 1: Usuario con idioma configurado
user = Mock()
user.is_authenticated = True
user.perfil = Mock(idioma_preferido="en")

request = RequestFactory().get("/cl/dashboard/")
request.user = user
request.country = "CL"
middleware = LanguageContextMiddleware(get_response=lambda r: r)
middleware.process_request(request)

assert request.preferred_language == "en"  # Usuario gana

# Test 2: Sin usuario, usa país
request = RequestFactory().get("/us/dashboard/")
request.user = AnonymousUser()
request.country = "US"
middleware.process_request(request)

assert request.preferred_language == "en"

# Test 3: Sin usuario ni país claro, usa Accept-Language
request = RequestFactory().get(
    "/dashboard/",
    HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9,es;q=0.8"
)
request.user = AnonymousUser()
request.country = "CL"
middleware.process_request(request)

assert request.preferred_language == "en"  # Accept-Language tiene "en" primero
```

**Resultado esperado:** ✅ Detecta idioma por jerarquía: Usuario > URL > País > Header

---

## 🚀 Suite Completa de Pytest

```python
# tests/test_country_middleware.py

import pytest
from unittest.mock import Mock
from django.test import RequestFactory
from taller.middleware.country_context import (
    CountryContextMiddleware,
    LanguageContextMiddleware,
    _is_whitelisted,
)


class TestWhitelist:
    def test_static_files_whitelisted(self):
        assert _is_whitelisted("/static/css/style.css")
        assert _is_whitelisted("/media/uploads/image.jpg")
        assert _is_whitelisted("/admin/login/")
        assert _is_whitelisted("/favicon.ico")

    def test_normal_routes_not_whitelisted(self):
        assert not _is_whitelisted("/cl/vehiculos/")
        assert not _is_whitelisted("/us/dashboard/")


class TestCanonicalRedirects:
    @pytest.fixture
    def middleware(self):
        return CountryContextMiddleware(get_response=lambda r: r)

    def test_es_redirects_to_cl(self, middleware):
        request = RequestFactory().get("/es/vehiculos/")
        response = middleware.process_request(request)

        assert response.status_code == 301
        assert response.url == "/cl/vehiculos/"

    def test_en_redirects_to_us(self, middleware):
        request = RequestFactory().get("/en/dashboard/")
        response = middleware.process_request(request)

        assert response.status_code == 301
        assert response.url == "/us/dashboard/"

    def test_query_string_preserved(self, middleware):
        request = RequestFactory().get("/es/vehiculos/?page=2")
        response = middleware.process_request(request)

        assert response.url == "/cl/vehiculos/?page=2"


class TestConflictRedirects:
    @pytest.fixture
    def middleware(self):
        return CountryContextMiddleware(get_response=lambda r: r)

    @pytest.fixture
    def user_cl(self):
        user = Mock()
        user.is_authenticated = True
        user.empresa = Mock(pais="CL")
        return user

    def test_get_conflict_302(self, middleware, user_cl):
        request = RequestFactory().get("/us/vehiculos/")
        request.user = user_cl

        response = middleware.process_request(request)

        assert response.status_code == 302
        assert response.url == "/cl/vehiculos/"

    def test_post_conflict_307(self, middleware, user_cl):
        request = RequestFactory().post("/us/vehiculos/crear/")
        request.user = user_cl

        response = middleware.process_request(request)

        assert response.status_code == 307  # Mantiene método
        assert response.url == "/cl/vehiculos/crear/"

    def test_no_conflict_no_redirect(self, middleware, user_cl):
        request = RequestFactory().get("/cl/vehiculos/")
        request.user = user_cl

        response = middleware.process_request(request)

        assert response is None  # No redirige
        assert request.country == "CL"


class TestDetectionHierarchy:
    @pytest.fixture
    def middleware(self):
        return CountryContextMiddleware(get_response=lambda r: r)

    def test_url_overrides_subdomain(self, middleware):
        request = RequestFactory().get("/us/dashboard/", HTTP_HOST="cl.myapp.com")
        request.user = Mock(is_authenticated=False)

        middleware.process_request(request)

        assert request.country == "US"
        assert request._country_source == "url"

    def test_subdomain_when_no_url(self, middleware):
        request = RequestFactory().get("/dashboard/", HTTP_HOST="us.myapp.com")
        request.user = Mock(is_authenticated=False)

        middleware.process_request(request)

        assert request.country == "US"
        assert request._country_source == "subdomain"


class TestSwapPrefix:
    def test_basic_swap(self):
        from taller.middleware.country_context import CountryContextMiddleware
        swap = CountryContextMiddleware._swap_prefix

        assert swap("/cl/vehiculos", "/cl", "/us") == "/us/vehiculos"
        assert swap("/us/dashboard", "/us", "/cl") == "/cl/dashboard"

    def test_swap_with_trailing_slash(self):
        swap = CountryContextMiddleware._swap_prefix

        assert swap("/cl/", "/cl", "/us") == "/us/"
        assert swap("/cl", "/cl", "/us") == "/us"

    def test_swap_without_prefix(self):
        swap = CountryContextMiddleware._swap_prefix

        # Inyecta prefijo si no existe
        assert swap("/vehiculos", "/cl", "/us") == "/us/vehiculos"


# Ejecutar con:
# pytest tests/test_country_middleware.py -v
```

---

## 🎯 Smoke Tests Rápidos (Manual)

### Test 1: Whitelist
```bash
# Debe retornar sin redirección
curl -I http://localhost:8000/static/css/style.css
# → 200 OK (sin redirect)

curl -I http://localhost:8000/admin/
# → 302 (redirect a login, pero NO a /cl/admin/)
```

### Test 2: Canonical
```bash
# Debe redirigir con 301
curl -I http://localhost:8000/es/vehiculos/
# → 301 Location: /cl/vehiculos/

curl -I http://localhost:8000/en/dashboard/
# → 301 Location: /us/dashboard/
```

### Test 3: Conflicto
```bash
# Login como usuario CL, luego accede a US
# Debe redirigir a /cl/*
curl -I http://localhost:8000/us/vehiculos/ \
  -H "Cookie: sessionid=..."
# → 302 Location: /cl/vehiculos/
```

---

## 📊 Cobertura Esperada

| Funcionalidad | Cobertura |
|---------------|-----------|
| Whitelist | 100% |
| Canonicalización legacy | 100% |
| Swap prefix robusto | 100% |
| Conflicto URL/empresa | 100% |
| Jerarquía de detección | 100% |
| Query string preservado | 100% |
| Prevención de bucles | 100% |
| POST seguro (307) | 100% |
| Subdominio con puerto | 100% |
| Idioma con Accept-Language | 100% |

---

## 🐛 Casos Edge a Verificar

- [ ] Ruta sin trailing slash: `/cl` vs `/cl/`
- [ ] Query string vacío: `?`
- [ ] Query string con caracteres especiales: `?q=motor%20V8`
- [ ] Subdominio triple: `cl.staging.prod.myapp.com`
- [ ] Puerto no estándar: `us.local:8080`
- [ ] Usuario sin empresa (solo perfil)
- [ ] POST con body JSON
- [ ] PUT/PATCH con conflicto
- [ ] Rutas con `/cl/es/` (legacy anidado)
- [ ] Accept-Language con múltiples idiomas

---

## ✅ Resultado Final

Con estos tests garantizas:

✅ **Sin bucles** de redirección
✅ **Canonical URLs** (/es → /cl, /en → /us)
✅ **Whitelist** respetada (static/admin/webhooks)
✅ **POST seguro** con 307
✅ **Query string** siempre preservado
✅ **Multi-tenant** estricto (URL vs empresa)
✅ **Regex robusto** (sin slicing frágil)
✅ **Idioma** con Accept-Language fallback

**Próximo paso**: Ejecutar suite completa con `pytest -v --cov=taller.middleware`
