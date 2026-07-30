"""
Tests para LetsEncryptSSLIssuanceService.

Usa mocks de subprocess.run y operaciones de archivo para evitar llamadas
reales a certbot, nginx ni openssl.
"""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from django.contrib.auth.models import User

from taller.models.empresa import Empresa
from taller.models.empresa_dominio import EmpresaDominio
from taller.services.ssl_issuance import (
    LetsEncryptSSLIssuanceService,
    SSLIssuanceError,
    SSLIssuanceService,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _proc(returncode=0, stdout="", stderr=""):
    """Fake subprocess.CompletedProcess."""
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def _mock_path(exists=False):
    """Fake Path para conf de Nginx."""
    m = MagicMock(spec=Path)
    m.exists.return_value = exists
    return m


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def owner(db):
    return User.objects.create_user("ssl_owner", "ssl@example.com", "pass")


@pytest.fixture
def empresa(db, owner):
    return Empresa.objects.create(
        user=owner,
        nombre_taller="Taller SSL",
        pais="CL",
        email="ssl@example.com",
        telefono="+56911111111",
    )


@pytest.fixture
def dominio_activo(db, empresa):
    """EmpresaDominio ACTIVO, sin SSL aún."""
    return EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="taller.example.cl",
        estado=EmpresaDominio.Estado.ACTIVO,
        ssl_emitido=False,
    )


@pytest.fixture
def dominio_con_ssl(db, empresa):
    """EmpresaDominio con SSL ya emitido."""
    return EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="ssl.example.cl",
        estado=EmpresaDominio.Estado.ACTIVO,
        ssl_emitido=True,
        ssl_cert_path="/etc/letsencrypt/live/ssl.example.cl/fullchain.pem",
        ssl_key_path="/etc/letsencrypt/live/ssl.example.cl/privkey.pem",
        ssl_expira_en=date(2026, 10, 1),
    )


@pytest.fixture
def svc():
    return LetsEncryptSSLIssuanceService()


# ── Tests: emitir — happy path ─────────────────────────────────────────────────


@pytest.mark.django_db
def test_emitir_actualiza_db_correctamente(dominio_activo, svc):
    expiry = date(2026, 9, 1)

    with (
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_escribir_nginx_conf"),
        patch.object(svc, "_recargar_nginx"),
        patch.object(LetsEncryptSSLIssuanceService, "_leer_expiracion", return_value=expiry),
    ):
        svc.emitir(dominio_activo)

    dominio_activo.refresh_from_db()
    assert dominio_activo.ssl_emitido   is True
    assert dominio_activo.ssl_expira_en == expiry
    assert dominio_activo.ssl_cert_path == "/etc/letsencrypt/live/taller.example.cl/fullchain.pem"
    assert dominio_activo.ssl_key_path  == "/etc/letsencrypt/live/taller.example.cl/privkey.pem"
    assert dominio_activo.estado        == EmpresaDominio.Estado.ACTIVO


@pytest.mark.django_db
def test_emitir_pasa_por_ssl_pendiente(dominio_activo, svc):
    """El estado debe pasar por SSL_PENDIENTE antes de llamar a certbot."""
    estados_durante_certbot = []

    def _capturar(*a, **kw):
        dominio_activo.refresh_from_db()
        estados_durante_certbot.append(dominio_activo.estado)

    with (
        patch.object(svc, "_ejecutar_certbot", side_effect=_capturar),
        patch.object(svc, "_escribir_nginx_conf"),
        patch.object(svc, "_recargar_nginx"),
        patch.object(LetsEncryptSSLIssuanceService, "_leer_expiracion", return_value=None),
    ):
        svc.emitir(dominio_activo)

    assert EmpresaDominio.Estado.SSL_PENDIENTE in estados_durante_certbot


@pytest.mark.django_db
def test_emitir_ssl_expiracion_none_no_rompe(dominio_activo, svc):
    """ssl_expira_en=None es válido cuando openssl no puede leer el cert."""
    with (
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_escribir_nginx_conf"),
        patch.object(svc, "_recargar_nginx"),
        patch.object(LetsEncryptSSLIssuanceService, "_leer_expiracion", return_value=None),
    ):
        svc.emitir(dominio_activo)

    dominio_activo.refresh_from_db()
    assert dominio_activo.ssl_emitido   is True
    assert dominio_activo.ssl_expira_en is None


# ── Tests: emitir — estados válidos / inválidos ────────────────────────────────


