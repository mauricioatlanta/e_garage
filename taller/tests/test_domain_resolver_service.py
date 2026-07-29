"""
Tests para DomainResolverService.

Estos tests verifican el servicio directamente, independiente del middleware.
Los tests del middleware (test_host_tenant_middleware.py) cubren la integración.

Cubre:
    - normalize_host: puerto, mayúsculas, IPv6
    - is_custom_host: plataforma, subdominios egarage, externos
    - get_for_host: hit positivo, miss negativo, caché
    - resolve: orquestación (plataforma → None, custom → ED o None)
    - invalidate_cache: limpia la entrada; siguiente llamada consulta DB
    - Constantes CACHE_TTL_* tienen valores razonables
"""

import pytest
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import RequestFactory

from taller.models import Empresa
from taller.models.empresa_dominio import EmpresaDominio
from taller.services.domain_resolver_service import (
    DomainResolverService,
    _SENTINEL,
    _PLATFORM_HOSTS,
)

factory = RequestFactory()
HOST = "taller.midominio.cl"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def owner(db):
    return User.objects.create_user("svc_owner", "svc@example.com", "pass")


@pytest.fixture
def empresa(db, owner):
    return Empresa.objects.create(user=owner, nombre_taller="Taller Servicio", pais="CL")


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


# ── normalize_host ────────────────────────────────────────────────────────────


class TestNormalizeHost:
    def _req(self, host):
        return factory.get("/", HTTP_HOST=host)

    def test_strip_puerto_http(self):
        assert DomainResolverService.normalize_host(self._req(f"{HOST}:8080")) == HOST

    def test_lowercase(self):
        assert DomainResolverService.normalize_host(self._req("TALLER.MiDominio.CL")) == HOST

    def test_sin_puerto_no_modifica(self):
        assert DomainResolverService.normalize_host(self._req(HOST)) == HOST

    def test_ipv6_sin_puerto(self):
        assert DomainResolverService.normalize_host(self._req("[::1]")) == "[::1]"

    def test_ipv6_con_puerto(self):
        assert DomainResolverService.normalize_host(self._req("[::1]:8000")) == "[::1]"


# ── is_custom_host ────────────────────────────────────────────────────────────


class TestIsCustomHost:
    def test_todos_los_platform_hosts_rechazados(self):
        for h in _PLATFORM_HOSTS:
            assert DomainResolverService.is_custom_host(h) is False, f"Falló con: {h}"

    def test_subdominio_egarage_rechazado(self):
        assert DomainResolverService.is_custom_host("taller.egarage.cl") is False
        assert DomainResolverService.is_custom_host("mi.egarage.cl") is False

    def test_host_vacio_rechazado(self):
        assert DomainResolverService.is_custom_host("") is False

    def test_dominio_externo_aceptado(self):
        assert DomainResolverService.is_custom_host(HOST) is True
        assert DomainResolverService.is_custom_host("mirepuesteria.com") is True
        assert DomainResolverService.is_custom_host("taller.cl") is True

    def test_dominio_similar_a_egarage_aceptado(self):
        assert DomainResolverService.is_custom_host("egarage-taller.com") is True


