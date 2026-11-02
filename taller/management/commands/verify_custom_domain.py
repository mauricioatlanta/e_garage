"""
verify_custom_domain — verifica el registro TXT de dominios personalizados
y, si la verificación es exitosa, emite el certificado SSL via Let's Encrypt.

Uso:
    # Verificar un dominio concreto
    python manage.py verify_custom_domain --dominio taller.midominio.cl

    # Verificar todos los dominios pendientes/en error
    python manage.py verify_custom_domain --all

    # Solo verificar DNS, no emitir SSL aunque pase
    python manage.py verify_custom_domain --all --skip-ssl
"""

import logging

from django.core.management.base import BaseCommand, CommandError

from taller.models.empresa_dominio import EmpresaDominio
from taller.services.domain_verification import DomainVerificationService
from taller.services.ssl_issuance import LetsEncryptSSLIssuanceService, SSLIssuanceError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Verifica el TXT DNS de dominios personalizados y emite SSL si pasa."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--dominio",
            metavar="FQDN",
            help="FQDN exacto del dominio a verificar.",
        )
        group.add_argument(
            "--all",
            action="store_true",
            dest="all_dominios",
            help="Verificar todos los dominios en estado PENDIENTE, VERIFICANDO o ERROR_DNS.",
        )
        parser.add_argument(
            "--skip-ssl",
            action="store_true",
            default=False,
            help="No emitir certificado SSL aunque la verificación DNS pase.",
        )

    def handle(self, *args, **options):
        skip_ssl   = options["skip_ssl"]
        ssl_service = LetsEncryptSSLIssuanceService()

        if options["dominio"]:
            dominios = self._obtener_dominio_unico(options["dominio"])
        else:
            dominios = list(
                EmpresaDominio.objects.filter(
                    estado__in=[
                        EmpresaDominio.Estado.PENDIENTE,
                        EmpresaDominio.Estado.VERIFICANDO,
                        EmpresaDominio.Estado.ERROR_DNS,
                    ]
                ).select_related("empresa")
            )
            if not dominios:
                self.stdout.write(self.style.WARNING("No hay dominios en estado verificable."))
                return

        ok = err = 0
        for ed in dominios:
            resultado = self._verificar(ed)
            if resultado is None:
                err += 1
                continue

            if resultado.success and not skip_ssl:
                self._emitir_ssl(ed, ssl_service)

            if resultado.success:
                ok += 1
            else:
                err += 1

        self.stdout.write(
            self.style.SUCCESS(f"Completado: {ok} OK, {err} con error.")
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _obtener_dominio_unico(self, fqdn: str) -> list[EmpresaDominio]:
        try:
            ed = EmpresaDominio.objects.select_related("empresa").get(dominio=fqdn)
        except EmpresaDominio.DoesNotExist:
            raise CommandError(f"No existe ningún dominio registrado con FQDN '{fqdn}'.")
        return [ed]

    def _verificar(self, ed: EmpresaDominio):
        try:
            resultado = DomainVerificationService.verificar(ed)
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(f"[SKIP] {ed.dominio}: {exc}"))
            return None
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"[ERROR] {ed.dominio}: {exc}"))
            logger.exception("verify_custom_domain: excepción no esperada para %s", ed.dominio)
            return None

        if resultado.success:
            self.stdout.write(self.style.SUCCESS(f"[OK]    {ed.dominio} — TXT verificado."))
        else:
            msg = f"[FAIL]  {ed.dominio} — TXT no coincide. Encontrado: {resultado.found or '[]'}"
            if resultado.error:
                msg += f" | Error: {resultado.error}"
            self.stdout.write(self.style.WARNING(msg))

        return resultado

    def _emitir_ssl(self, ed: EmpresaDominio, ssl_service: LetsEncryptSSLIssuanceService) -> None:
        if ed.ssl_emitido:
            self.stdout.write(f"        {ed.dominio} — SSL ya emitido, saltando.")
            return
        try:
            ssl_service.emitir(ed)
            self.stdout.write(
                self.style.SUCCESS(f"        {ed.dominio} — SSL emitido (expira {ed.ssl_expira_en}).")
            )
        except SSLIssuanceError as exc:
            self.stderr.write(self.style.ERROR(f"        {ed.dominio} — fallo SSL: {exc}"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"        {ed.dominio} — error inesperado SSL: {exc}"))
            logger.exception("verify_custom_domain: excepción SSL para %s", ed.dominio)
