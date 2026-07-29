"""
Tests para HostTenantMiddleware (Fase 2 — dominios personalizados).

Cubre:
    - Normalización de host (puerto, mayúsculas).
    - Detección de host personalizado vs. plataforma.
    - Resolución de empresa desde EmpresaDominio ACTIVO.
    - Estados no ACTIVO (SUSPENDIDO, PENDIENTE) → sin resolución.
    - Caché: hit positivo, hit negativo, miss.
    - Integración con EmpresaResolverMiddleware:
        · Usuario del mismo tenant → permitido.
        · Usuario de otro tenant → rechazado (redirect 302).
        · Acceso por egarage.cl → comportamiento sin cambios.
"""

import pytest
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory

from taller.models import Empresa
from taller.models.empresa_dominio import EmpresaDominio
from taller.middleware.host_tenant import (
    HostTenantMiddleware,
    _get_empresa_dominio_activo,
    _is_custom_host,
    _normalize_host,
    _SENTINEL,
)
from taller.middleware.empresa_resolver import EmpresaResolverMiddleware

# ── Constantes de test ────────────────────────────────────────────────────────

HOST = "taller.midominio.cl"
factory = RequestFactory()


def _ok(request):
    return HttpResponse("ok")


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def owner_user(db):
    return User.objects.create_user("tenant_owner", "owner@example.com", "pass")


@pytest.fixture
def empresa(db, owner_user):
    return Empresa.objects.create(
        user=owner_user,
        nombre_taller="Taller Externo",
        pais="CL",
    )


@pytest.fixture
def otro_user(db):
    return User.objects.create_user("otro_owner", "otro@example.com", "pass")


@pytest.fixture
def otra_empresa(db, otro_user):
    return Empresa.objects.create(
        user=otro_user,
        nombre_taller="Otro Taller",
        pais="CL",
    )


@pytest.fixture(autouse=True)
def limpiar_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def dominio_activo(db, empresa):
    return EmpresaDominio.objects.create(
        empresa=empresa,
        dominio=HOST,
        estado=EmpresaDominio.Estado.ACTIVO,
    )


# ── Utilidades helper para correr la cadena de middlewares ────────────────────


def _make_request(host, user=None):
    """Crea un request con HTTP_HOST y user configurados."""
    req = factory.get("/", HTTP_HOST=host)
    req.user = user or AnonymousUser()
    req.session = MagicMock()   # logout() necesita session.flush()
    return req


def _run_host(request):
    """Ejecuta solo HostTenantMiddleware."""
    return HostTenantMiddleware(_ok)(request)


def _run_chain(request):
    """Ejecuta HostTenantMiddleware → EmpresaResolverMiddleware → _ok."""
    return HostTenantMiddleware(EmpresaResolverMiddleware(_ok))(request)


# ── Tests: normalización de host ──────────────────────────────────────────────


class TestNormalizacionHost:
    def test_strip_puerto(self):
        req = factory.get("/", HTTP_HOST=f"{HOST}:8080")
        assert _normalize_host(req) == HOST

    def test_lowercase(self):
        req = factory.get("/", HTTP_HOST="TALLER.MiDominio.CL")
        assert _normalize_host(req) == "taller.midominio.cl"

    def test_sin_puerto_no_altera(self):
        req = factory.get("/", HTTP_HOST=HOST)
        assert _normalize_host(req) == HOST

    def test_ipv6_no_stripea_brackets(self):
        req = factory.get("/", HTTP_HOST="[::1]:8000")
        assert _normalize_host(req) == "[::1]"


# ── Tests: detección de host personalizado ────────────────────────────────────


class TestIsCustomHost:
    def test_egarage_cl_no_es_custom(self):
        assert _is_custom_host("egarage.cl") is False

    def test_www_egarage_cl_no_es_custom(self):
        assert _is_custom_host("www.egarage.cl") is False

    def test_subdominio_egarage_no_es_custom(self):
        assert _is_custom_host("app.egarage.cl") is False
        assert _is_custom_host("api.egarage.cl") is False

    def test_localhost_no_es_custom(self):
        assert _is_custom_host("localhost") is False

    def test_ip_loopback_no_es_custom(self):
        assert _is_custom_host("127.0.0.1") is False

    def test_host_vacio_no_es_custom(self):
        assert _is_custom_host("") is False

    def test_dominio_externo_es_custom(self):
        assert _is_custom_host(HOST) is True
        assert _is_custom_host("taller.cl") is True
        assert _is_custom_host("mirepuesteria.com") is True


# ── Tests: resolución desde EmpresaDominio ────────────────────────────────────


