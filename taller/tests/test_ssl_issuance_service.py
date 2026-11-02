"""
Tests para LetsEncryptSSLIssuanceService.

Usa mocks de subprocess.run y operaciones de archivo para evitar llamadas
reales a certbot, nginx ni openssl.
"""

import os
import stat
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
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(
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


@pytest.mark.django_db
def test_A_conf_inexistente_nginx_falla_conf_desaparece(dominio_activo, svc, tmp_path):
    """CASO A: el .conf no existía, esta ejecución lo escribe de verdad
    (sin mockear _escribir_nginx_conf) y, si nginx falla después, el
    archivo recién creado debe desaparecer del disco."""
    def _conf_path(dominio):
        return tmp_path / f"tenant_{dominio}.conf"

    with (
        patch.object(svc, "_nginx_conf_path", side_effect=_conf_path),
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_recargar_nginx", side_effect=SSLIssuanceError("nginx -t falló")),
        pytest.raises(SSLIssuanceError),
    ):
        svc.emitir(dominio_activo)

    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    assert not conf_path.exists()
    assert list(tmp_path.iterdir()) == []  # sin restos (.tmp<pid> incluidos)
    dominio_activo.refresh_from_db()
    assert dominio_activo.ssl_emitido is False
    assert dominio_activo.estado      == EmpresaDominio.Estado.ACTIVO


@pytest.mark.django_db
def test_B_conf_preexistente_restaura_contenido_original_tras_fallo(dominio_activo, svc, tmp_path):
    """CASO B — el hallazgo crítico de Fase 329: no basta con "no borrar" un
    .conf preexistente. _escribir_nginx_conf() lo sobrescribe de verdad con
    la plantilla nueva; si nginx falla después, el contenido en disco debe
    volver a ser EXACTAMENTE el original, no el nuevo (aunque el archivo
    "siga existiendo")."""
    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    conf_path.write_text("ORIGINAL CONFIG\n", encoding="utf-8")

    with (
        patch.object(svc, "_nginx_conf_path", return_value=conf_path),
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_recargar_nginx", side_effect=SSLIssuanceError("nginx -t falló")),
        pytest.raises(SSLIssuanceError),
    ):
        svc.emitir(dominio_activo)

    assert conf_path.read_text(encoding="utf-8") == "ORIGINAL CONFIG\n"
    dominio_activo.refresh_from_db()
    assert dominio_activo.ssl_emitido is False
    assert dominio_activo.estado      == EmpresaDominio.Estado.ACTIVO


@pytest.mark.django_db
def test_C_certbot_falla_antes_de_escribir_no_toca_conf_preexistente(dominio_activo, svc, tmp_path):
    """CASO C: certbot falla ANTES de _escribir_nginx_conf() — un .conf
    preexistente no debe modificarse ni borrarse en absoluto."""
    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    conf_path.write_text("ORIGINAL CONFIG\n", encoding="utf-8")

    with (
        patch.object(svc, "_nginx_conf_path", return_value=conf_path),
        patch.object(svc, "_ejecutar_certbot", side_effect=SSLIssuanceError("certbot rc=1")),
        pytest.raises(SSLIssuanceError, match="certbot"),
    ):
        svc.emitir(dominio_activo)

    assert conf_path.read_text(encoding="utf-8") == "ORIGINAL CONFIG\n"


@pytest.mark.django_db
def test_D_certbot_falla_antes_de_escribir_conf_inexistente_no_crea_nada(dominio_activo, svc, tmp_path):
    """CASO D: certbot falla ANTES de _escribir_nginx_conf() y el .conf no
    existía — no debe aparecer ningún archivo nuevo en el directorio."""
    def _conf_path(dominio):
        return tmp_path / f"tenant_{dominio}.conf"

    with (
        patch.object(svc, "_nginx_conf_path", side_effect=_conf_path),
        patch.object(svc, "_ejecutar_certbot", side_effect=SSLIssuanceError("certbot rc=1")),
        pytest.raises(SSLIssuanceError, match="certbot"),
    ):
        svc.emitir(dominio_activo)

    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    assert not conf_path.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.django_db
def test_E_fallo_durante_rollback_no_oculta_excepcion_original(dominio_activo, svc, tmp_path):
    """CASO E: si la propia restauración del .conf preexistente falla
    (ej. disco lleno), el SSLIssuanceError final debe seguir describiendo la
    causa RAÍZ del fallo de emisión (nginx en este caso), no el error de
    limpieza — y el fallo de limpieza no debe propagarse en su lugar."""
    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    conf_path.write_text("ORIGINAL CONFIG\n", encoding="utf-8")

    real_escribir_atomico = LetsEncryptSSLIssuanceService._escribir_atomico
    llamadas = {"n": 0}

    def _escribir_atomico_flaky(path, contenido):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            return real_escribir_atomico(path, contenido)  # escritura hacia adelante: real
        raise OSError("disco lleno (simulado) durante el rollback")

    with (
        patch.object(svc, "_nginx_conf_path", return_value=conf_path),
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_escribir_atomico", side_effect=_escribir_atomico_flaky),
        patch.object(
            svc, "_recargar_nginx",
            side_effect=SSLIssuanceError("nginx -t falló: causa raíz"),
        ),
        pytest.raises(SSLIssuanceError, match="nginx -t falló: causa raíz"),
    ):
        svc.emitir(dominio_activo)

    # El rollback falló de verdad (el contenido NO volvió al original) pero
    # la excepción que llegó al llamador sigue siendo la causa raíz (nginx),
    # no un error interno de limpieza.
    assert conf_path.read_text(encoding="utf-8") != "ORIGINAL CONFIG\n"
    dominio_activo.refresh_from_db()
    assert dominio_activo.estado == EmpresaDominio.Estado.ACTIVO


# ── Concurrencia: select_for_update en la transición ACTIVO → SSL_PENDIENTE ───
#
# NOTA (Fase 330): no se implementa un TEST F de "segunda emisión en
# SSL_PENDIENTE no ejecuta certbot" porque esa protección NO se implementó a
# propósito — excluir SSL_PENDIENTE de _ESTADOS_APTOS rompería el reintento
# legítimo tras crash que ya prueba test_emitir_ssl_pendiente_es_estado_valido
# (preexistente). Ver el docstring de LetsEncryptSSLIssuanceService
# ("Concurrencia") para el razonamiento completo.


@pytest.mark.django_db
def test_emitir_usa_select_for_update_para_la_transicion_de_estado(dominio_activo, svc):
    """La transición ACTIVO → SSL_PENDIENTE debe hacerse re-consultando la
    fila con select_for_update(), no confiando en el estado en memoria del
    objeto que recibió el llamador."""
    with (
        patch.object(
            EmpresaDominio.objects, "select_for_update", wraps=EmpresaDominio.objects.select_for_update
        ) as mock_sfu,
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_escribir_nginx_conf"),
        patch.object(svc, "_recargar_nginx"),
        patch.object(LetsEncryptSSLIssuanceService, "_leer_expiracion", return_value=None),
    ):
        svc.emitir(dominio_activo)

    mock_sfu.assert_called_once()


# ── Tests: metadata / permisos en escritura atómica (Fase 331/332) ────────────
#
# Hallazgo de Fase 331, confirmado con una prueba local real (fuera del repo,
# sin tocar /etc/nginx): os.replace() reemplaza el inode completo del
# destino, por lo que el archivo resultante hereda el modo de CREACIÓN del
# temporal, no el del archivo que reemplaza — MODE_BEFORE=0640 se convertía
# en MODE_AFTER=0664. Estos tests fijan la corrección: _escribir_atomico()
# ahora preserva el modo explícitamente.


@pytest.mark.django_db
def test_escribir_atomico_preserva_modo_de_conf_preexistente(dominio_activo, svc, tmp_path):
    """TEST MODE EXISTENTE: un .conf con chmod 0640 debe conservar
    exactamente ese modo tras una escritura atómica exitosa (camino feliz,
    sin fallo posterior) — no el modo por defecto del umask del proceso."""
    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    conf_path.write_text("ORIGINAL CONFIG\n", encoding="utf-8")
    os.chmod(conf_path, 0o640)

    svc._escribir_atomico(conf_path, "NUEVO CONTENIDO\n")

    assert conf_path.read_text(encoding="utf-8") == "NUEVO CONTENIDO\n"
    assert stat.S_IMODE(conf_path.stat().st_mode) == 0o640
    assert list(tmp_path.iterdir()) == [conf_path]  # sin temporales residuales


@pytest.mark.django_db
def test_escribir_atomico_archivo_nuevo_no_impone_modo_artificial(dominio_activo, svc, tmp_path):
    """TEST ARCHIVO NUEVO: si el .conf no existía, no se le impone 0640 ni
    ningún modo artificial — se aplica el modo por defecto que produciría el
    umask actual del proceso (el mismo que Path.write_text() habría usado),
    NO el 0600 fijo que tempfile.mkstemp() aplica por diseño de seguridad."""
    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    assert not conf_path.exists()

    svc._escribir_atomico(conf_path, "CONTENIDO\n")

    assert conf_path.exists()
    assert conf_path.read_text(encoding="utf-8") == "CONTENIDO\n"
    modo_esperado = LetsEncryptSSLIssuanceService._modo_por_defecto_umask()
    assert stat.S_IMODE(conf_path.stat().st_mode) == modo_esperado
    assert stat.S_IMODE(conf_path.stat().st_mode) != 0o600  # no el default de mkstemp
    assert list(tmp_path.iterdir()) == [conf_path]  # sin temporales residuales


@pytest.mark.django_db
def test_rollback_restaura_contenido_y_modo_original(dominio_activo, svc, tmp_path):
    """TEST ROLLBACK + MODE: hay DOS escrituras atómicas en juego (la nueva,
    que sobrescribe, y la de rollback, que restaura) — ambas deben preservar
    el modo 0640 original, no solo el contenido."""
    conf_path = tmp_path / f"tenant_{dominio_activo.dominio}.conf"
    conf_path.write_text("ORIGINAL CONFIG\n", encoding="utf-8")
    os.chmod(conf_path, 0o640)

    with (
        patch.object(svc, "_nginx_conf_path", return_value=conf_path),
        patch.object(svc, "_ejecutar_certbot"),
        patch.object(svc, "_recargar_nginx", side_effect=SSLIssuanceError("nginx -t falló")),
        pytest.raises(SSLIssuanceError),
    ):
        svc.emitir(dominio_activo)

    assert conf_path.read_text(encoding="utf-8") == "ORIGINAL CONFIG\n"
    assert stat.S_IMODE(conf_path.stat().st_mode) == 0o640
    assert list(tmp_path.iterdir()) == [conf_path]  # sin temporales residuales
    dominio_activo.refresh_from_db()
    assert dominio_activo.estado == EmpresaDominio.Estado.ACTIVO


# ── Tests: www condicional (Fase 343 — ADR-004) ───────────────────────────────
#
# dominio_activo tiene incluir_www=True por default del modelo — se usa tal
# cual para los casos "con www" (equivalente al patrón real de MonteAzul).
# Para "sin www" se crea una instancia explícita con incluir_www=False
# (equivalente a un futuro tenant apex-only).


@pytest.fixture
def dominio_activo_sin_www(db, empresa):
    """EmpresaDominio ACTIVO con incluir_www=False (tenant apex-only)."""
    return EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="apexonly.example.cl",
        estado=EmpresaDominio.Estado.ACTIVO,
        ssl_emitido=False,
        incluir_www=False,
    )


