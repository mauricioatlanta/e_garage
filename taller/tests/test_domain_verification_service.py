"""
Tests para DomainVerificationService.

Usa mocks de dns.resolver para evitar consultas DNS reales.
Cubre: éxito, fallos de distinto tipo, contador de intentos,
       estructura de VerificationResult y estados inválidos.
"""

import pytest
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User

from taller.models.empresa import Empresa
from taller.models.empresa_dominio import EmpresaDominio
from taller.services.domain_verification import DomainVerificationService, VerificationResult


# ── Helper ────────────────────────────────────────────────────────────────────


def _dns_answer(*txt_values: str):
    """Mock de dns.resolver.Answer con los valores TXT indicados.

    Cada valor se convierte en un rdata con rdata.strings = [valor.encode()].
    """
    rdata_list = []
    for val in txt_values:
        rdata = MagicMock()
        rdata.strings = [val.encode("utf-8")]
        rdata_list.append(rdata)
    answer = MagicMock()
    answer.__iter__ = lambda self: iter(rdata_list)
    return answer


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def owner(db):
    return User.objects.create_user("dvsvc_owner", "owner@example.com", "pass")


@pytest.fixture
def empresa(db, owner):
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(
        user=owner,
        nombre_taller="Taller DVSvc",
        pais="CL",
        email="dvsvc@example.com",
        telefono="+56911111111",
    )


@pytest.fixture
def dominio(db, empresa):
    """EmpresaDominio en estado PENDIENTE, listo para verificar."""
    return EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="taller.midominio.cl",
    )


# ── Tests: verificación exitosa ───────────────────────────────────────────────


@pytest.mark.django_db
def test_txt_correcto_activa_dominio(dominio):
    expected = dominio.get_txt_record_value()

    with patch("dns.resolver.resolve", return_value=_dns_answer(expected)):
        result = DomainVerificationService.verificar(dominio)

    assert result.success is True
    assert result.dominio == "taller.midominio.cl"
    assert result.txt_name == dominio.get_txt_record_name()
    assert result.expected == expected
    assert expected in result.found
    assert result.error == ""

    dominio.refresh_from_db()
    assert dominio.estado       == EmpresaDominio.Estado.ACTIVO
    assert dominio.verificado_en is not None
    assert dominio.ultimo_check_dns is not None
    assert dominio.intentos_verificacion == 1


@pytest.mark.django_db
def test_multiples_txt_con_valor_correcto(dominio):
    """Si hay varios TXT y uno coincide, la verificación es exitosa."""
    expected = dominio.get_txt_record_value()

    with patch("dns.resolver.resolve", return_value=_dns_answer("v=spf1 include:egarage.cl ~all", expected)):
        result = DomainVerificationService.verificar(dominio)

    assert result.success is True
    dominio.refresh_from_db()
    assert dominio.estado == EmpresaDominio.Estado.ACTIVO


@pytest.mark.django_db
def test_txt_correcto_invalida_cache_de_resolucion_exactamente_una_vez(dominio):
    """Al activar el dominio, la caché de HostTenantMiddleware debe invalidarse
    para que el próximo request no sirva un miss negativo cacheado."""
    expected = dominio.get_txt_record_value()

    with patch("dns.resolver.resolve", return_value=_dns_answer(expected)), \
         patch(
             "taller.services.domain_resolver_service.DomainResolverService.invalidate_cache"
         ) as mock_invalidate:
        result = DomainVerificationService.verificar(dominio)

    assert result.success is True
    mock_invalidate.assert_called_once_with(dominio.dominio)


# ── Tests: verificación fallida ───────────────────────────────────────────────


@pytest.mark.django_db
def test_txt_incorrecto_marca_error_dns(dominio):
    with patch("dns.resolver.resolve", return_value=_dns_answer("egarage-verify=token-ajeno")):
        result = DomainVerificationService.verificar(dominio)

    assert result.success is False
    assert result.error == ""                   # no fue excepción, solo valor incorrecto
    assert "egarage-verify=token-ajeno" in result.found

    dominio.refresh_from_db()
    assert dominio.estado         == EmpresaDominio.Estado.ERROR_DNS
    assert dominio.verificado_en  is None       # no debe marcarse como verificado
    assert dominio.intentos_verificacion == 1


@pytest.mark.django_db
def test_txt_incorrecto_no_invalida_cache(dominio):
    """Un fallo de verificación no debe tocar la caché de resolución de dominio."""
    with patch("dns.resolver.resolve", return_value=_dns_answer("egarage-verify=token-ajeno")), \
         patch(
             "taller.services.domain_resolver_service.DomainResolverService.invalidate_cache"
         ) as mock_invalidate:
        result = DomainVerificationService.verificar(dominio)

    assert result.success is False
    mock_invalidate.assert_not_called()


@pytest.mark.django_db
def test_sin_registros_txt_marca_error_dns(dominio):
    import dns.resolver

    with patch("dns.resolver.resolve", side_effect=dns.resolver.NoAnswer()):
        result = DomainVerificationService.verificar(dominio)

    assert result.success is False
    assert result.found   == []
    assert result.error   == ""     # NoAnswer se absorbe internamente

    dominio.refresh_from_db()
    assert dominio.estado == EmpresaDominio.Estado.ERROR_DNS


