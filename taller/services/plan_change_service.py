import logging
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.subscription_change import SubscriptionChange
from taller.models.suscripcion_transaccion import SuscripcionTransaccion
from taller.models.team_member import TeamMember
from taller.utils.plan_catalog import (
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    get_plan_price,
)

logger = logging.getLogger(__name__)


class PlanLimitValidation:
    """Valida límites de usuarios por plan."""

    LIMITES_PLANES = {
        # Nombres de negocio (usados en UI y nuevos flows)
        "express": 1,
        "taller": 4,
        "pro": 10,
        # Códigos internos canónicos (plan_catalog.py)
        "entry": 1,
        "growth": 4,
        "business": 10,
        # Fallbacks
        "trial": 1,
        "basic": 1,
        "premium": 4,
        "enterprise": 10,
    }

    @classmethod
    def get_count(cls, empresa: Empresa) -> int:
        """Cuenta usuarios activos (owner incluido, ya es TeamMember con rol=Owner)."""
        return TeamMember.objects.filter(empresa=empresa, is_active=True).count()

    @classmethod
    def can_add_user(cls, empresa: Empresa) -> tuple[bool, int, int]:
        """Verifica si la empresa puede agregar un usuario más según su plan.
        Retorna (puede_agregar, usuarios_actuales, limite_maximo).
        """
        plan_codigo = getattr(empresa, "plan", "express") or "express"
        limite = cls.LIMITES_PLANES.get(str(plan_codigo).lower(), 1)
        count = cls.get_count(empresa)
        return count < limite, count, limite

    @classmethod
    def validar_cupo_usuario(cls, empresa_actual: Empresa) -> tuple[bool, int, int]:
        """Alias legacy — usar can_add_user en código nuevo."""
        return cls.can_add_user(empresa_actual)


def calculate_prorated_amount(
    empresa: Empresa,
    current_plan: str,
    requested_plan: str,
    billing_cycle: str,
    now: Any = None,
) -> Decimal:
    """Calcula monto prorrateado para upgrade.

    Proration = (días_restantes / días_ciclo) × (precio_nuevo - precio_actual)

    Args:
        empresa: Empresa para obtener país
        current_plan: Plan actual
        requested_plan: Plan solicitado
        billing_cycle: Ciclo de facturación ("monthly" o "annual")
        now: datetime para cálculos (default: timezone.now())

    Returns:
        Decimal con monto prorrateado
    """
    if now is None:
        now = timezone.now()

    # Validar que es un upgrade (requested > current en precio)
    current_price_info = get_plan_price(empresa.pais, current_plan, billing_cycle)
    requested_price_info = get_plan_price(empresa.pais, requested_plan, billing_cycle)

    if requested_price_info["price"] <= current_price_info["price"]:
        return Decimal("0.00")

    # Calcular días restantes en el ciclo actual
    days_in_cycle = 365 if billing_cycle == BILLING_ANNUAL else 30
    days_remaining = (empresa.fecha_fin - now).total_seconds() / 86400

    # Evitar negativos
    if days_remaining < 0:
        days_remaining = 0

    # Calcular el monto prorrateado
    price_difference = requested_price_info["price"] - current_price_info["price"]
    prorated = (Decimal(str(days_remaining)) / Decimal(str(days_in_cycle))) * price_difference

    # Redondear a 2 decimales, asegurar no negativo
    prorated = max(prorated.quantize(Decimal("0.01")), Decimal("0.00"))

    return prorated


