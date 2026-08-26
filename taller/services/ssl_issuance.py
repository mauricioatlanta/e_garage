"""
SSLIssuanceService — Fase 3: emisión y revocación de certificados SSL via Let's Encrypt.

Jerarquía:
    SSLIssuanceService                 (ABC — interfaz)
    └── LetsEncryptSSLIssuanceService  (implementación oficial: certbot + Nginx por tenant)

No modifica:
    domain_service.py           (CRUD / ciclo de vida)
    domain_resolver_service.py  (caché / middleware)
    domain_verification.py      (verificación DNS)
    host_tenant.py              (routing)
    empresa_dominio.py          (modelo)
"""

import logging
import os
import stat
import subprocess
import tempfile
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path

from django.db import transaction

from taller.models.empresa_dominio import EmpresaDominio

logger = logging.getLogger(__name__)

_NGINX_CONF_TEMPLATE = """\
# Generado por eGarage / LetsEncryptSSLIssuanceService — no editar manualmente.
server {{
    listen 80;
    server_name {domain};
    location /.well-known/acme-challenge/ {{ root /var/www/certbot; }}
    location / {{ return 301 https://$host$request_uri; }}
}}
server {{
    listen 443 ssl http2;
    server_name {domain};
    ssl_certificate     /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    location / {{
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Host  $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }}
}}
"""


class SSLIssuanceError(Exception):
    """Error durante la emisión o revocación de un certificado SSL."""


class SSLIssuanceService(ABC):
    """Interfaz para servicios de emisión de certificados SSL por tenant."""

    @abstractmethod
    def emitir(self, empresa_dominio: EmpresaDominio) -> None:
        """
        Emite un certificado SSL para el dominio del tenant.

        Transiciona: ACTIVO/SSL_PENDIENTE → SSL_PENDIENTE (durante certbot) → ACTIVO.
        Actualiza ssl_cert_path, ssl_key_path, ssl_expira_en, ssl_emitido=True.

        Raises:
            SSLIssuanceError: si certbot o nginx fallan.
            ValueError: si el dominio no está en un estado apto para recibir SSL.
        """

    @abstractmethod
    def revocar(self, empresa_dominio: EmpresaDominio) -> None:
        """
        Revoca el certificado SSL y elimina la configuración Nginx del tenant.

        Limpia ssl_cert_path, ssl_key_path, ssl_expira_en y ssl_emitido=False.
        No falla si el archivo de conf o el cert ya no existen en disco.
        """


