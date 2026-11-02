"""
Tests del CommercePaidConsumer — H4.1.1.

Principio: Commerce no mueve inventario. El ERP lo mueve.
El consumer solo emite el Documento y marca el pago.
La señal pre_save → InventoryService es la única fuente de verdad para stock.

1.  commerce.order.paid emite el Documento (BORRADOR → EMITIDO).
2.  Marca el Documento como pagado (estado_pago=PAGADO, pagado=True).
3.  Idempotencia: reprocesar el evento no duplica el efecto.
4.  Error si commerce.order.submitted aún no fue procesado (retryable).
5.  El consumer no crea MovimientoInventario directamente (single-source-of-truth).
6.  Error si Empresa no existe.
"""
import uuid
from decimal import Decimal

import pytest

from commerce.services.cart_service import CartService
from commerce.services.order_service import OrderService
from commerce.tests.conftest import make_category, make_product
from runtime.models.outbox_event import OutboxEvent
from runtime.models.processed_event import ProcessedEvent
from runtime.services.outbox_service import OutboxService
from taller.models.documento import Documento
from taller.models.movimiento_inventario import MovimientoInventario
from taller.tests.factories import EmpresaFactory, RepuestoFactory


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def empresa(db):
    return EmpresaFactory(nombre_taller="MonteAzul", pais="CL")


def _checkout(empresa, stock=10):
    repuesto = RepuestoFactory(empresa=empresa, part_number="F-001",
                               precio_venta=Decimal("4990"), cantidad_stock=stock)
    cat = make_category(empresa)
    product = make_product(empresa, repuesto=repuesto, category=cat)
    cart = CartService.get_or_create(empresa, "a" * 32)
    CartService.add_item(cart, product, 2)
    order = OrderService.create_from_cart(
        cart, {"name": "Juan Pérez", "email": "juan@test.cl"}
    )
    return order, repuesto


def _enqueue_paid(order, empresa, repuesto_id=None):
    event_id = uuid.uuid4()
    items = []
    if repuesto_id is not None:
        items = [{
            "commerce_order_item_id": 1,
            "sku": "F-001",
            "name": "Filtro aceite",
            "quantity": 2,
            "unit_price": "4990.00",
            "repuesto_id": repuesto_id,
        }]
    OutboxService.enqueue(
        event_id=event_id,
        aggregate_type="commerce_order",
        aggregate_id=str(order.pk),
        event_type="commerce.order.paid",
        payload={
            "event_id": str(event_id),
            "occurred_at": "2026-08-01T10:00:00+00:00",
            "schema_version": "1.0.0",
            "empresa_id": empresa.pk,
            "commerce_order_id": order.pk,
            "order_number": order.order_number,
            "gateway": "webpay",
            "gateway_ref": "AUTH001",
            "amount": int(order.total),
            "currency": "CLP",
            "card_last4": "1234",
            "paid_at": "2026-08-01T10:00:00+00:00",
            "items": items,
        },
    )
    return event_id


# ── 1. Emite el Documento ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_paid_consumer_emits_documento(empresa):
    order, repuesto = _checkout(empresa)
    OutboxService.process_pending(event_type="commerce.order.submitted")

    doc = Documento.objects.get(empresa=empresa, tipo="PTS")
    assert doc.estado == "BORRADOR"

    _enqueue_paid(order, empresa, repuesto_id=repuesto.pk)
    OutboxService.process_pending(event_type="commerce.order.paid")

    doc.refresh_from_db()
    assert doc.estado == "EMITIDO"


# ── 2. Marca el Documento como pagado ────────────────────────────────────────

@pytest.mark.django_db
def test_paid_consumer_marks_documento_paid(empresa):
    order, repuesto = _checkout(empresa)
    OutboxService.process_pending(event_type="commerce.order.submitted")
    _enqueue_paid(order, empresa, repuesto_id=repuesto.pk)
    OutboxService.process_pending(event_type="commerce.order.paid")

    doc = Documento.objects.get(empresa=empresa, tipo="PTS")
    assert doc.estado_pago == "PAGADO"
    assert doc.pagado is True