def request_plan_change(
    empresa: Empresa,
    requested_plan: str,
    requested_by: Any = None,
    now: Any = None,
) -> SubscriptionChange:
    """Inicia un cambio de plan (upgrade/downgrade).

    - Upgrade: crea transacción PENDING, retorna change STATUS_PENDING
    - Downgrade: programa para fecha_fin, retorna change STATUS_SCHEDULED
    - Valida limites de usuarios; bloquea si hay cambio pendiente

    Args:
        empresa: Empresa solicitante
        requested_plan: Plan destino
        requested_by: User que solicita (optional)
        now: datetime para cálculos (default: timezone.now())

    Returns:
        SubscriptionChange con estado PENDING o SCHEDULED

    Raises:
        ValidationError si hay validaciones fallidas
    """
    if now is None:
        now = timezone.now()

    with transaction.atomic():
        # Bloquear empresa para evitar race conditions
        empresa = Empresa.objects.select_for_update().get(pk=empresa.pk)

        # Validar que no hay cambio pendiente
        pending_or_scheduled = SubscriptionChange.objects.filter(
            empresa=empresa,
            status__in=[
                SubscriptionChange.STATUS_PENDING,
                SubscriptionChange.STATUS_SCHEDULED,
            ],
        ).first()

        if pending_or_scheduled:
            raise ValidationError(
                f"Ya hay un cambio de plan pendiente: {pending_or_scheduled.status}"
            )

        # Determinar tipo de cambio
        if requested_plan == empresa.plan:
            raise ValidationError("El plan solicitado es igual al actual")

        # Obtener precios para comparar
        current_price = get_plan_price(empresa.pais, empresa.plan, "monthly")["price"]
        requested_price = get_plan_price(empresa.pais, requested_plan, "monthly")["price"]

        if requested_price > current_price:
            change_type = SubscriptionChange.CHANGE_UPGRADE
        else:
            change_type = SubscriptionChange.CHANGE_DOWNGRADE

        # Para downgrade, validar límites de usuarios
        if change_type == SubscriptionChange.CHANGE_DOWNGRADE:
            current_count = PlanLimitValidation.get_count(empresa)
            new_limit = PlanLimitValidation.LIMITES_PLANES.get(
                str(requested_plan).lower(), 1
            )
            if current_count > new_limit:
                raise ValidationError(
                    f"No se puede cambiar a {requested_plan}: "
                    f"tiene {current_count} usuarios, límite es {new_limit}"
                )

        # Calcular monto prorrateado (solo para upgrades)
        billing_cycle = BILLING_MONTHLY  # Asumir mensual por defecto
        prorated_amount = Decimal("0.00")
        transaction_obj = None

        if change_type == SubscriptionChange.CHANGE_UPGRADE:
            prorated_amount = calculate_prorated_amount(
                empresa=empresa,
                current_plan=empresa.plan,
                requested_plan=requested_plan,
                billing_cycle=billing_cycle,
                now=now,
            )

            # Crear transacción para el pago
            transaction_obj = SuscripcionTransaccion.objects.create(
                empresa=empresa,
                source_type="plan_upgrade",
                status="pending",
                raw_status="pending",
                payment_method="transferencia",
                billing_cycle=billing_cycle,
                plan_code=requested_plan,
                months_paid=1,
                amount=prorated_amount,
                currency=get_plan_price(empresa.pais, requested_plan, billing_cycle).get(
                    "currency", "USD"
                ),
                customer_email=empresa.user.email if empresa.user else "",
                description=f"Upgrade {empresa.plan} → {requested_plan}",
            )

        # Crear el cambio de suscripción
        change = SubscriptionChange.objects.create(
            empresa=empresa,
            requested_by=requested_by,
            current_plan=empresa.plan,
            requested_plan=requested_plan,
            change_type=change_type,
            status=(
                SubscriptionChange.STATUS_PENDING
                if change_type == SubscriptionChange.CHANGE_UPGRADE
                else SubscriptionChange.STATUS_SCHEDULED
            ),
            billing_cycle=billing_cycle,
            prorated_amount=prorated_amount,
            currency=get_plan_price(empresa.pais, requested_plan, billing_cycle).get(
                "currency", "USD"
            ),
            scheduled_at=(
                empresa.fecha_fin
                if change_type == SubscriptionChange.CHANGE_DOWNGRADE
                else None
            ),
            transaction=transaction_obj,
        )

        return change


def complete_paid_plan_change(change: SubscriptionChange) -> SubscriptionChange:
    """Aplica upgrade después de que transacción sea aprobada.

    Args:
        change: SubscriptionChange con status PENDING

    Returns:
        SubscriptionChange actualizado a COMPLETED
    """
    with transaction.atomic():
        change = SubscriptionChange.objects.select_for_update().get(pk=change.pk)
        empresa = change.empresa

        # Actualizar empresa con el nuevo plan
        empresa.plan = change.requested_plan
        empresa.save(update_fields=["plan"])

        # Marcar cambio como completado
        change.status = SubscriptionChange.STATUS_COMPLETED
        change.applied_at = timezone.now()
        change.save(update_fields=["status", "applied_at"])

        return change


def cancel_scheduled_plan_change(change: SubscriptionChange) -> None:
    """Cancela cambio de plan programado.

    Args:
        change: SubscriptionChange a cancelar
    """
    with transaction.atomic():
        change = SubscriptionChange.objects.select_for_update().get(pk=change.pk)

        change.status = SubscriptionChange.STATUS_CANCELLED
        change.cancelled_at = timezone.now()
        change.save(update_fields=["status", "cancelled_at"])

        # Cancelar transacción si existe
        if change.transaction:
            change.transaction.status = "cancelled"
            change.transaction.raw_status = "cancelled_by_user"
            change.transaction.save(update_fields=["status", "raw_status"])


