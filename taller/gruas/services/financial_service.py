from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from taller.models import TowingLedgerEntry, TowingOrder


@transaction.atomic
def add_entry(*, order_id, empresa, entry_type, amount, currency, user, tax_rate=Decimal("0.00"), tax_included=False, reference="", reversed_entry=None):
    order = TowingOrder.objects.select_for_update().get(pk=order_id, empresa=empresa)
    amount = Decimal(amount)
    if amount <= 0:
        raise ValidationError("El importe debe ser positivo")
    if currency != order.currency:
        raise ValidationError("La moneda debe coincidir con la orden")
    if reversed_entry and (reversed_entry.order_id != order.id or reversed_entry.reversed_entry_id):
        raise ValidationError("La reversa no corresponde a la orden o ya fue revertida")
    if reversed_entry:
        expected = TowingLedgerEntry.EXPENSE_REVERSAL if reversed_entry.entry_type == TowingLedgerEntry.EXPENSE else TowingLedgerEntry.REFUND
        if entry_type != expected:
            raise ValidationError(f"La reversa de {reversed_entry.entry_type} debe registrarse como {expected}")
    return TowingLedgerEntry.objects.create(order=order, entry_type=entry_type, amount=amount, currency=currency, tax_rate=tax_rate, tax_included=tax_included, reference=reference, reversed_entry=reversed_entry, created_by=user)


def financial_summary(order):
    entries = order.ledger_entries.all()
    def total(kind):
        return entries.filter(entry_type=kind).aggregate(value=Sum("amount"))["value"] or Decimal("0.00")
    quote = order.vigente_quote
    accepted_total = quote.total_amount if quote else Decimal("0.00")
    net_collected = total(TowingLedgerEntry.ADVANCE) + total(TowingLedgerEntry.PAYMENT) - total(TowingLedgerEntry.REFUND)
    expenses = total(TowingLedgerEntry.EXPENSE) - total(TowingLedgerEntry.EXPENSE_REVERSAL)
    return {
        "accepted_total": accepted_total,
        "net_collected": net_collected,
        "balance": accepted_total - net_collected,
        "recorded_margin": accepted_total - expenses,
        "charges": total(TowingLedgerEntry.CHARGE),
        "expenses": expenses,
    }
