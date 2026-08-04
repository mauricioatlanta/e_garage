from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone

from taller.models import Empresa, TeamMember
from taller.models.subscription_change import SubscriptionChange
from taller.services.plan_change_service import (
    apply_due_scheduled_changes,
    calculate_prorated_amount,
    cancel_scheduled_plan_change,
    expire_pending_upgrades,
    get_plan_change_health,
    request_plan_change,
)
from taller.services.suscripcion_transaccion_service import approve_transaction
from taller.utils.plan_catalog import PLAN_BUSINESS, PLAN_ENTRY, PLAN_GROWTH


@pytest.fixture
def empresa_activa(db):
    from taller.tests.factories import EmpresaFactory
    now = timezone.now()
    return EmpresaFactory(
        nombre_taller="Taller Planes",
        pais="US",
        plan=PLAN_ENTRY,
        suscripcion_activa=True,
        fecha_inicio=now - timedelta(days=15),
        fecha_fin=now + timedelta(days=15),
        ultimo_pago=now - timedelta(days=15),
        valor_mensual=Decimal("20.00"),
    )


def test_upgrade_with_proration_waits_for_payment_confirmation(empresa_activa, monkeypatch):
    fecha_fin_original = empresa_activa.fecha_fin
    monkeypatch.setattr(
        "taller.services.suscripcion_transaccion_service._send_subscription_notifications",
        lambda *args, **kwargs: None,
    )

    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_GROWTH)

    empresa_activa.refresh_from_db()
    assert empresa_activa.plan == PLAN_ENTRY
    assert empresa_activa.fecha_fin == fecha_fin_original
    assert change.status == SubscriptionChange.STATUS_PENDING
    assert change.change_type == SubscriptionChange.CHANGE_UPGRADE
    assert change.prorated_amount > 0
    assert change.transaction is not None

    approve_transaction(change.transaction, processed_by="test")

    empresa_activa.refresh_from_db()
    change.refresh_from_db()
    assert empresa_activa.plan == PLAN_GROWTH
    assert empresa_activa.fecha_fin == fecha_fin_original
    assert change.status == SubscriptionChange.STATUS_COMPLETED
    assert change.transaction.subscription_applied_at is not None


def test_downgrade_is_scheduled_for_period_end(empresa_activa):
    empresa_activa.plan = PLAN_BUSINESS
    empresa_activa.save(update_fields=["plan"])

    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_ENTRY)

    empresa_activa.refresh_from_db()
    assert empresa_activa.plan == PLAN_BUSINESS
    assert change.status == SubscriptionChange.STATUS_SCHEDULED
    assert change.change_type == SubscriptionChange.CHANGE_DOWNGRADE
    assert change.scheduled_at == empresa_activa.fecha_fin


def test_due_downgrade_is_applied_after_period_end(empresa_activa):
    empresa_activa.plan = PLAN_BUSINESS
    empresa_activa.fecha_fin = timezone.now() - timedelta(minutes=1)
    empresa_activa.save(update_fields=["plan", "fecha_fin"])
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_ENTRY)

    stats = apply_due_scheduled_changes()

    empresa_activa.refresh_from_db()
    change.refresh_from_db()
    assert stats == {"applied": 1, "failed": 0}
    assert empresa_activa.plan == PLAN_ENTRY
    assert change.status == SubscriptionChange.STATUS_COMPLETED


def test_plan_change_validates_new_plan_user_limit(empresa_activa):
    empresa_activa.plan = PLAN_BUSINESS
    empresa_activa.save(update_fields=["plan"])
    for index in range(2):
        member_user = User.objects.create_user(f"member-{index}", f"m{index}@example.com")
        TeamMember.objects.create(user=member_user, empresa=empresa_activa, is_active=True)

    with pytest.raises(ValidationError):
        request_plan_change(empresa=empresa_activa, requested_plan=PLAN_ENTRY)


def test_blocks_second_change_while_downgrade_is_scheduled(empresa_activa):
    empresa_activa.plan = PLAN_BUSINESS
    empresa_activa.save(update_fields=["plan"])
    request_plan_change(empresa=empresa_activa, requested_plan=PLAN_GROWTH)

    with pytest.raises(ValidationError):
        request_plan_change(empresa=empresa_activa, requested_plan=PLAN_ENTRY)


def test_blocks_second_change_while_upgrade_payment_is_pending(empresa_activa):
    request_plan_change(empresa=empresa_activa, requested_plan=PLAN_GROWTH)

    with pytest.raises(ValidationError):
        request_plan_change(empresa=empresa_activa, requested_plan=PLAN_BUSINESS)


def test_cancel_scheduled_downgrade_prevents_application(empresa_activa):
    empresa_activa.plan = PLAN_BUSINESS
    empresa_activa.fecha_fin = timezone.now() - timedelta(minutes=1)
    empresa_activa.save(update_fields=["plan", "fecha_fin"])
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_ENTRY)

    cancel_scheduled_plan_change(change=change)
    stats = apply_due_scheduled_changes()

    empresa_activa.refresh_from_db()
    change.refresh_from_db()
    assert stats == {"applied": 0, "failed": 0}
    assert empresa_activa.plan == PLAN_BUSINESS
    assert change.status == SubscriptionChange.STATUS_CANCELLED


def test_apply_due_scheduled_changes_is_idempotent(empresa_activa):
    empresa_activa.plan = PLAN_BUSINESS
    empresa_activa.fecha_fin = timezone.now() - timedelta(minutes=1)
    empresa_activa.save(update_fields=["plan", "fecha_fin"])
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_ENTRY)

    first_stats = apply_due_scheduled_changes()
    second_stats = apply_due_scheduled_changes()

    change.refresh_from_db()
    assert first_stats == {"applied": 1, "failed": 0}
    assert second_stats == {"applied": 0, "failed": 0}
    assert change.status == SubscriptionChange.STATUS_COMPLETED