def apply_due_scheduled_changes(now: Any = None) -> dict[str, int]:
    """Aplica downgrades programados que vencieron.

    Busca cambios SCHEDULED con scheduled_at < now y los aplica.
    Si la validación falla (ej: demasiados usuarios), marca como FAILED.

    Args:
        now: datetime para cálculos (default: timezone.now())

    Returns:
        {"applied": int, "failed": int}
    """
    if now is None:
        now = timezone.now()

    stats = {"applied": 0, "failed": 0}

    # Buscar cambios vencidos
    due_changes = SubscriptionChange.objects.filter(
        status=SubscriptionChange.STATUS_SCHEDULED,
        scheduled_at__lte=now,
    ).select_for_update()

    for change in due_changes:
        with transaction.atomic():
            change = SubscriptionChange.objects.select_for_update().get(pk=change.pk)

            # Validar límites antes de aplicar (contra el nuevo plan)
            empresa = change.empresa
            current_count = PlanLimitValidation.get_count(empresa)
            new_limit = PlanLimitValidation.LIMITES_PLANES.get(
                str(change.requested_plan).lower(), 1
            )

            if current_count > new_limit:
                # Marcar como fallido
                change.status = SubscriptionChange.STATUS_FAILED
                change.failure_reason = (
                    f"Demasiados usuarios ({current_count}) para plan {change.requested_plan} "
                    f"(límite: {new_limit})"
                )
                change.save(update_fields=["status", "failure_reason"])
                stats["failed"] += 1
                continue

            # Aplicar el cambio
            empresa.plan = change.requested_plan
            empresa.save(update_fields=["plan"])

            change.status = SubscriptionChange.STATUS_COMPLETED
            change.applied_at = timezone.now()
            change.save(update_fields=["status", "applied_at"])
            stats["applied"] += 1

    return stats


def expire_pending_upgrades(now: Any = None) -> dict[str, int]:
    """Cancela upgrades pendientes de pago después de 24 horas.

    Args:
        now: datetime para cálculos (default: timezone.now())

    Returns:
        {"expired": int}
    """
    if now is None:
        now = timezone.now()

    stats = {"expired": 0}

    # Buscar upgrades PENDING creados hace >24h
    cutoff_time = now - timezone.timedelta(hours=24)

    pending_upgrades = SubscriptionChange.objects.filter(
        status=SubscriptionChange.STATUS_PENDING,
        change_type=SubscriptionChange.CHANGE_UPGRADE,
        created_at__lte=cutoff_time,
    ).select_for_update()

    for change in pending_upgrades:
        with transaction.atomic():
            change = SubscriptionChange.objects.select_for_update().get(pk=change.pk)

            change.status = SubscriptionChange.STATUS_CANCELLED
            change.cancelled_at = timezone.now()
            change.save(update_fields=["status", "cancelled_at"])

            # Cancelar transacción asociada
            if change.transaction:
                change.transaction.status = "cancelled"
                change.transaction.raw_status = "expired"
                change.transaction.save(update_fields=["status", "raw_status"])

            stats["expired"] += 1

    return stats


def get_plan_change_health(now: Any = None) -> dict[str, int]:
    """Reporta estado de cambios de plan.

    Retorna conteos de diferentes estados de cambios.

    Args:
        now: datetime para cálculos (default: timezone.now())

    Returns:
        {"pending_upgrades": int, "expired_pending_upgrades": int,
         "scheduled_downgrades": int, "failed_downgrades": int}
    """
    if now is None:
        now = timezone.now()

    # Contar upgrades PENDING
    pending_upgrades = SubscriptionChange.objects.filter(
        status=SubscriptionChange.STATUS_PENDING,
        change_type=SubscriptionChange.CHANGE_UPGRADE,
    ).count()

    # Contar upgrades PENDING expirados (>24h)
    cutoff_time = now - timezone.timedelta(hours=24)
    expired_pending_upgrades = SubscriptionChange.objects.filter(
        status=SubscriptionChange.STATUS_PENDING,
        change_type=SubscriptionChange.CHANGE_UPGRADE,
        created_at__lte=cutoff_time,
    ).count()

    # Contar downgrades SCHEDULED
    scheduled_downgrades = SubscriptionChange.objects.filter(
        status=SubscriptionChange.STATUS_SCHEDULED,
        change_type=SubscriptionChange.CHANGE_DOWNGRADE,
    ).count()

    # Contar downgrades FAILED
    failed_downgrades = SubscriptionChange.objects.filter(
        status=SubscriptionChange.STATUS_FAILED,
        change_type=SubscriptionChange.CHANGE_DOWNGRADE,
    ).count()

    return {
        "pending_upgrades": pending_upgrades,
        "expired_pending_upgrades": expired_pending_upgrades,
        "scheduled_downgrades": scheduled_downgrades,
        "failed_downgrades": failed_downgrades,
    }
