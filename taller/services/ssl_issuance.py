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
import subprocess
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path

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
        if empresa_dominio.estado not in self._ESTADOS_APTOS:
            raise ValueError(
                f"El dominio '{empresa_dominio.dominio}' está en estado "
                f"'{empresa_dominio.get_estado_display()}' y no puede recibir un certificado."
            )

        dominio = empresa_dominio.dominio

        empresa_dominio.estado = EmpresaDominio.Estado.SSL_PENDIENTE
        empresa_dominio.save(update_fields=["estado", "actualizado_en"])

        try:
            self._ejecutar_certbot(dominio)
            self._escribir_nginx_conf(dominio)
            self._recargar_nginx()
        except Exception as exc:
            logger.error("SSLIssuanceService.emitir: fallo para %s — %s", dominio, exc)
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
        conf_path.write_text(_NGINX_CONF_TEMPLATE.format(domain=dominio), encoding="utf-8")
        logger.info("SSLIssuanceService: conf Nginx escrita en %s", conf_path)

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