@pytest.mark.django_db
def test_get_domains_incluye_www_por_defecto(dominio_activo, svc):
    assert dominio_activo.incluir_www is True
    assert LetsEncryptSSLIssuanceService._get_domains(dominio_activo) == [
        "taller.example.cl",
        "www.taller.example.cl",
    ]


@pytest.mark.django_db
def test_get_domains_sin_www_si_incluir_www_false(dominio_activo_sin_www, svc):
    assert LetsEncryptSSLIssuanceService._get_domains(dominio_activo_sin_www) == [
        "apexonly.example.cl",
    ]


@pytest.mark.django_db
def test_get_domains_no_duplica_www_si_apex_ya_empieza_con_www(db, empresa):
    ed = EmpresaDominio.objects.create(
        empresa=empresa,
        dominio="www.raro.example.cl",
        estado=EmpresaDominio.Estado.ACTIVO,
        incluir_www=True,
    )
    # No debe generar "www.www.raro.example.cl".
    assert LetsEncryptSSLIssuanceService._get_domains(ed) == ["www.raro.example.cl"]


@pytest.mark.django_db
def test_emitir_con_incluir_www_true_genera_server_name_apex_y_www(
    dominio_activo, svc, tmp_path
):
    """CASO I (MonteAzul-like): certbot recibe ambos -d y el .conf real
    generado por _escribir_nginx_conf() (sin mockear) tiene server_name con
    apex + www — igual al patrón ya operando en producción para MonteAzul."""
    with (
        patch.object(svc, "_nginx_conf_path", return_value=tmp_path / "tenant_taller.example.cl.conf"),
        patch("subprocess.run", return_value=_proc(returncode=0)) as mock_run,
        patch.object(svc, "_recargar_nginx"),
        patch.object(LetsEncryptSSLIssuanceService, "_leer_expiracion", return_value=None),
    ):
        svc.emitir(dominio_activo)

    certbot_args = mock_run.call_args_list[0].args[0]
    d_values = [certbot_args[i + 1] for i, a in enumerate(certbot_args) if a == "-d"]
    assert d_values == ["taller.example.cl", "www.taller.example.cl"]

    conf = (tmp_path / "tenant_taller.example.cl.conf").read_text(encoding="utf-8")
    assert "server_name taller.example.cl www.taller.example.cl;" in conf
    # El path del certificado sigue basado SOLO en el apex (certbot usa el
    # primer -d como --cert-name, igual que el cert real de MonteAzul).
    assert "/etc/letsencrypt/live/taller.example.cl/fullchain.pem" in conf
    assert "/etc/letsencrypt/live/taller.example.cl/privkey.pem" in conf
    assert "www.example.cl/fullchain" not in conf

    dominio_activo.refresh_from_db()
    assert dominio_activo.ssl_cert_path == "/etc/letsencrypt/live/taller.example.cl/fullchain.pem"
    assert dominio_activo.ssl_key_path == "/etc/letsencrypt/live/taller.example.cl/privkey.pem"