@pytest.mark.django_db
def test_nxdomain_marca_error_dns(dominio):
    import dns.resolver

    with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
        result = DomainVerificationService.verificar(dominio)

    assert result.success is False
    assert result.found   == []
    assert result.error   == ""     # NXDOMAIN se absorbe internamente

    dominio.refresh_from_db()
    assert dominio.estado == EmpresaDominio.Estado.ERROR_DNS


@pytest.mark.django_db
def test_timeout_marca_error_dns_con_mensaje(dominio):
    import dns.exception

    with patch("dns.resolver.resolve", side_effect=dns.exception.Timeout()):
        result = DomainVerificationService.verificar(dominio)

    assert result.success is False
    assert "Timeout" in result.error        # TimeoutError re-lanzado con mensaje

    dominio.refresh_from_db()
    assert dominio.estado == EmpresaDominio.Estado.ERROR_DNS


@pytest.mark.django_db
def test_error_dns_generico_marca_error_dns(dominio):
    import dns.exception

    with patch("dns.resolver.resolve", side_effect=dns.exception.DNSException("error genérico")):
        result = DomainVerificationService.verificar(dominio)

    assert result.success is False
    assert result.error != ""

    dominio.refresh_from_db()
    assert dominio.estado == EmpresaDominio.Estado.ERROR_DNS


# ── Tests: contador de intentos y persistencia ────────────────────────────────


@pytest.mark.django_db
def test_intentos_se_incrementan_en_cada_llamada(dominio):
    import dns.resolver

    for i in range(1, 4):
        dominio.refresh_from_db()
        with patch("dns.resolver.resolve", side_effect=dns.resolver.NXDOMAIN()):
            DomainVerificationService.verificar(dominio)
        dominio.refresh_from_db()
        assert dominio.intentos_verificacion == i


@pytest.mark.django_db
def test_ultimo_check_dns_se_registra_siempre(dominio):
    assert dominio.ultimo_check_dns is None

    with patch("dns.resolver.resolve", return_value=_dns_answer("valor-incorrecto")):
        DomainVerificationService.verificar(dominio)

    dominio.refresh_from_db()
    assert dominio.ultimo_check_dns is not None


@pytest.mark.django_db
def test_exito_registra_verificado_en(dominio):
    expected = dominio.get_txt_record_value()

    with patch("dns.resolver.resolve", return_value=_dns_answer(expected)):
        DomainVerificationService.verificar(dominio)

    dominio.refresh_from_db()
    assert dominio.verificado_en is not None


# ── Tests: restricciones de estado ───────────────────────────────────────────


@pytest.mark.django_db
def test_estado_activo_lanza_valueerror(empresa):
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="ya-activo.midominio.cl",
        estado=EmpresaDominio.Estado.ACTIVO,
    )
    with pytest.raises(ValueError, match="no puede verificarse"):
        DomainVerificationService.verificar(ed)


@pytest.mark.django_db
def test_estado_suspendido_lanza_valueerror(empresa):
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="suspendido.midominio.cl",
        estado=EmpresaDominio.Estado.SUSPENDIDO,
    )
    with pytest.raises(ValueError, match="no puede verificarse"):
        DomainVerificationService.verificar(ed)


@pytest.mark.django_db
def test_estado_ssl_pendiente_lanza_valueerror(empresa):
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="ssl-pendiente.midominio.cl",
        estado=EmpresaDominio.Estado.SSL_PENDIENTE,
    )
    with pytest.raises(ValueError, match="no puede verificarse"):
        DomainVerificationService.verificar(ed)


@pytest.mark.django_db
def test_estado_verificando_es_valido(empresa):
    """VERIFICANDO está en puede_verificarse=True, debe ejecutarse sin error."""
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="verificando.midominio.cl",
        estado=EmpresaDominio.Estado.VERIFICANDO,
    )
    expected = ed.get_txt_record_value()

    with patch("dns.resolver.resolve", return_value=_dns_answer(expected)):
        result = DomainVerificationService.verificar(ed)

    assert result.success is True
    ed.refresh_from_db()
    assert ed.estado == EmpresaDominio.Estado.ACTIVO


@pytest.mark.django_db
def test_estado_error_dns_puede_reintentarse(empresa):
    """ERROR_DNS también está en puede_verificarse=True (reintento posible)."""
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="error-dns.midominio.cl",
        estado=EmpresaDominio.Estado.ERROR_DNS,
        intentos_verificacion=3,
    )
    expected = ed.get_txt_record_value()

    with patch("dns.resolver.resolve", return_value=_dns_answer(expected)):
        result = DomainVerificationService.verificar(ed)

    assert result.success is True
    ed.refresh_from_db()
    assert ed.estado                  == EmpresaDominio.Estado.ACTIVO
    assert ed.intentos_verificacion   == 4      # acumulado


# ── Tests: estructura de VerificationResult ───────────────────────────────────


def test_verification_result_defaults():
    r = VerificationResult(
        success=True,
        dominio="taller.example.com",
        txt_name="_egarage-verify.taller.example.com",
        expected="egarage-verify=abc-123",
        found=["egarage-verify=abc-123"],
    )
    assert r.error == ""
    assert r.found == ["egarage-verify=abc-123"]


def test_verification_result_fallo_sin_found():
    r = VerificationResult(
        success=False,
        dominio="taller.example.com",
        txt_name="_egarage-verify.taller.example.com",
        expected="egarage-verify=abc-123",
        error="Timeout al consultar ...",
    )
    assert r.found == []
    assert r.success is False