@pytest.mark.django_db
def test_emitir_ssl_pendiente_es_estado_valido(empresa, svc):
    """SSL_PENDIENTE permite reintento sin ValueError."""
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="retry.example.cl",
        estado=EmpresaDominio.Estado.SSL_PENDIENTE,
    )
    with (
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_escribir_nginx_conf"),
        patch.object(svc, "_recargar_nginx"),
        patch.object(LetsEncryptSSLIssuanceService, "_leer_expiracion", return_value=None),
    ):
        svc.emitir(ed)  # no debe lanzar

    ed.refresh_from_db()
    assert ed.ssl_emitido is True


@pytest.mark.django_db
@pytest.mark.parametrize("estado", [
    EmpresaDominio.Estado.PENDIENTE,
    EmpresaDominio.Estado.VERIFICANDO,
    EmpresaDominio.Estado.ERROR_DNS,
    EmpresaDominio.Estado.SUSPENDIDO,
])
def test_emitir_estado_no_apto_lanza_valueerror(empresa, svc, estado):
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio=f"{estado.lower()}.example.cl",
        estado=estado,
    )
    with pytest.raises(ValueError, match="no puede recibir un certificado"):
        svc.emitir(ed)


# ── Tests: emitir — fallos con rollback ───────────────────────────────────────


@pytest.mark.django_db
def test_certbot_fallo_lanza_ssl_issuance_error_y_revierte_activo(dominio_activo, svc):
    with (
        patch.object(svc, "_ejecutar_certbot", side_effect=SSLIssuanceError("certbot rc=1")),
        pytest.raises(SSLIssuanceError, match="certbot"),
    ):
        svc.emitir(dominio_activo)

    dominio_activo.refresh_from_db()
    assert dominio_activo.ssl_emitido is False
    assert dominio_activo.estado      == EmpresaDominio.Estado.ACTIVO


@pytest.mark.django_db
def test_nginx_fallo_lanza_ssl_issuance_error_y_revierte_activo(dominio_activo, svc):
    with (
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_escribir_nginx_conf"),
        patch.object(svc, "_recargar_nginx", side_effect=SSLIssuanceError("nginx -t falló")),
        pytest.raises(SSLIssuanceError),
    ):
        svc.emitir(dominio_activo)

    dominio_activo.refresh_from_db()
    assert dominio_activo.ssl_emitido is False
    assert dominio_activo.estado      == EmpresaDominio.Estado.ACTIVO


# ── Tests: revocar ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_revocar_limpia_db(dominio_con_ssl, svc):
    with (
        patch.object(svc, "_nginx_conf_path", return_value=_mock_path(exists=False)),
        patch.object(svc, "_ejecutar_certbot_delete"),
    ):
        svc.revocar(dominio_con_ssl)

    dominio_con_ssl.refresh_from_db()
    assert dominio_con_ssl.ssl_emitido   is False
    assert dominio_con_ssl.ssl_cert_path == ""
    assert dominio_con_ssl.ssl_key_path  == ""
    assert dominio_con_ssl.ssl_expira_en is None


@pytest.mark.django_db
def test_revocar_llama_certbot_delete_cuando_ssl_emitido(dominio_con_ssl, svc):
    with (
        patch.object(svc, "_nginx_conf_path", return_value=_mock_path(exists=False)),
        patch.object(svc, "_ejecutar_certbot_delete") as mock_delete,
    ):
        svc.revocar(dominio_con_ssl)

    mock_delete.assert_called_once_with(dominio_con_ssl.dominio)


@pytest.mark.django_db
def test_revocar_sin_ssl_emitido_no_llama_certbot_delete(empresa, svc):
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="nossl.example.cl",
        estado=EmpresaDominio.Estado.ACTIVO,
        ssl_emitido=False,
    )
    with (
        patch.object(svc, "_nginx_conf_path", return_value=_mock_path(exists=False)),
        patch.object(svc, "_ejecutar_certbot_delete") as mock_delete,
    ):
        svc.revocar(ed)

    mock_delete.assert_not_called()


@pytest.mark.django_db
def test_revocar_elimina_conf_cuando_existe(dominio_con_ssl, svc):
    mock_conf = _mock_path(exists=True)

    with (
        patch.object(svc, "_nginx_conf_path", return_value=mock_conf),
        patch.object(svc, "_recargar_nginx"),
        patch.object(svc, "_ejecutar_certbot_delete"),
    ):
        svc.revocar(dominio_con_ssl)

    mock_conf.unlink.assert_called_once()