def test_command_retry_does_not_reapply_failed_downgrade(empresa_activa):
    empresa_activa.plan = PLAN_BUSINESS
    empresa_activa.fecha_fin = timezone.now() - timedelta(minutes=1)
    empresa_activa.save(update_fields=["plan", "fecha_fin"])
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_ENTRY)
    member_user = User.objects.create_user("late-member", "late-member@example.com")
    TeamMember.objects.create(user=member_user, empresa=empresa_activa, is_active=True)

    first_stats = apply_due_scheduled_changes()
    second_stats = apply_due_scheduled_changes()

    change.refresh_from_db()
    empresa_activa.refresh_from_db()
    assert first_stats == {"applied": 0, "failed": 1}
    assert second_stats == {"applied": 0, "failed": 0}
    assert empresa_activa.plan == PLAN_BUSINESS
    assert change.status == SubscriptionChange.STATUS_FAILED


def test_proration_with_one_day_remaining_uses_decimal_rounding(empresa_activa):
    now = timezone.now()
    empresa_activa.ultimo_pago = now - timedelta(days=29)
    empresa_activa.fecha_inicio = now - timedelta(days=29)
    empresa_activa.fecha_fin = now + timedelta(days=1)

    amount = calculate_prorated_amount(
        empresa=empresa_activa,
        current_plan=PLAN_ENTRY,
        requested_plan=PLAN_GROWTH,
        billing_cycle="monthly",
        now=now,
    )

    assert amount == Decimal("0.63")


def test_proration_in_last_minute_is_non_negative_decimal(empresa_activa):
    now = timezone.now()
    empresa_activa.ultimo_pago = now - timedelta(days=30) + timedelta(minutes=1)
    empresa_activa.fecha_inicio = empresa_activa.ultimo_pago
    empresa_activa.fecha_fin = now + timedelta(minutes=1)

    amount = calculate_prorated_amount(
        empresa=empresa_activa,
        current_plan=PLAN_ENTRY,
        requested_plan=PLAN_GROWTH,
        billing_cycle="monthly",
        now=now,
    )

    assert isinstance(amount, Decimal)
    assert amount >= Decimal("0.00")


def test_proration_is_stable_with_local_timezone_override(empresa_activa, settings):
    settings.TIME_ZONE = "UTC"
    utc_now = datetime(2026, 5, 18, 12, 0, tzinfo=ZoneInfo("UTC"))
    local_now = utc_now.astimezone(ZoneInfo("America/Santiago"))
    empresa_activa.ultimo_pago = utc_now - timedelta(days=15)
    empresa_activa.fecha_inicio = empresa_activa.ultimo_pago
    empresa_activa.fecha_fin = utc_now + timedelta(days=15)

    with timezone.override("America/Santiago"):
        local_amount = calculate_prorated_amount(
            empresa=empresa_activa,
            current_plan=PLAN_ENTRY,
            requested_plan=PLAN_GROWTH,
            billing_cycle="monthly",
            now=local_now,
        )
    utc_amount = calculate_prorated_amount(
        empresa=empresa_activa,
        current_plan=PLAN_ENTRY,
        requested_plan=PLAN_GROWTH,
        billing_cycle="monthly",
        now=utc_now,
    )

    assert local_amount == utc_amount == Decimal("9.50")


def test_expire_pending_upgrades_cancels_change_and_transaction(empresa_activa):
    now = timezone.now()
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_GROWTH, now=now)
    SubscriptionChange.objects.filter(pk=change.pk).update(created_at=now - timedelta(hours=25))

    stats = expire_pending_upgrades(now=now)

    empresa_activa.refresh_from_db()
    change.refresh_from_db()
    change.transaction.refresh_from_db()
    assert stats == {"expired": 1}
    assert empresa_activa.plan == PLAN_ENTRY
    assert change.status == SubscriptionChange.STATUS_CANCELLED
    assert change.transaction.status == "cancelled"
    assert change.transaction.raw_status == "expired"


def test_expire_pending_upgrades_is_idempotent(empresa_activa):
    now = timezone.now()
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_GROWTH, now=now)
    SubscriptionChange.objects.filter(pk=change.pk).update(created_at=now - timedelta(hours=25))

    first_stats = expire_pending_upgrades(now=now)
    second_stats = expire_pending_upgrades(now=now)

    assert first_stats == {"expired": 1}
    assert second_stats == {"expired": 0}


def test_plan_change_health_counts_operational_states(empresa_activa):
    now = timezone.now()
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_GROWTH, now=now)
    SubscriptionChange.objects.filter(pk=change.pk).update(created_at=now - timedelta(hours=25))

    health = get_plan_change_health(now=now)

    assert health["pending_upgrades"] == 1
    assert health["expired_pending_upgrades"] == 1
    assert health["scheduled_downgrades"] == 0
    assert health["failed_downgrades"] == 0


def test_apply_scheduled_plan_changes_command_reports_health(empresa_activa):
    now = timezone.now()
    change = request_plan_change(empresa=empresa_activa, requested_plan=PLAN_GROWTH, now=now)
    SubscriptionChange.objects.filter(pk=change.pk).update(created_at=now - timedelta(hours=25))
    output = StringIO()

    call_command("apply_scheduled_plan_changes", stdout=output)

    change.refresh_from_db()
    assert change.status == SubscriptionChange.STATUS_CANCELLED
    assert "Upgrades expirados: 1" in output.getvalue()
    assert "Health billing:" in output.getvalue()
