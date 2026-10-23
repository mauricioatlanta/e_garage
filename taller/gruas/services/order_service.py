from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from taller.models import TowingEvent, TowingOrder, TowingQuote

ALLOWED_TRANSITIONS = {
    TowingOrder.STATUS_REQUESTED: {TowingOrder.STATUS_QUOTED, TowingOrder.STATUS_CANCELLED},
    TowingOrder.STATUS_QUOTED: {TowingOrder.STATUS_ACCEPTED, TowingOrder.STATUS_CANCELLED},
    TowingOrder.STATUS_ACCEPTED: {TowingOrder.STATUS_ASSIGNED, TowingOrder.STATUS_CANCELLED},
    TowingOrder.STATUS_ASSIGNED: {TowingOrder.STATUS_EN_ROUTE, TowingOrder.STATUS_CANCELLED},
    TowingOrder.STATUS_EN_ROUTE: {TowingOrder.STATUS_PICKUP, TowingOrder.STATUS_FAILED},
    TowingOrder.STATUS_PICKUP: {TowingOrder.STATUS_LOADED, TowingOrder.STATUS_FAILED},
    TowingOrder.STATUS_LOADED: {TowingOrder.STATUS_TRANSIT},
    TowingOrder.STATUS_TRANSIT: {TowingOrder.STATUS_DELIVERED},
    TowingOrder.STATUS_DELIVERED: {TowingOrder.STATUS_CLOSED},
}


@transaction.atomic
def transition_order(*, order_id, empresa, to_status, user, comment="", metadata=None):
    order = TowingOrder.objects.select_for_update().get(pk=order_id, empresa=empresa)
    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if to_status not in allowed:
        raise ValidationError(f"Transición no permitida: {order.status} → {to_status}")
    previous = order.status
    order.status = to_status
    if to_status == TowingOrder.STATUS_CLOSED:
        order.closed_at = timezone.now()
    order.save(update_fields=["status", "closed_at", "updated_at"])
    TowingEvent.objects.create(
        order=order, event_type="STATUS_CHANGE", from_status=previous,
        to_status=to_status, comment=comment, metadata=metadata or {}, created_by=user,
    )
    return order


@transaction.atomic
def create_quote(*, order_id, empresa, user, net_amount, tax_rate, notes="", included_km=0):
    order = TowingOrder.objects.select_for_update().get(pk=order_id, empresa=empresa)
    current = order.quotes.filter(is_current=True).first()
    version = (order.quotes.order_by("-version").values_list("version", flat=True).first() or 0) + 1
    net_amount = net_amount
    tax_amount = (net_amount * tax_rate / 100).quantize(Decimal("0.01"))
    if current:
        # Release the partial unique slot before inserting the new current version.
        current.is_current = False
        current.status = TowingQuote.STATUS_EXPIRED
        current.save(update_fields=["is_current", "status"])
    quote = TowingQuote.objects.create(
        order=order, version=version, is_current=True, status=TowingQuote.STATUS_SENT,
        currency=order.currency, tax_rate=tax_rate, net_amount=net_amount,
        tax_amount=tax_amount, total_amount=net_amount + tax_amount,
        notes=notes, included_km=included_km, supersedes=current, created_by=user,
    )
    if order.status == TowingOrder.STATUS_REQUESTED:
        order.status = TowingOrder.STATUS_QUOTED
        order.save(update_fields=["status", "updated_at"])
        TowingEvent.objects.create(order=order, event_type="QUOTE_CREATED", to_status=order.status, created_by=user, metadata={"quote_id": quote.id, "version": quote.version})
    return quote


@transaction.atomic
def accept_quote(*, quote_id, empresa, user):
    quote = TowingQuote.objects.select_for_update().select_related("order").get(pk=quote_id, order__empresa=empresa)
    TowingQuote.objects.filter(order=quote.order, is_current=True).exclude(pk=quote.pk).update(is_current=False, status=TowingQuote.STATUS_EXPIRED)
    quote.is_current = True
    quote.status = TowingQuote.STATUS_ACCEPTED
    quote.accepted_at = timezone.now()
    quote.accepted_by = user
    quote.save(update_fields=["is_current", "status", "accepted_at", "accepted_by"])
    order = TowingOrder.objects.select_for_update().get(pk=quote.order_id, empresa=empresa)
    if order.status == TowingOrder.STATUS_QUOTED:
        order.status = TowingOrder.STATUS_ACCEPTED
        order.save(update_fields=["status", "updated_at"])
        TowingEvent.objects.create(order=order, event_type="QUOTE_ACCEPTED", to_status=order.status, created_by=user, metadata={"quote_id": quote.id, "version": quote.version})
    return quote