@pytest.mark.django_db
def test_revocar_certbot_delete_fallo_no_interrumpe_limpieza_db(dominio_con_ssl, svc):
    """Un fallo en certbot delete no debe impedir la limpieza del registro."""
    with (
        patch.object(svc, "_nginx_conf_path", return_value=_mock_path(exists=False)),
        patch.object(
            svc, "_ejecutar_certbot_delete", side_effect=SSLIssuanceError("certbot delete fallo")
        ),
    ):
        svc.revocar(dominio_con_ssl)  # no debe lanzar

    dominio_con_ssl.refresh_from_db()
    assert dominio_con_ssl.ssl_emitido is False


# ── Tests: _ejecutar_certbot (subprocess) ────────────────────────────────────


def test_ejecutar_certbot_incluye_dominio_y_flags(svc):
    with patch("subprocess.run", return_value=_proc(returncode=0)) as mock_run:
        svc._ejecutar_certbot("taller.example.cl")

    args = mock_run.call_args[0][0]
    assert args[0] == "certbot"
    assert "taller.example.cl" in args
    assert "--non-interactive" in args
    assert "--agree-tos" in args


def test_ejecutar_certbot_fallo_lanza_ssl_issuance_error(svc):
    with patch("subprocess.run", return_value=_proc(returncode=1, stderr="ACME error")):
        with pytest.raises(SSLIssuanceError, match="certbot falló"):
            svc._ejecutar_certbot("taller.example.cl")


def test_ejecutar_certbot_delete_fallo_lanza_ssl_issuance_error(svc):
    with patch("subprocess.run", return_value=_proc(returncode=1, stderr="not found")):
        with pytest.raises(SSLIssuanceError, match="certbot delete falló"):
            svc._ejecutar_certbot_delete("taller.example.cl")


# ── Tests: _recargar_nginx ────────────────────────────────────────────────────


def test_recargar_nginx_happy_path(svc):
    with patch("subprocess.run", return_value=_proc(returncode=0)):
        svc._recargar_nginx()  # no debe lanzar


def test_recargar_nginx_test_fallo_lanza_error(svc):
    with patch("subprocess.run", return_value=_proc(returncode=1, stderr="unknown directive")):
        with pytest.raises(SSLIssuanceError, match="nginx -t"):
            svc._recargar_nginx()


def test_recargar_nginx_reload_fallo_lanza_error(svc):
    with patch("subprocess.run", side_effect=[
        _proc(returncode=0),                          # nginx -t → OK
        _proc(returncode=1, stderr="unit not found"), # systemctl reload → FAIL
    ]):
        with pytest.raises(SSLIssuanceError, match="systemctl reload"):
            svc._recargar_nginx()


# ── Tests: _leer_expiracion ───────────────────────────────────────────────────


def test_leer_expiracion_parsea_fecha_correctamente():
    stdout = "notAfter=Sep  1 12:00:00 2026 GMT\n"
    with patch("subprocess.run", return_value=_proc(returncode=0, stdout=stdout)):
        result = LetsEncryptSSLIssuanceService._leer_expiracion("/fake/fullchain.pem")
    assert result == date(2026, 9, 1)


def test_leer_expiracion_openssl_fallo_retorna_none():
    with patch("subprocess.run", return_value=_proc(returncode=1)):
        result = LetsEncryptSSLIssuanceService._leer_expiracion("/fake/fullchain.pem")
    assert result is None


def test_leer_expiracion_salida_malformada_retorna_none():
    with patch("subprocess.run", return_value=_proc(returncode=0, stdout="salida inesperada")):
        result = LetsEncryptSSLIssuanceService._leer_expiracion("/fake/fullchain.pem")
    assert result is None


# ── Tests: _escribir_nginx_conf ───────────────────────────────────────────────


def test_escribir_nginx_conf_contiene_dominio_y_rutas(tmp_path, svc):
    svc.NGINX_CONF_DIR = tmp_path
    svc._escribir_nginx_conf("taller.example.cl")

    conf = (tmp_path / "tenant_taller.example.cl.conf").read_text()
    assert "server_name taller.example.cl" in conf
    assert "/etc/letsencrypt/live/taller.example.cl/fullchain.pem" in conf
    assert "/etc/letsencrypt/live/taller.example.cl/privkey.pem" in conf
    assert "proxy_pass http://127.0.0.1:8000" in conf


def test_nginx_conf_path_usa_prefijo_tenant(svc):
    path = svc._nginx_conf_path("mi-taller.cl")
    assert path.name == "tenant_mi-taller.cl.conf"


# ── Tests: SSLIssuanceService es ABC ─────────────────────────────────────────


def test_ssl_issuance_service_no_es_instanciable_directamente():
    with pytest.raises(TypeError):
        SSLIssuanceService()