@pytest.mark.django_db
def test_emitir_con_incluir_www_false_no_incluye_www_en_nada(
    dominio_activo_sin_www, svc, tmp_path
):
    """CASO J (apex-only): un tenant que no quiere/puede www sigue
    funcionando exactamente igual que antes de esta fase."""
    with (
        patch.object(
            svc, "_nginx_conf_path", return_value=tmp_path / "tenant_apexonly.example.cl.conf"
        ),
        patch("subprocess.run", return_value=_proc(returncode=0)) as mock_run,
        patch.object(svc, "_recargar_nginx"),
        patch.object(LetsEncryptSSLIssuanceService, "_leer_expiracion", return_value=None),
    ):
        svc.emitir(dominio_activo_sin_www)

    certbot_args = mock_run.call_args_list[0].args[0]
    d_values = [certbot_args[i + 1] for i, a in enumerate(certbot_args) if a == "-d"]
    assert d_values == ["apexonly.example.cl"]
    assert "www.apexonly.example.cl" not in certbot_args

    conf = (tmp_path / "tenant_apexonly.example.cl.conf").read_text(encoding="utf-8")
    assert "server_name apexonly.example.cl;" in conf
    assert "www.apexonly.example.cl" not in conf


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
        svc._ejecutar_certbot(["taller.example.cl"])

    args = mock_run.call_args[0][0]
    assert args[0] == "certbot"
    assert "taller.example.cl" in args
    assert "--non-interactive" in args
    assert "--agree-tos" in args