# ── get_for_host ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetForHost:
    def test_activo_devuelve_empresa_dominio(self, dominio_activo):
        result = DomainResolverService.get_for_host(HOST)
        assert result is not None
        assert result.pk == dominio_activo.pk

    def test_inexistente_devuelve_none(self, db):
        assert DomainResolverService.get_for_host("sin-registro.example.com") is None

    def test_suspendido_no_resuelve(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio=HOST, estado=EmpresaDominio.Estado.SUSPENDIDO
        )
        assert DomainResolverService.get_for_host(HOST) is None

    def test_pendiente_no_resuelve(self, empresa):
        EmpresaDominio.objects.create(
            empresa=empresa, dominio=HOST, estado=EmpresaDominio.Estado.PENDIENTE
        )
        assert DomainResolverService.get_for_host(HOST) is None

    def test_cache_hit_positivo_almacenado(self, dominio_activo):
        DomainResolverService.get_for_host(HOST)
        cached = cache.get(f"custom_domain:{HOST}", _SENTINEL)
        assert cached is not _SENTINEL
        assert cached.pk == dominio_activo.pk

    def test_cache_miss_negativo_almacenado(self, db):
        DomainResolverService.get_for_host("sin-registro.example.com")
        cached = cache.get("custom_domain:sin-registro.example.com", _SENTINEL)
        assert cached is not _SENTINEL
        assert cached is None

    def test_cache_hit_no_consulta_db(self, dominio_activo):
        DomainResolverService.get_for_host(HOST)   # prime
        with patch("taller.services.domain_resolver_service.EmpresaDominio.objects") as m:
            DomainResolverService.get_for_host(HOST)
            m.select_related.assert_not_called()

    def test_cache_negativo_no_consulta_db(self, db):
        DomainResolverService.get_for_host("sin-registro.example.com")  # prime
        with patch("taller.services.domain_resolver_service.EmpresaDominio.objects") as m:
            DomainResolverService.get_for_host("sin-registro.example.com")
            m.select_related.assert_not_called()


# ── resolve ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestResolve:
    def _req(self, host):
        return factory.get("/", HTTP_HOST=host)

    def test_host_plataforma_devuelve_none(self, db):
        assert DomainResolverService.resolve(self._req("egarage.cl")) is None

    def test_subdominio_egarage_devuelve_none(self, db):
        assert DomainResolverService.resolve(self._req("panel.egarage.cl")) is None

    def test_host_custom_activo_devuelve_empresa_dominio(self, dominio_activo):
        result = DomainResolverService.resolve(self._req(HOST))
        assert result is not None
        assert result.pk == dominio_activo.pk

    def test_host_custom_sin_registro_devuelve_none(self, db):
        assert DomainResolverService.resolve(self._req("sin-registro.example.com")) is None

    def test_resolve_popula_empresa_en_empresa_dominio(self, dominio_activo, empresa):
        result = DomainResolverService.resolve(self._req(HOST))
        assert result.empresa == empresa

    def test_host_con_puerto_resuelve_correctamente(self, dominio_activo):
        result = DomainResolverService.resolve(self._req(f"{HOST}:443"))
        assert result is not None
        assert result.pk == dominio_activo.pk


# ── invalidate_cache ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestInvalidateCache:
    def test_invalida_entrada_positiva(self, dominio_activo):
        DomainResolverService.get_for_host(HOST)   # prime
        DomainResolverService.invalidate_cache(HOST)
        cached = cache.get(f"custom_domain:{HOST}", _SENTINEL)
        assert cached is _SENTINEL   # eliminado del caché

    def test_invalida_entrada_negativa(self, db):
        DomainResolverService.get_for_host("sin-registro.example.com")   # prime
        DomainResolverService.invalidate_cache("sin-registro.example.com")
        cached = cache.get("custom_domain:sin-registro.example.com", _SENTINEL)
        assert cached is _SENTINEL

    def test_tras_invalidacion_consulta_db(self, dominio_activo):
        DomainResolverService.get_for_host(HOST)   # prime
        DomainResolverService.invalidate_cache(HOST)
        # Próxima llamada debe ir a DB (no puede parchear con mock previo)
        result = DomainResolverService.get_for_host(HOST)
        assert result is not None
        assert result.pk == dominio_activo.pk

    def test_invalida_host_inexistente_no_lanza(self, db):
        DomainResolverService.invalidate_cache("nunca-existio.example.com")  # no debe lanzar


# ── Constantes ────────────────────────────────────────────────────────────────


class TestConstantes:
    def test_cache_ttl_hit_mayor_que_miss(self):
        assert DomainResolverService.CACHE_TTL_HIT > DomainResolverService.CACHE_TTL_MISS

    def test_cache_ttl_hit_al_menos_60s(self):
        assert DomainResolverService.CACHE_TTL_HIT >= 60

    def test_cache_ttl_miss_positivo(self):
        assert DomainResolverService.CACHE_TTL_MISS > 0
