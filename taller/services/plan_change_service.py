from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from taller.models.subscription_change import SubscriptionChange
from taller.services.suscripcion_transaccion_service import create_gateway_transaction
from taller.utils.plan_catalog import (
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    COUNTRY_CURRENCY,
    DEFAULT_CURRENCY,
    PLAN_BUSINESS,
    PLAN_ENTRY,
    PLAN_GROWTH,
    PLAN_TRIAL,
    get_plan_limits,
    get_plan_price,
    normalize_billing_cycle,
    normalize_plan_code,
)


PLAN_RANK = {
    PLAN_TRIAL: 0,
    PLAN_ENTRY: 1,
    PLAN_GROWTH: 2,
    PLAN_BUSINESS: 3,
}
PENDING_UPGRADE_EXPIRATION_HOURS = 24


@dataclass(frozen=True)
class PlanLimitValidation:
    active_users: int
    users_max: int

    @property
    def as_dict(self):
        return {"active_users": self.active_users, "users_max": self.users_max}


def infer_billing_cycle(empresa) -> str:
    start = getattr(empresa, "ultimo_pago", None) or getattr(empresa, "fecha_inicio", None)
    end = getattr(empresa, "fecha_fin", None)
    if start and end and (end - start).days > 45:
        return BILLING_ANNUAL
    return BILLING_MONTHLY


def get_active_user_count(empresa) -> int:
    owner_id = getattr(empresa, "user_id", None)
    team_user_ids = set(
        empresa.team_members.filter(is_active=True)
        .exclude(user_id=owner_id)
        .values_list("user_id", flat=True)
    )
    return 1 + len(team_user_ids)


def validate_plan_limits(empresa, requested_plan: str) -> PlanLimitValidation:
    limits = get_plan_limits(requested_plan)
    active_users = get_active_user_count(empresa)
    users_max = limits["users_max"]
    if active_users > users_max:
        raise ValidationError(
            f"El plan solicitado permite hasta {users_max} usuario(s), "
            f"pero la empresa tiene {active_users} usuario(s) activo(s)."
        )
    return PlanLimitValidation(active_users=active_users, users_max=users_max)


def get_change_type(current_plan: str, requested_plan: str) -> str:
    current_rank = PLAN_RANK.get(normalize_plan_code(current_plan), 0)
    requested_rank = PLAN_RANK.get(normalize_plan_code(requested_plan), 0)
    if requested_rank == current_rank:
        raise ValidationError("La empresa ya está en ese plan.")
    if requested_rank > current_rank:
        return SubscriptionChange.CHANGE_UPGRADE
    return SubscriptionChange.CHANGE_DOWNGRADE


def money_round(amount: Decimal, currency: str) -> Decimal:
    quantizer = Decimal("1") if currency == "CLP" else Decimal("0.01")
    return amount.quantize(quantizer, rounding=ROUND_HALF_UP)


def calculate_prorated_amount(
    *,
    empresa,
    current_plan: str,
    requested_plan: str,
    billing_cycle: str,
    now=None,
) -> Decimal:
    now = now or timezone.now()
    period_start = getattr(empresa, "ultimo_pago", None) or getattr(empresa, "fecha_inicio", None) or now
    period_end = getattr(empresa, "fecha_fin", None) or now

    total_seconds = max(1, (period_end - period_start).total_seconds())
    remaining_seconds = max(0, (period_end - now).total_seconds())
    remaining_ratio = Decimal(str(remaining_seconds)) / Decimal(str(total_seconds))

    country = getattr(empresa, "pais", "")
    current_price = get_plan_price(country, current_plan, billing_cycle)["price"]
    requested_price = get_plan_price(country, requested_plan, billing_cycle)["price"]
    currency = COUNTRY_CURRENCY.get(country, DEFAULT_CURRENCY)
    prorated = (requested_price - current_price) * remaining_ratio
    return money_round(max(Decimal("0"), prorated), currency)


def _apply_plan_change(empresa, requested_plan: str):
    price_info = get_plan_price(
        getattr(empresa, "pais", ""),
        requested_plan,
        infer_billing_cycle(empresa),
    )
    empresa.plan = requested_plan
    empresa.valor_mensual = price_info["price"]
    empresa.suscripcion_activa = True
    empresa.save(update_fields=["plan", "valor_mensual", "suscripcion_activa"])