class LetsEncryptSSLIssuanceService(SSLIssuanceService):
    """
    Emite certificados via certbot (webroot) y genera bloques Nginx por tenant.

    Requisitos de infraestructura:
        - certbot instalado y accesible en PATH
        - /var/www/certbot existe (raíz para http-01 challenges)
        - Nginx instalado; configuración en /etc/nginx/sites-enabled/
        - El proceso tiene privilegios para escribir en NGINX_CONF_DIR y
          ejecutar certbot, nginx -t y systemctl reload nginx

    Precondición no resuelta por este servicio (chicken-and-egg conocido):
        _ejecutar_certbot() usa el plugin --webroot y se ejecuta ANTES de que
        _escribir_nginx_conf() genere el bloque Nginx del tenant. Para que el
        challenge HTTP-01 de un dominio nuevo (sin bloque Nginx propio
        todavía) tenga dónde responder, debe existir de antemano un bloque
        Nginx (default_server o catch-all) que sirva
        /.well-known/acme-challenge/ desde CERTBOT_WEBROOT para CUALQUIER
        Host, no solo los dominios ya configurados. Esa pieza vive en
        /etc/nginx (fuera de este repo) y no está confirmada en producción —
        ver ADR-003 §11 Paso 1c. emitir() no la crea ni la valida; si no
        existe, certbot fallará y este método revertirá el estado a ACTIVO
        con ssl_emitido=False, sin dejar el tenant en un estado inconsistente
        (ver limpieza de conf huérfano más abajo).

    Concurrencia (Fase 329/330):
        La transición ACTIVO → SSL_PENDIENTE se hace con
        select_for_update() dentro de una transacción corta, para que dos
        llamadas verdaderamente simultáneas partiendo de ACTIVO no puedan
        ambas ganar la carrera y lanzar certbot dos veces para el mismo
        dominio. La transacción NO envuelve certbot/nginx (subprocess.run
        externo, potencialmente lento) — solo el chequeo+flip de estado.

        Gap conocido y NO cerrado a propósito: SSL_PENDIENTE sigue siendo un
        estado "apto" para (re)iniciar emitir() — es el contrato preexistente
        que permite reintentar tras un crash a mitad de emisión (ver
        test_emitir_ssl_pendiente_es_estado_valido, ya existente antes de
        esta fase). Excluir SSL_PENDIENTE rompería ese reintento legítimo de
        recuperación; por eso NO se excluyó de _ESTADOS_APTOS aquí. Esto
        significa que dos llamadas mientras el dominio YA está en
        SSL_PENDIENTE (una legítima recuperación y otra concurrente, o dos
        reintentos concurrentes) siguen pudiendo correr certbot dos veces —
        ese caso específico requeriría una decisión de producto (¿cuánto
        tiempo es "demasiado" en SSL_PENDIENTE para considerarlo huérfano?)
        que excede el alcance de esta corrección.

        select_for_update() no bloquea filas en SQLite (los tests locales
        corren sobre SQLite en memoria) — la exclusión mutua real solo se
        valida contra PostgreSQL en producción.
    """

    NGINX_CONF_DIR  = Path("/etc/nginx/sites-enabled")
    CERTBOT_WEBROOT = Path("/var/www/certbot")
    LE_LIVE_DIR     = Path("/etc/letsencrypt/live")

    _ESTADOS_APTOS = (
        EmpresaDominio.Estado.ACTIVO,
        EmpresaDominio.Estado.SSL_PENDIENTE,
    )

    # ── Interfaz pública ──────────────────────────────────────────────────

    def emitir(self, empresa_dominio: EmpresaDominio) -> None:
        dominio = empresa_dominio.dominio

        with transaction.atomic():
            locked = EmpresaDominio.objects.select_for_update().get(pk=empresa_dominio.pk)
            if locked.estado not in self._ESTADOS_APTOS:
                raise ValueError(
                    f"El dominio '{locked.dominio}' está en estado "
                    f"'{locked.get_estado_display()}' y no puede recibir un certificado."
                )
            locked.estado = EmpresaDominio.Estado.SSL_PENDIENTE
            locked.save(update_fields=["estado", "actualizado_en"])
        empresa_dominio.estado = locked.estado

        conf_path = self._nginx_conf_path(dominio)
        conf_existia_antes = conf_path.exists()
        contenido_original: str | None = None
        if conf_existia_antes:
            try:
                contenido_original = conf_path.read_text(encoding="utf-8")
            except OSError as exc:
                # No podemos garantizar un rollback seguro sin el contenido
                # original: abortar ANTES de tocar certbot/nginx, sin dejar
                # el dominio a medio camino en SSL_PENDIENTE.
                empresa_dominio.estado = EmpresaDominio.Estado.ACTIVO
                empresa_dominio.save(update_fields=["estado", "actualizado_en"])
                raise SSLIssuanceError(
                    f"No se pudo leer la configuración Nginx existente de {dominio} "
                    f"antes de modificarla; abortando por seguridad: {exc}"
                ) from exc

        try:
            self._ejecutar_certbot(dominio)
            self._escribir_nginx_conf(dominio)
            self._recargar_nginx()
        except Exception as exc:
            logger.error("SSLIssuanceService.emitir: fallo para %s — %s", dominio, exc)
            self._revertir_conf_nginx(conf_path, conf_existia_antes, contenido_original)
            empresa_dominio.estado = EmpresaDominio.Estado.ACTIVO
            empresa_dominio.save(update_fields=["estado", "actualizado_en"])
            raise SSLIssuanceError(f"No se pudo emitir SSL para {dominio}: {exc}") from exc

        empresa_dominio.ssl_cert_path = str(self.LE_LIVE_DIR / dominio / "fullchain.pem")
        empresa_dominio.ssl_key_path  = str(self.LE_LIVE_DIR / dominio / "privkey.pem")
        empresa_dominio.ssl_expira_en = self._leer_expiracion(empresa_dominio.ssl_cert_path)
        empresa_dominio.ssl_emitido   = True
        empresa_dominio.estado        = EmpresaDominio.Estado.ACTIVO
        empresa_dominio.save(update_fields=[
            "ssl_cert_path", "ssl_key_path", "ssl_expira_en",
            "ssl_emitido", "estado", "actualizado_en",
        ])

        logger.info(
            "SSLIssuanceService.emitir: OK para %s (expira %s)",
            dominio,
            empresa_dominio.ssl_expira_en,
        )

    def revocar(self, empresa_dominio: EmpresaDominio) -> None:
        dominio   = empresa_dominio.dominio
        conf_path = self._nginx_conf_path(dominio)

        if conf_path.exists():
            conf_path.unlink()
            logger.info("SSLIssuanceService.revocar: eliminado %s", conf_path)
            try:
                self._recargar_nginx()
            except SSLIssuanceError:
                logger.warning(
                    "SSLIssuanceService.revocar: nginx reload falló tras eliminar conf %s",
                    dominio,
                )

        if empresa_dominio.ssl_emitido:
            try:
                self._ejecutar_certbot_delete(dominio)
            except Exception as exc:
                logger.error(
                    "SSLIssuanceService.revocar: certbot delete falló para %s — %s",
                    dominio,
                    exc,
                )

        empresa_dominio.ssl_emitido   = False
        empresa_dominio.ssl_cert_path = ""
        empresa_dominio.ssl_key_path  = ""
        empresa_dominio.ssl_expira_en = None
        empresa_dominio.save(update_fields=[
            "ssl_emitido", "ssl_cert_path", "ssl_key_path",
            "ssl_expira_en", "actualizado_en",
        ])
        logger.info("SSLIssuanceService.revocar: OK para %s", dominio)

    # ── Internos ──────────────────────────────────────────────────────────

    def _nginx_conf_path(self, dominio: str) -> Path:
        return self.NGINX_CONF_DIR / f"tenant_{dominio}.conf"

    def _ejecutar_certbot(self, dominio: str) -> None:
        resultado = subprocess.run(
            [
                "certbot", "certonly",
                "--webroot",
                "-w", str(self.CERTBOT_WEBROOT),
                "-d", dominio,
                "--non-interactive",
                "--agree-tos",
                "--email", "support@egarage.cl",
            ],
            capture_output=True,
            text=True,
        )
        if resultado.returncode != 0:
            raise SSLIssuanceError(
                f"certbot falló (rc={resultado.returncode}): {resultado.stderr.strip()}"
            )

    def _ejecutar_certbot_delete(self, dominio: str) -> None:
        resultado = subprocess.run(
            ["certbot", "delete", "--cert-name", dominio, "--non-interactive"],
            capture_output=True,
            text=True,
        )
        if resultado.returncode != 0:
            raise SSLIssuanceError(
                f"certbot delete falló (rc={resultado.returncode}): {resultado.stderr.strip()}"
            )

    def _escribir_nginx_conf(self, dominio: str) -> None:
        conf_path = self._nginx_conf_path(dominio)
        self._escribir_atomico(conf_path, _NGINX_CONF_TEMPLATE.format(domain=dominio))
        logger.info("SSLIssuanceService: conf Nginx escrita en %s", conf_path)

    @staticmethod
    def _modo_por_defecto_umask() -> int:
        """Modo que produciría escribir un archivo NUEVO bajo el umask actual
        del proceso — el mismo comportamiento que Path.write_text()/open().

        tempfile.mkstemp() ignora el umask por diseño (siempre crea con 0600
        por seguridad); sin este ajuste, un .conf nuevo quedaría con permisos
        más restrictivos de los que tenía antes de introducir la escritura
        atómica, lo que podría impedir que el worker de Nginx (usuario sin
        privilegios) lo lea.
        """
        umask_actual = os.umask(0)
        os.umask(umask_actual)
        return 0o666 & ~umask_actual

    @classmethod
    def _escribir_atomico(cls, path: Path, contenido: str) -> None:
        """Escribe *contenido* en *path* de forma atómica, preservando modo
        (y, en la medida de lo posible, propietario/grupo) si *path* ya
        existía.

        Usa tempfile.mkstemp() en el MISMO directorio (mismo filesystem,
        requisito para que os.replace() sea atómico) con nombre único
        garantizado por el sistema operativo, y reemplaza con os.replace().
        Evita que *path* quede parcialmente escrito si el proceso se
        interrumpe a mitad de la escritura (crash, OOM-kill, etc.).

        os.replace() sustituye el inode completo del destino por el del
        temporal: sin preservación explícita, un archivo PREEXISTENTE perdería
        su modo/propietario originales (heredaría el modo por defecto del
        proceso que escribió el temporal). Preservar el modo es obligatorio;
        preservar propietario/grupo es best-effort — un chown() sin
        privilegios NO debe hacer fallar una escritura por lo demás legítima.
        """
        stat_original = None
        if path.exists():
            try:
                stat_original = path.stat()
            except OSError as exc:
                logger.warning(
                    "SSLIssuanceService._escribir_atomico: no se pudo leer "
                    "metadata previa de %s, se preservará solo el modo por "
                    "defecto del proceso — %s",
                    path, exc,
                )

        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(contenido)

            modo_destino = (
                stat.S_IMODE(stat_original.st_mode)
                if stat_original is not None
                else cls._modo_por_defecto_umask()
            )
            try:
                os.chmod(tmp_path, modo_destino)
            except OSError as exc:
                logger.warning(
                    "SSLIssuanceService._escribir_atomico: no se pudo aplicar "
                    "el modo %o a %s — %s", modo_destino, path, exc,
                )

            if stat_original is not None:
                tmp_stat = os.stat(tmp_path)
                if (tmp_stat.st_uid, tmp_stat.st_gid) != (
                    stat_original.st_uid, stat_original.st_gid,
                ):
                    try:
                        os.chown(tmp_path, stat_original.st_uid, stat_original.st_gid)
                    except (PermissionError, OSError) as exc:
                        logger.warning(
                            "SSLIssuanceService._escribir_atomico: no se pudo "
                            "preservar propietario/grupo (uid=%s gid=%s) de %s "
                            "— %s",
                            stat_original.st_uid, stat_original.st_gid, path, exc,
                        )

            os.replace(tmp_path, path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def _revertir_conf_nginx(
        self,
        conf_path: Path,
        existia_antes: bool,
        contenido_original: str | None,
    ) -> None:
        """Deja el .conf del tenant como estaba antes de una emisión fallida.

        - No existía antes: elimina el archivo que ESTA ejecución creó (evita
          un huérfano que rompa el próximo `nginx -t`/reload de otro tenant).
        - Ya existía: restaura su contenido ORIGINAL byte a byte —
          _escribir_nginx_conf() pudo haberlo sobrescrito con la plantilla
          nueva antes de que `nginx -t`/reload fallara; no basta con "no
          borrarlo", el contenido debe volver a ser el de antes.

        Nunca propaga una excepción: un fallo durante el rollback se
        registra, pero la excepción real (certbot/nginx) es la que debe
        llegar al llamador — no debe quedar oculta detrás de un error de
        limpieza.
        """
        try:
            if not existia_antes:
                if conf_path.exists():
                    conf_path.unlink()
                    logger.info(
                        "SSLIssuanceService.emitir: conf huérfano eliminado tras fallo (%s)",
                        conf_path,
                    )
            elif contenido_original is not None:
                self._escribir_atomico(conf_path, contenido_original)
                logger.info(
                    "SSLIssuanceService.emitir: conf preexistente restaurada a su "
                    "contenido original tras fallo (%s)",
                    conf_path,
                )
        except OSError as rollback_exc:
            logger.error(
                "SSLIssuanceService.emitir: fallo al revertir conf Nginx de %s "
                "tras un error de emisión — %s",
                conf_path,
                rollback_exc,
            )

    def _recargar_nginx(self) -> None:
        test = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
        if test.returncode != 0:
            raise SSLIssuanceError(f"nginx -t falló: {test.stderr.strip()}")
        reload_result = subprocess.run(
            ["systemctl", "reload", "nginx"],
            capture_output=True,
            text=True,
        )
        if reload_result.returncode != 0:
            raise SSLIssuanceError(
                f"systemctl reload nginx falló (rc={reload_result.returncode}): "
                f"{reload_result.stderr.strip()}"
            )

    @staticmethod
    def _leer_expiracion(cert_path: str) -> date | None:
        """Lee la fecha de expiración del cert usando openssl. Devuelve None si falla."""
        try:
            resultado = subprocess.run(
                ["openssl", "x509", "-enddate", "-noout", "-in", cert_path],
                capture_output=True,
                text=True,
            )
            if resultado.returncode != 0:
                logger.warning("_leer_expiracion: openssl falló para %s", cert_path)
                return None
            # Output: "notAfter=Jan 10 12:00:00 2026 GMT"
            raw = resultado.stdout.strip().split("=", 1)[1].strip()
            return datetime.strptime(raw, "%b %d %H:%M:%S %Y %Z").date()
        except Exception as exc:
            logger.warning("_leer_expiracion: no pudo parsear para %s — %s", cert_path, exc)
            return None
