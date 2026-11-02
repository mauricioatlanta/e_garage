from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from taller.models import TowingAssignment, TowingEvent, TowingOrder, TowingDriver, TowingUnit


def _overlap(start, end):
    return Q(planned_start_at__lt=end, planned_end_at__gt=start)


@transaction.atomic
def assign_order(*, order_id, empresa, unit_id, driver_id, planned_start_at, planned_end_at, user):
    order = TowingOrder.objects.select_for_update().get(pk=order_id, empresa=empresa)
    if order.status not in (TowingOrder.STATUS_ACCEPTED, TowingOrder.STATUS_ASSIGNED):
        raise ValidationError("La orden debe tener una cotización aceptada antes de asignar recursos")
    active_old = list(order.assignments.filter(is_active=True).select_related("unit", "driver"))
    unit_ids = sorted({a.unit_id for a in active_old} | {unit_id})
    driver_ids = sorted({a.driver_id for a in active_old} | {driver_id})
    # Deterministic lock order: all units by id, then all drivers by id.
    locked_units = {u.id: u for u in TowingUnit.objects.select_for_update().filter(empresa=empresa, id__in=unit_ids).order_by("id")}
    locked_drivers = {d.id: d for d in TowingDriver.objects.select_for_update().filter(empresa=empresa, id__in=driver_ids).order_by("id")}
    unit = locked_units.get(unit_id)
    driver = locked_drivers.get(driver_id)
    if not unit or unit.estado != "ACTIVA":
        raise ValidationError("La grúa no está disponible")
    if not driver or not driver.activo:
        raise ValidationError("El conductor no está disponible")
    if planned_end_at <= planned_start_at:
        raise ValidationError("El intervalo de asignación no es válido")
    conflicts = TowingAssignment.objects.select_for_update().filter(
        is_active=True,
    ).filter(_overlap(planned_start_at, planned_end_at)).filter(Q(unit=unit) | Q(driver=driver)).exclude(order=order)
    if conflicts.exists():
        raise ValidationError("La grúa o el conductor ya están reservados en ese intervalo")
    for previous in active_old:
        previous.is_active = False
        previous.released_at = timezone.now()
        previous.release_reason = "REASIGNACION"
        previous.save(update_fields=["is_active", "released_at", "release_reason"])
        TowingEvent.objects.create(order=order, assignment=previous, event_type="REASSIGNED", metadata={"previous_assignment_id": previous.id}, created_by=user)
    assignment = TowingAssignment.objects.create(order=order, unit=unit, driver=driver, planned_start_at=planned_start_at, planned_end_at=planned_end_at, assigned_by=user)
    if order.status == TowingOrder.STATUS_ACCEPTED:
        order.status = TowingOrder.STATUS_ASSIGNED
        order.save(update_fields=["status", "updated_at"])
    TowingEvent.objects.create(order=order, assignment=assignment, event_type="ASSIGNED", to_status=order.status, created_by=user)
    return assignment


@transaction.atomic
def release_assignment(*, assignment_id, empresa, user, reason):
    assignment = TowingAssignment.objects.select_for_update().select_related("order").get(pk=assignment_id, order__empresa=empresa)
    if not assignment.is_active:
        return assignment
    assignment.is_active = False
    assignment.released_at = timezone.now()
    assignment.release_reason = reason
    assignment.save(update_fields=["is_active", "released_at", "release_reason"])
    TowingEvent.objects.create(order=assignment.order, assignment=assignment, event_type="ASSIGNMENT_RELEASED", metadata={"reason": reason}, created_by=user)
    return assignment