def request_plan_change(
    *,
    empresa,
    requested_plan,
    requested_by=None,
    billing_cycle=None,
    now=None,
) -> SubscriptionChange:
    now = now or timezone.now()
    current_plan = normalize_plan_code(empresa.plan)
    requested_plan = normalize_plan_code(requested_plan)
    billing_cycle = normalize_billing_cycle(billing_cycle or infer_billing_cycle(empresa))
    currency = COUNTRY_CURRENCY.get(getattr(empresa, "pais", ""), DEFAULT_CURRENCY)

    with transaction.atomic():
        empresa = empresa.__class__.objects.select_for_update().get(pk=empresa.pk)
        current_plan = normalize_plan_code(empresa.plan)
        change_type = get_change_type(current_plan, requested_plan)
        validation = validate_plan_limits(empresa, requested_plan)

        existing_change = SubscriptionChange.objects.filter(
            empresa=empresa,
            status__in=[
                SubscriptionChange.STATUS_PENDING,
                SubscriptionChange.STATUS_SCHEDULED,
            ],
        ).first()
        if existing_change:
            raise ValidationError(
                "Ya existe un cambio de plan pendiente para esta empresa. "
                "Cancélalo o complétalo antes de solicitar otro."
            )

        if change_type == SubscriptionChange.CHANGE_UPGRADE:
            prorated_amount = calculate_prorated_amount(
                empresa=empresa,
                current_plan=current_plan,
                requested_plan=requested_plan,
                billing_cycle=billing_cycle,
                now=now,
            )
            change = SubscriptionChange.objects.create(
                empresa=empresa,
                requested_by=requested_by,
                current_plan=current_plan,
                requested_plan=requested_plan,
                change_type=change_type,
                status=(
                    SubscriptionChange.STATUS_PENDING
                    if prorated_amount > 0
                    else SubscriptionChange.STATUS_COMPLETED
                ),
                billing_cycle=billing_cycle,
                prorated_amount=prorated_amount,
                currency=currency,
                applied_at=None if prorated_amount > 0 else now,
                validation_snapshot=validation.as_dict,
            )
            if prorated_amount > 0:
                change.transaction = create_gateway_transaction(
                    empresa=empresa,
                    source_type="otro",
                    payment_method="otro",
                    amount=prorated_amount,
                    currency=currency,
                    billing_cycle=billing_cycle,
                    plan_code=requested_plan,
                    reference=f"plan-change-{change.pk}",
                    description=(
                        f"Cobro proporcional por cambio de plan "
                        f"{current_plan} -> {requested_plan}"
                    ),
                    gateway_payload={"subscription_change_id": change.pk},
                )
            if prorated_amount == 0:
                _apply_plan_change(empresa, requested_plan)
            if change.transaction_id:
                change.save(update_fields=["transaction", "updated_at"])
            return change

        return SubscriptionChange.objects.create(
            empresa=empresa,
            requested_by=requested_by,
            current_plan=current_plan,
            requested_plan=requested_plan,
            change_type=change_type,
            status=SubscriptionChange.STATUS_SCHEDULED,
            billing_cycle=billing_cycle,
            prorated_amount=Decimal("0.00"),
            currency=currency,
            scheduled_at=empresa.fecha_fin or now,
            validation_snapshot=validation.as_dict,
        )


def complete_paid_plan_change(*, change: SubscriptionChange, now=None) -> SubscriptionChange:
    now = now or timezone.now()
    with transaction.atomic():
        locked = (
            SubscriptionChange.objects.select_for_update()
            .select_related("empresa")
            .get(pk=change.pk)
        )
        if locked.status == SubscriptionChange.STATUS_COMPLETED:
            return locked
        if locked.change_type != SubscriptionChange.CHANGE_UPGRADE:
            raise ValidationError("Solo los upgrades pagados se completan por transacción.")
        if locked.status != SubscriptionChange.STATUS_PENDING:
            raise ValidationError("El cambio de plan no está pendiente de pago.")

        validation = validate_plan_limits(locked.empresa, locked.requested_plan)
        _apply_plan_change(locked.empresa, locked.requested_plan)
        locked.status = SubscriptionChange.STATUS_COMPLETED
        locked.applied_at = now
        locked.failure_reason = ""
        locked.validation_snapshot = validation.as_dict
        locked.save(
            update_fields=[
                "status",
                "applied_at",
                "failure_reason",
                "validation_snapshot",
                "updated_at",
            ]
        )
        return locked


def cancel_scheduled_plan_change(*, change: SubscriptionChange, cancelled_by=None):
    if not change.is_pending_downgrade:
        raise ValidationError("Solo se pueden cancelar downgrades pendientes.")
    change.status = SubscriptionChange.STATUS_CANCELLED
    change.cancelled_at = timezone.now()
    change.save(update_fields=["status", "cancelled_at", "updated_at"])
    return change