# ── 3. Idempotencia ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_paid_consumer_idempotent(empresa):
    order, repuesto = _checkout(empresa)
    OutboxService.process_pending(event_type="commerce.order.submitted")
    event_id = _enqueue_paid(order, empresa, repuesto_id=repuesto.pk)

    OutboxService.process_pending(event_type="commerce.order.paid")

    # Forzar reintento del mismo evento
    OutboxEvent.objects.filter(
        aggregate_id=str(order.pk), event_type="commerce.order.paid"
    ).update(status=OutboxEvent.PENDING, attempts=0)
    OutboxService.process_pending(event_type="commerce.order.paid")

    assert ProcessedEvent.objects.filter(
        event_id=event_id, consumer="commerce_paid_consumer"
    ).count() == 1

    doc = Documento.objects.get(empresa=empresa, tipo="PTS")
    assert doc.estado == "EMITIDO"


# ── 4. Error si submitted no fue procesado ────────────────────────────────────

@pytest.mark.django_db
def test_paid_consumer_fails_if_submitted_not_processed(empresa):
    order, _ = _checkout(empresa)
    # NO procesamos commerce.order.submitted
    _enqueue_paid(order, empresa)
    OutboxService.process_pending(event_type="commerce.order.paid")

    paid_event = OutboxEvent.objects.get(
        aggregate_id=str(order.pk), event_type="commerce.order.paid"
    )
    assert paid_event.last_error
    assert "BORRADOR" in paid_event.last_error or "submitted" in paid_event.last_error


# ── 5. ERP (señal) crea MovimientoInventario y descuenta stock ───────────────

@pytest.mark.django_db
def test_paid_consumer_triggers_inventory_via_erp_signal(empresa):
    """
    El consumer emite el Documento con doc.save() → pre_save signal →
    InventoryService.procesar_movimiento_stock → MovimientoInventario + stock.

    El consumer NO toca MovimientoInventario ni Repuesto directamente.
    El ERP hace el trabajo completo.
    """
    order, repuesto = _checkout(empresa, stock=10)
    OutboxService.process_pending(event_type="commerce.order.submitted")

    stock_antes = repuesto.cantidad_stock  # 10
    count_antes = MovimientoInventario.objects.filter(empresa=empresa).count()

    _enqueue_paid(order, empresa, repuesto_id=repuesto.pk)
    OutboxService.process_pending(event_type="commerce.order.paid")

    doc = Documento.objects.get(empresa=empresa, tipo="PTS")
    assert doc.estado == "EMITIDO"

    # ERP creó el MovimientoInventario via señal
    movs = MovimientoInventario.objects.filter(empresa=empresa, repuesto=repuesto)
    assert movs.count() == count_antes + 1
    mov = movs.latest("created_at")
    assert mov.tipo == MovimientoInventario.TipoMovimiento.EMISION
    assert mov.cantidad_delta == -2
    assert mov.saldo_resultante == 8

    # Stock decrementado
    repuesto.refresh_from_db()
    assert repuesto.cantidad_stock == stock_antes - 2


# ── 6. Error si Empresa no existe ─────────────────────────────────────────────

@pytest.mark.django_db
def test_paid_consumer_fails_for_nonexistent_empresa(empresa):
    order, _ = _checkout(empresa)
    OutboxService.process_pending(event_type="commerce.order.submitted")

    bad_event_id = uuid.uuid4()
    OutboxService.enqueue(
        event_id=bad_event_id,
        aggregate_type="commerce_order",
        aggregate_id=str(order.pk),
        event_type="commerce.order.paid",
        payload={
            "event_id": str(bad_event_id),
            "schema_version": "1.0.0",
            "empresa_id": 999999,
            "commerce_order_id": order.pk,
            "order_number": order.order_number,
            "gateway": "webpay",
            "gateway_ref": "AUTH",
            "amount": 9980,
            "currency": "CLP",
            "card_last4": "",
            "paid_at": "2026-08-01T10:00:00+00:00",
            "items": [],
        },
    )
    OutboxService.process_pending(event_type="commerce.order.paid")

    bad_event = OutboxEvent.objects.get(event_id=bad_event_id)
    assert bad_event.last_error
    assert "999999" in bad_event.last_error or "Empresa" in bad_event.last_error
