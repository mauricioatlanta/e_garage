"""
DomainVerificationService — Fase 2: verificación DNS del registro TXT.

Responsabilidad única: consultar el registro TXT _egarage-verify.<dominio>
y confirmar que su valor coincide con el token del tenant. Transiciona el
estado del EmpresaDominio en consecuencia.

No modifica:
    domain_service.py        (CRUD / ciclo de vida)
    domain_resolver_service.py (caché / middleware)
    host_tenant.py           (routing)
    empresa_dominio.py       (modelo)
"""

import logging
from dataclasses import dataclass, field

from django.utils import timezone

from taller.models.empresa_dominio import EmpresaDominio

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Resultado inmutable de una verificación DNS."""

    success:  bool
    dominio:  str
    txt_name: str           # nombre del registro TXT consultado
    expected: str           # valor esperado en el registro
    found:    list[str] = field(default_factory=list)   # valores encontrados
    error:    str = ""      # vacío en éxito; descripción del error en fallo


class DomainVerificationService:
    """
    Verifica que _egarage-verify.<dominio> TXT existe y coincide con el token.

    Uso típico (management command o tarea asíncrona):
        result = DomainVerificationService.verificar(empresa_dominio)
        if result.success:
            notificar_tenant(empresa_dominio.empresa)
    """

    @classmethod
    def verificar(cls, empresa_dominio: EmpresaDominio) -> VerificationResult:
        """
        Consulta DNS y persiste el resultado en una sola escritura.

        Raises:
            ValueError: si el dominio no está en un estado verificable
                        (PENDIENTE, VERIFICANDO o ERROR_DNS).
        """
        if not empresa_dominio.puede_verificarse:
            raise ValueError(
                f"El dominio '{empresa_dominio.dominio}' está en estado "
                f"'{empresa_dominio.get_estado_display()}' y no puede verificarse."
            )

        txt_name = empresa_dominio.get_txt_record_name()
        expected = empresa_dominio.get_txt_record_value()

        found: list[str] = []
        error_msg = ""
        try:
            found = cls._consultar_txt(txt_name)
        except Exception as exc:
            error_msg = str(exc)
            logger.warning(
                "DomainVerificationService: excepción DNS para %s — %s",
                txt_name,
                exc,
            )

        success = cls._coincide(found, expected)

        # Una sola escritura con todos los campos actualizados.
        now = timezone.now()
        empresa_dominio.ultimo_check_dns      = now
        empresa_dominio.intentos_verificacion = (empresa_dominio.intentos_verificacion or 0) + 1

        if success:
            empresa_dominio.estado        = EmpresaDominio.Estado.ACTIVO
            empresa_dominio.verificado_en = now
            update_fields = [
                "estado", "verificado_en", "ultimo_check_dns",
                "intentos_verificacion", "actualizado_en",
            ]
        else:
            empresa_dominio.estado = EmpresaDominio.Estado.ERROR_DNS
            update_fields = [
                "estado", "ultimo_check_dns",
                "intentos_verificacion", "actualizado_en",
            ]

        empresa_dominio.save(update_fields=update_fields)

        logger.info(
            "DomainVerificationService.verificar: dominio=%s success=%s intentos=%d",
            empresa_dominio.dominio,
            success,
            empresa_dominio.intentos_verificacion,
        )

        return VerificationResult(
            success=success,
            dominio=empresa_dominio.dominio,
            txt_name=txt_name,
            expected=expected,
            found=found,
            error=error_msg,
        )

    # ── Internos ──────────────────────────────────────────────────────────────

    @classmethod
    def _consultar_txt(cls, nombre: str) -> list[str]:
        """
        Retorna todos los valores TXT del registro *nombre*.

        NXDOMAIN / NoAnswer / NoNameservers → lista vacía (sin TXT).
        Timeout / otros errores → re-lanza para que verificar() los registre.
        """
        try:
            import dns.exception
            import dns.resolver
        except ImportError as exc:
            raise ImportError(
                "dnspython no está instalado. Añade 'dnspython>=2.6.0' a requirements.txt."
            ) from exc

        try:
            answers = dns.resolver.resolve(nombre, "TXT")
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return []
        except dns.exception.Timeout as exc:
            raise TimeoutError(f"Timeout al consultar {nombre}") from exc
        except dns.exception.DNSException as exc:
            raise RuntimeError(f"Error DNS consultando {nombre}: {exc}") from exc

        result = []
        for rdata in answers:
            for raw in rdata.strings:
                try:
                    result.append(raw.decode("utf-8"))
                except (UnicodeDecodeError, AttributeError):
                    result.append(raw.decode("latin-1", errors="replace"))
        return result

    @staticmethod
    def _coincide(registros: list[str], valor_esperado: str) -> bool:
        """True si alguno de los registros TXT encontrados coincide exactamente."""
        return valor_esperado in registros