@pytest.mark.django_db
class TestResolucionDominio:
    def test_host_valido_puebla_empresa(self, dominio_activo):
        req = _make_request(HOST)
        _run_host(req)
        assert req.empresa == dominio_activo.empresa
        assert req.company == dominio_activo.empresa
        assert req.country == "CL"
        assert req.is_custom_domain is True

    def test_host_inexistente_no_puebla_empresa(self, db):
        req = _make_request("sin-registro.com")
        _run_host(req)
        assert req.is_custom_domain is False
        assert not hasattr(req, "empresa")  # HostTenant no lo inicializa cuando no hay match

    def test_dominio_suspendido_no_resuelve(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio=HOST, estado=EmpresaDominio.Estado.SUSPENDIDO
        )
        req = _make_request(HOST)
        _run_host(req)
        assert req.is_custom_domain is False

    def test_dominio_pendiente_no_resuelve(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio=HOST, estado=EmpresaDominio.Estado.PENDIENTE
        )
        req = _make_request(HOST)
        _run_host(req)
        assert req.is_custom_domain is False

    def test_dominio_verificando_no_resuelve(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio=HOST, estado=EmpresaDominio.Estado.VERIFICANDO
        )
        req = _make_request(HOST)
        _run_host(req)
        assert req.is_custom_domain is False

    def test_host_plataforma_is_custom_domain_falso(self, db):
        req = _make_request("egarage.cl")
        _run_host(req)
        assert req.is_custom_domain is False


# ── Tests: comportamiento de caché ────────────────────────────────────────────


@pytest.mark.django_db
class TestCache:
    def test_cache_miss_devuelve_empresa_dominio(self, dominio_activo):
        result = _get_empresa_dominio_activo(HOST)
        assert result is not None
        assert result.pk == dominio_activo.pk

    def test_cache_miss_almacena_resultado_positivo(self, dominio_activo):
        _get_empresa_dominio_activo(HOST)
        cached = cache.get(f"custom_domain:{HOST}", _SENTINEL)
        assert cached is not _SENTINEL
        assert cached.pk == dominio_activo.pk

    def test_cache_miss_almacena_none_para_host_inexistente(self, db):
        host = "no-existe.example.com"
        result = _get_empresa_dominio_activo(host)
        assert result is None
        cached = cache.get(f"custom_domain:{host}", _SENTINEL)
        assert cached is not _SENTINEL
        assert cached is None   # miss negativo cacheado explícitamente

    def test_cache_hit_no_consulta_db(self, dominio_activo):
        _get_empresa_dominio_activo(HOST)   # prime cache
        with patch("taller.services.domain_resolver_service.EmpresaDominio.objects") as mock_mgr:
            result = _get_empresa_dominio_activo(HOST)
            mock_mgr.select_related.assert_not_called()
        assert result is not None

    def test_cache_negativo_no_consulta_db(self, db):
        host = "no-existe.example.com"
        _get_empresa_dominio_activo(host)   # prime negative cache
        with patch("taller.services.domain_resolver_service.EmpresaDominio.objects") as mock_mgr:
            result = _get_empresa_dominio_activo(host)
            mock_mgr.select_related.assert_not_called()
        assert result is None


# ── Tests: integración HostTenantMiddleware + EmpresaResolverMiddleware ───────


@pytest.mark.django_db
class TestIntegracionCadenaMiddleware:
    def test_usuario_anonimo_custom_domain(self, dominio_activo):
        """Anónimo en dominio personalizado → empresa fijada por host, pass."""
        req = _make_request(HOST)
        resp = _run_chain(req)
        assert resp.status_code == 200
        assert req.empresa == dominio_activo.empresa
        assert req.is_custom_domain is True

    def test_usuario_mismo_tenant_permitido(self, dominio_activo, owner_user):
        """Propietario del tenant accede a su dominio personalizado."""
        req = _make_request(HOST, owner_user)
        resp = _run_chain(req)
        assert resp.status_code == 200
        assert req.empresa == dominio_activo.empresa

    def test_usuario_otro_tenant_rechazado(self, dominio_activo, otro_user):
        """Usuario de otra empresa en un dominio personalizado → 302 a login."""
        req = _make_request(HOST, otro_user)
        resp = _run_chain(req)
        assert resp.status_code == 302

    def test_acceso_egarage_cl_usuario_autenticado(self, empresa, owner_user):
        """egarage.cl con usuario autenticado → empresa resuelta desde usuario, sin custom domain."""
        req = _make_request("egarage.cl", owner_user)
        resp = _run_chain(req)
        assert resp.status_code == 200
        assert req.is_custom_domain is False
        assert req.empresa == empresa

    def test_acceso_egarage_cl_anonimo(self, db):
        """egarage.cl anónimo → empresa=None, flujo sin cambios."""
        req = _make_request("egarage.cl")
        resp = _run_chain(req)
        assert resp.status_code == 200
        assert req.is_custom_domain is False
        assert req.empresa is None
