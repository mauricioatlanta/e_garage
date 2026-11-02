"""
sync_ssl_expiry — sincroniza la fecha de expiración SSL de cada dominio activo
leyéndola directamente del certificado en disco via openssl.

Uso:
    # Actualizar todos los dominios con ssl_emitido=True
    python manage.py sync_ssl_expiry

    # Alertar dominios que expiran en menos de N días (default: 14)
    python manage.py sync_ssl_expiry --alert-days 20

    # Solo reportar; no escribir en DB
    python manage.py sync_ssl_expiry --dry-run

Casos de uso típicos:
    - Tarea cron post-renovación: sync_ssl_expiry actualiza ssl_expira_en tras
      que certbot renueva el cert automáticamente.
    - Monitoreo: cron diario que alerta cuando un cert expira pronto.
"""

import logging
import subprocess
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand

from taller.models.empresa_dominio import EmpresaDominio

logger = logging.getLogger(__name__)

_DEFAULT_ALERT_DAYS = 14


class Command(BaseCommand):
    help = "Sincroniza ssl_expira_en desde disco y alerta certs próximos a vencer."

    def add_arguments(self, parser):
        parser.add_argument(
            "--alert-days",
            type=int,
            default=_DEFAULT_ALERT_DAYS,
            metavar="N",
            help=f"Alertar dominios que expiran en menos de N días (default: {_DEFAULT_ALERT_DAYS}).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="No escribir en DB; solo reportar cambios que se harían.",
        )

    def handle(self, *args, **options):
        alert_days = options["alert_days"]
        dry_run    = options["dry_run"]

        dominios = list(
            EmpresaDominio.objects.filter(
                ssl_emitido=True,
                estado=EmpresaDominio.Estado.ACTIVO,
            ).exclude(ssl_cert_path="")
        )

        if not dominios:
            self.stdout.write(self.style.WARNING("No hay dominios con SSL emitido y activos."))
            return

        hoy          = date.today()
        umbral       = hoy + timedelta(days=alert_days)
        actualizados = 0
        alertas      = 0

        for ed in dominios:
            nueva_expiracion = _leer_expiracion(ed.ssl_cert_path)

            if nueva_expiracion is None:
                self.stderr.write(
                    self.style.ERROR(
                        f"[ERROR] {ed.dominio}: no pudo leer expiración desde {ed.ssl_cert_path}"
                    )
                )
                continue

            if nueva_expiracion != ed.ssl_expira_en:
                if dry_run:
                    self.stdout.write(
                        f"[DRY-RUN] {ed.dominio}: {ed.ssl_expira_en} → {nueva_expiracion}"
                    )
                else:
                    ed.ssl_expira_en = nueva_expiracion
                    ed.save(update_fields=["ssl_expira_en", "actualizado_en"])
                    self.stdout.write(
                        f"[SYNC]  {ed.dominio}: ssl_expira_en → {nueva_expiracion}"
                    )
                actualizados += 1

            expiracion_efectiva = nueva_expiracion
            if expiracion_efectiva <= umbral:
                dias_restantes = (expiracion_efectiva - hoy).days
                self.stderr.write(
                    self.style.WARNING(
                        f"[ALERTA] {ed.dominio}: expira en {dias_restantes} días ({expiracion_efectiva})"
                    )
                )
                logger.warning(
                    "sync_ssl_expiry: %s expira en %d días (%s)",
                    ed.dominio,
                    dias_restantes,
                    expiracion_efectiva,
                )
                alertas += 1

        dry_label = " [dry-run]" if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"sync_ssl_expiry{dry_label}: {actualizados} actualizados, {alertas} alertas."
            )
        )


def _leer_expiracion(cert_path: str) -> date | None:
    """Lee la fecha de expiración del cert vía openssl. Devuelve None si falla."""
    try:
        resultado = subprocess.run(
            ["openssl", "x509", "-enddate", "-noout", "-in", cert_path],
            capture_output=True,
            text=True,
        )
        if resultado.returncode != 0:
            return None
        # Output: "notAfter=Jan 10 12:00:00 2026 GMT"
        raw = resultado.stdout.strip().split("=", 1)[1].strip()
        return datetime.strptime(raw, "%b %d %H:%M:%S %Y %Z").date()
    except Exception as exc:
        logger.warning("_leer_expiracion: error leyendo %s — %s", cert_path, exc)
        return None
