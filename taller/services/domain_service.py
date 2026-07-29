"""
DomainService — operaciones de modelo sobre EmpresaDominio.

Fase 1: solo operaciones sobre el modelo (sin DNS, sin SSL, sin Nginx).
Fase 2: añadir DomainVerificationService (DNS lookup).
Fase 3: añadir SSLIssuanceService (certbot).
"""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from taller.models.empresa_dominio import EmpresaDominio

logger = logging.getLogger(__name__)


class DomainService:
    """Operaciones sobre dominios personalizados de tenants."""

    @classmethod
    @transaction.atomic
    def registrar(cls, empresa, dominio_raw: str, creado_por=None) -> EmpresaDominio:
        """
        Crea un nuevo EmpresaDominio en estado PENDIENTE.

        Valida:
          - Formato del dominio (delegado a EmpresaDominio.clean).
          - Que el dominio no esté ya registrado por otro tenant.
          - Que la empresa no tenga ya un dominio ACTIVO.

        Raises:
          ValidationError: si el dominio es inválido o ya existe.
        """
        dominio = (dominio_raw or "").strip().lower()

        # Verificar duplicado antes de llamar a clean() para un mensaje más claro.
        if EmpresaDominio.objects.filter(dominio=dominio).exists():
            raise ValidationError(
                {"dominio": f"El dominio '{dominio}' ya está registrado en eGarage."}
            )

        ed = EmpresaDominio(
            empresa=empresa,
            dominio=dominio,
            creado_por=creado_por,
        )
        ed.full_clean()  # ejecuta clean() + validaciones de campo
        ed.save()

        logger.info(
            "DomainService.registrar: empresa_id=%s dominio=%s",
            empresa.pk,
            dominio,
        )
        return ed

    @classmethod
    @transaction.atomic
    def suspender(cls, empresa_dominio: EmpresaDominio) -> None:
        """
        Suspende un dominio activo.

        Invalida el cache de resolución si está disponible.
        """
        if empresa_dominio.estado == EmpresaDominio.Estado.SUSPENDIDO:
            return  # idempotente

        empresa_dominio.suspender()
        cls._invalidar_cache(empresa_dominio.dominio)

        logger.info(
            "DomainService.suspender: empresa_id=%s dominio=%s",
            empresa_dominio.empresa_id,
            empresa_dominio.dominio,
        )

    @classmethod
    @transaction.atomic
    def reactivar(cls, empresa_dominio: EmpresaDominio) -> None:
        """
        Reactiva un dominio SUSPENDIDO transicionando a PENDIENTE.

        Invalida la caché de resolución para que el próximo request
        no sirva el resultado cacheado (miss negativo o dominio suspendido).
        """
        if empresa_dominio.estado != EmpresaDominio.Estado.SUSPENDIDO:
            return  # idempotente

        empresa_dominio.estado = EmpresaDominio.Estado.PENDIENTE
        empresa_dominio.save(update_fields=["estado", "actualizado_en"])
        cls._invalidar_cache(empresa_dominio.dominio)

        logger.info(
            "DomainService.reactivar: empresa_id=%s dominio=%s",
            empresa_dominio.empresa_id,
            empresa_dominio.dominio,
        )

    @classmethod
    @transaction.atomic
    def preparar_verificacion(cls, empresa_dominio: EmpresaDominio) -> None:
        """
        Transiciona el dominio a VERIFICANDO.

        Llama al estado de verificación para que la UI pueda mostrar
        el progreso. La verificación DNS real ocurre en Fase 2.
        """
        empresa_dominio.iniciar_verificacion()

        logger.info(
            "DomainService.preparar_verificacion: empresa_id=%s dominio=%s",
            empresa_dominio.empresa_id,
            empresa_dominio.dominio,
        )

    @classmethod
    def get_activo_para_empresa(cls, empresa) -> "EmpresaDominio | None":
        """
        Devuelve el dominio ACTIVO de la empresa, o None si no tiene.
        """
        return (
            EmpresaDominio.objects.filter(
                empresa=empresa,
                estado=EmpresaDominio.Estado.ACTIVO,
            )
            .select_related("empresa")
            .first()
        )

    @classmethod
    def listar_para_empresa(cls, empresa):
        """
        Lista todos los dominios de la empresa ordenados por creación.
        """
        return EmpresaDominio.objects.filter(empresa=empresa).order_by("-creado_en")

    # ── Helpers privados ──────────────────────────────────────────────────

    @staticmethod
    def _invalidar_cache(dominio: str) -> None:
        """Elimina la entrada de caché delegando a DomainResolverService (fuente única de la clave)."""
        try:
            from taller.services.domain_resolver_service import DomainResolverService
            DomainResolverService.invalidate_cache(dominio)
        except Exception as exc:
            # No propagar: el caché puede no estar disponible en tests.
            logger.debug("_invalidar_cache: %s — %s", dominio, exc)