def test_ejecutar_certbot_incluye_apex_y_www_como_dos_flags_d(svc):
    """Fase 343: incluir_www debe traducirse en DOS flags -d repetidos, no en
    un solo dominio con comas — certbot exige -d por cada SAN."""
    with patch("subprocess.run", return_value=_proc(returncode=0)) as mock_run:
        svc._ejecutar_certbot(["taller.example.cl", "www.taller.example.cl"])

    args = mock_run.call_args[0][0]
    assert args[0] == "certbot"
    # Exactamente dos pares "-d <dominio>", en el orden apex primero.
    d_indices = [i for i, a in enumerate(args) if a == "-d"]
    assert len(d_indices) == 2
    assert args[d_indices[0] + 1] == "taller.example.cl"
    assert args[d_indices[1] + 1] == "www.taller.example.cl"


def test_ejecutar_certbot_fallo_lanza_ssl_issuance_error(svc):
    with patch("subprocess.run", return_value=_proc(returncode=1, stderr="ACME error")):
        with pytest.raises(SSLIssuanceError, match="certbot falló"):
            svc._ejecutar_certbot(["taller.example.cl"])


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
    assert "proxy_pass http://unix:/run/gunicorn/gunicorn.sock" in conf
    assert "location /static/" in conf
    assert "alias /srv/egarage/staticfiles/" in conf
    assert "location /media/" in conf
    assert "alias /srv/egarage/media/" in conf


def test_nginx_conf_path_usa_prefijo_tenant(svc):
    path = svc._nginx_conf_path("mi-taller.cl")
    assert path.name == "tenant_mi-taller.cl.conf"


# ── Tests: SSLIssuanceService es ABC ─────────────────────────────────────────


def test_ssl_issuance_service_no_es_instanciable_directamente():
    with pytest.raises(TypeError):
        SSLIssuanceService()