def expire_pending_upgrades(*, now=None, expire_after=None) -> dict[str, int]:
    now = now or timezone.now()
    expire_after = expire_after or timedelta(hours=PENDING_UPGRADE_EXPIRATION_HOURS)
    cutoff = now - expire_after
    stats = {"expired": 0}
    pending_changes = SubscriptionChange.objects.select_related("transaction").filter(
        change_type=SubscriptionChange.CHANGE_UPGRADE,
        status=SubscriptionChange.STATUS_PENDING,
        created_at__lte=cutoff,
    )

    for change in pending_changes:
        with transaction.atomic():
            locked = (
                SubscriptionChange.objects.select_for_update()
                .select_related("transaction")
                .get(pk=change.pk)
            )
            if locked.status != SubscriptionChange.STATUS_PENDING:
                continue

            locked.status = SubscriptionChange.STATUS_CANCELLED
            locked.cancelled_at = now
            locked.failure_reason = "Pago no confirmado antes de expirar la solicitud."
            locked.save(
                update_fields=["status", "cancelled_at", "failure_reason", "updated_at"]
            )

            if locked.transaction_id and locked.transaction.status == "pending":
                locked.transaction.status = "cancelled"
                locked.transaction.raw_status = "expired"
                locked.transaction.processed_at = now
                locked.transaction.admin_notes = (
                    "Transacción cancelada automáticamente por expiración del cambio de plan."
                )
                locked.transaction.save(
                    update_fields=[
                        "status",
                        "raw_status",
                        "processed_at",
                        "admin_notes",
                        "updated_at",
                    ]
                )
            stats["expired"] += 1
    return stats


def get_plan_change_health(now=None) -> dict[str, int]:
    now = now or timezone.now()
    cutoff = now - timedelta(hours=PENDING_UPGRADE_EXPIRATION_HOURS)
    status_counts = {
        item["status"]: item["total"]
        for item in SubscriptionChange.objects.values("status").annotate(total=Count("id"))
    }
    return {
        "pending_upgrades": SubscriptionChange.objects.filter(
            change_type=SubscriptionChange.CHANGE_UPGRADE,
            status=SubscriptionChange.STATUS_PENDING,
        ).count(),
        "expired_pending_upgrades": SubscriptionChange.objects.filter(
            change_type=SubscriptionChange.CHANGE_UPGRADE,
            status=SubscriptionChange.STATUS_PENDING,
            created_at__lte=cutoff,
        ).count(),
        "scheduled_downgrades": SubscriptionChange.objects.filter(
            change_type=SubscriptionChange.CHANGE_DOWNGRADE,
            status=SubscriptionChange.STATUS_SCHEDULED,
        ).count(),
        "failed_downgrades": SubscriptionChange.objects.filter(
            change_type=SubscriptionChange.CHANGE_DOWNGRADE,
            status=SubscriptionChange.STATUS_FAILED,
        ).count(),
        "completed_changes": status_counts.get(SubscriptionChange.STATUS_COMPLETED, 0),
        "cancelled_changes": status_counts.get(SubscriptionChange.STATUS_CANCELLED, 0),
    }


def apply_due_scheduled_changes(now=None) -> dict[str, int]:
    now = now or timezone.now()
    stats = {"applied": 0, "failed": 0}
    due_changes = SubscriptionChange.objects.select_related("empresa").filter(
        change_type=SubscriptionChange.CHANGE_DOWNGRADE,
        status=SubscriptionChange.STATUS_SCHEDULED,
        scheduled_at__lte=now,
    )

    for change in due_changes:
        with transaction.atomic():
            locked = SubscriptionChange.objects.select_for_update().select_related("empresa").get(
                pk=change.pk
            )
            if locked.status != SubscriptionChange.STATUS_SCHEDULED:
                continue
            try:
                validate_plan_limits(locked.empresa, locked.requested_plan)
                _apply_plan_change(locked.empresa, locked.requested_plan)
                locked.status = SubscriptionChange.STATUS_COMPLETED
                locked.applied_at = now
                locked.failure_reason = ""
                locked.save(update_fields=["status", "applied_at", "failure_reason", "updated_at"])
                stats["applied"] += 1
            except ValidationError as exc:
                locked.status = SubscriptionChange.STATUS_FAILED
                locked.failure_reason = "; ".join(exc.messages)
                locked.save(update_fields=["status", "failure_reason", "updated_at"])
                stats["failed"] += 1
    return stats
