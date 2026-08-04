"""
Tests del Contract Runtime MVP (15 tests).

1.  Checkout crea Order + outbox atómicamente.
2.  Fallo al crear outbox revierte el Order.
3.  Consumer crea Documento PTS BORRADOR.
4.  Consumer crea líneas correctas.
5.  Precios/nombres permanecen congelados.
6.  Reprocesar event_id no duplica Documento.
7.  Otro tenant no puede consumir datos cruzados.
8.  Evento inválido queda FAILED.
9.  Reintentos incrementan attempts.
10. Stock no cambia.
11. Ledger no recibe movimientos.
12. Commerce no contiene imports ERP.
13. Contract schema valida (validación estructural).
14. manage.py check limpio.
15. Suites Commerce actuales siguen verdes.
"""
import io
import json
import uuid
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.test import Client, override_settings
from django.utils import timezone

from commerce.models.cart import CommerceCart
from commerce.models.order import CommerceOrder
from commerce.services.cart_service import CartService
from commerce.services.order_service import OrderService
from commerce.tests.conftest import make_category, make_product
from runtime.models.outbox_event import OutboxEvent
from runtime.models.processed_event import ProcessedEvent
from runtime.services.outbox_service import OutboxService
from taller.tests.factories import EmpresaFactory, RepuestoFactory


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def empresa(db):
    return EmpresaFactory(nombre_taller="MonteAzul", pais="CL")


@pytest.fixture
def empresa_b(db):
    return EmpresaFactory(nombre_taller="Otro Taller", pais="CL")


def make_cart(empresa, session_key="a" * 32):
    return CartService.get_or_create(empresa, session_key)


def fill_cart_and_checkout(empresa, session_key="a" * 32):
    cat = make_category(empresa)
    repuesto = RepuestoFactory(empresa=empresa, part_number="F-001",
                               precio_venta=Decimal("4990"), nombre="Filtro aceite")
    product = make_product(empresa, repuesto=repuesto, category=cat)
    cart = make_cart(empresa, session_key)
    CartService.add_item(cart, product, 2)
    return cart, product


# ── 1. Checkout crea Order + outbox atómicamente ──────────────────────────────

@pytest.mark.django_db
def test_checkout_creates_order_and_outbox_atomically(empresa):
    cart, _ = fill_cart_and_checkout(empresa)
    order = OrderService.create_from_cart(cart, {"name": "Juan", "email": "j@t.cl"})

    assert CommerceOrder.objects.filter(pk=order.pk).exists()
    outbox = OutboxEvent.objects.filter(
        aggregate_type="commerce_order",
        aggregate_id=str(order.pk),
        event_type="commerce.order.submitted",
    )
    assert outbox.count() == 1
    assert outbox.first().status == OutboxEvent.PENDING


# ── 2. Fallo en outbox revierte el Order ──────────────────────────────────────

@pytest.mark.django_db
def test_outbox_failure_reverts_order(empresa):
    cart, _ = fill_cart_and_checkout(empresa)

    with patch(
        "runtime.services.outbox_service.OutboxService.enqueue",
        side_effect=Exception("outbox error"),
    ):
        with pytest.raises(Exception, match="outbox error"):
            OrderService.create_from_cart(cart, {"name": "A", "email": "a@b.cl"})

    assert CommerceOrder.objects.filter(empresa=empresa).count() == 0


# ── 3. Consumer crea Documento PTS BORRADOR ───────────────────────────────────

@pytest.mark.django_db
def test_consumer_creates_pts_borrador(empresa):
    cart, _ = fill_cart_and_checkout(empresa)
    order = OrderService.create_from_cart(cart, {"name": "María García", "email": "m@t.cl"})

    OutboxService.process_pending(event_type="commerce.order.submitted")

    from taller.models.documento import Documento
    docs = Documento.objects.filter(empresa=empresa, tipo="PTS", estado="BORRADOR")
    assert docs.count() == 1
    doc = docs.first()
    assert doc.numero.startswith("PTS-")


# ── 4. Consumer crea líneas correctas ────────────────────────────────────────

@pytest.mark.django_db
def test_consumer_creates_lineas(empresa):
    cart, _ = fill_cart_and_checkout(empresa)
    order = OrderService.create_from_cart(cart, {"name": "Test", "email": "t@t.cl"})

    OutboxService.process_pending(event_type="commerce.order.submitted")

    from taller.models.documento import Documento
    from taller.models.lineas_documento import LineaRepuesto
    doc = Documento.objects.get(empresa=empresa, tipo="PTS", estado="BORRADOR")
    lineas = LineaRepuesto.objects.filter(documento=doc)
    assert lineas.count() == 1
    linea = lineas.first()
    assert linea.cantidad == 2


# ── 5. Precios/nombres congelados ────────────────────────────────────────────

@pytest.mark.django_db
def test_frozen_sku_name_price_in_linea(empresa):
    cart, product = fill_cart_and_checkout(empresa)
    order = OrderService.create_from_cart(cart, {"name": "Test", "email": "t@t.cl"})

    OutboxService.process_pending(event_type="commerce.order.submitted")

    from taller.models.documento import Documento
    from taller.models.lineas_documento import LineaRepuesto
    doc = Documento.objects.get(empresa=empresa, tipo="PTS", estado="BORRADOR")
    linea = LineaRepuesto.objects.get(documento=doc)

    assert linea.codigo == "F-001"
    assert linea.nombre == "Filtro aceite"
    assert linea.precio_unitario == Decimal("4990")
    assert linea.cantidad == 2


# ── 6. Idempotencia: reprocesar no duplica ───────────────────────────────────

@pytest.mark.django_db
def test_idempotent_consumer_no_duplicate(empresa):
    cart, _ = fill_cart_and_checkout(empresa)
    order = OrderService.create_from_cart(cart, {"name": "Test", "email": "t@t.cl"})

    OutboxService.process_pending(event_type="commerce.order.submitted")
    # Marcar el evento como PENDING de nuevo para forzar reintento
    OutboxEvent.objects.filter(aggregate_id=str(order.pk)).update(
        status=OutboxEvent.PENDING, attempts=0
    )
    OutboxService.process_pending(event_type="commerce.order.submitted")

    from taller.models.documento import Documento
    count = Documento.objects.filter(empresa=empresa, tipo="PTS").count()
    assert count == 1  # solo uno, no duplicado


# ── 7. Otro tenant no puede consumir datos cruzados ──────────────────────────

@pytest.mark.django_db
def test_tenant_isolation_in_consumer(empresa, empresa_b):
    cart, _ = fill_cart_and_checkout(empresa)
    order = OrderService.create_from_cart(cart, {"name": "Test A", "email": "a@a.cl"})

    # Procesar todo normalmente
    OutboxService.process_pending(event_type="commerce.order.submitted")

    from taller.models.documento import Documento
    # Solo empresa A tiene un Documento
    assert Documento.objects.filter(empresa=empresa, tipo="PTS").count() == 1
    assert Documento.objects.filter(empresa=empresa_b, tipo="PTS").count() == 0

    # Cliente creado pertenece a empresa A, no a empresa B
    from taller.models.clientes import Cliente
    assert not Cliente.objects.filter(empresa=empresa_b, email="a@a.cl").exists()


# ── 8. Evento inválido registra error y no crea Documento ────────────────────

@pytest.mark.django_db
def test_invalid_event_records_error(empresa):
    """
    Un evento con empresa_id inexistente no crea Documento y registra
    el error. El status vuelve a PENDING para reintento hasta MAX_ATTEMPTS.
    """
    event = OutboxEvent.objects.create(
        event_id=uuid.uuid4(),
        aggregate_type="commerce_order",
        aggregate_id="999",
        event_type="commerce.order.submitted",
        payload={"empresa_id": 999999, "buyer": {"full_name": "X", "email": "x@x.cl"},
                 "items": [{"sku": "A", "name": "B", "quantity": 1, "unit_price": "100",
                            "line_total": "100", "commerce_order_item_id": 1}],
                 "subtotal": "100", "tax_total": "0", "total": "100", "currency": "CLP"},
    )
    OutboxService.process_pending(event_type="commerce.order.submitted")
    event.refresh_from_db()

    assert event.attempts == 1
    assert event.last_error  # se registró el error
    assert "Empresa" in event.last_error or "DoesNotExist" in event.last_error

    from taller.models.documento import Documento
    assert Documento.objects.count() == 0


# ── 9. Reintentos incrementan attempts; FAILED tras MAX_ATTEMPTS ─────────────

@pytest.mark.django_db
def test_failed_event_increments_attempts():
    """
    Cada proceso_pending incrementa attempts.
    Tras MAX_ATTEMPTS (3), el evento queda en FAILED permanente.
    """
    from runtime.services.outbox_service import MAX_ATTEMPTS

    event = OutboxEvent.objects.create(
        event_id=uuid.uuid4(),
        aggregate_type="commerce_order",
        aggregate_id="0",
        event_type="commerce.order.submitted",
        payload={"empresa_id": 999999},  # payload inválido — empresa no existe
    )
    assert event.attempts == 0

    for _ in range(MAX_ATTEMPTS):
        OutboxService.process_pending(event_type="commerce.order.submitted")

    event.refresh_from_db()
    assert event.attempts == MAX_ATTEMPTS
    assert event.status == OutboxEvent.FAILED


# ── 10. Stock no cambia ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_stock_unchanged_after_consumer(empresa):
    cart, product = fill_cart_and_checkout(empresa)
    stock_antes = product.stock
    OrderService.create_from_cart(cart, {"name": "Test", "email": "t@t.cl"})
    OutboxService.process_pending(event_type="commerce.order.submitted")
    product.repuesto.refresh_from_db()
    assert product.repuesto.cantidad_stock == stock_antes


# ── 11. Ledger no recibe movimientos ─────────────────────────────────────────

@pytest.mark.django_db
def test_no_movimiento_inventario_created(empresa):
    from taller.models.movimiento_inventario import MovimientoInventario
    count_antes = MovimientoInventario.objects.filter(empresa=empresa).count()
    cart, _ = fill_cart_and_checkout(empresa)
    OrderService.create_from_cart(cart, {"name": "Test", "email": "t@t.cl"})
    OutboxService.process_pending(event_type="commerce.order.submitted")
    assert MovimientoInventario.objects.filter(empresa=empresa).count() == count_antes


# ── 12. Commerce no contiene imports ERP transaccionales ─────────────────────

def test_commerce_does_not_import_erp_transactional_models():
    """
    Ningún archivo bajo commerce/ debe importar los modelos ERP transaccionales
    (Documento, Cliente, LineaRepuesto, MovimientoInventario).
    Importar Empresa está permitido: es el objeto-tenant que Commerce necesita.
    """
    forbidden_modules = [
        "taller.models.documento",
        "taller.models.clientes",
        "taller.models.lineas_documento",
        "taller.models.movimiento_inventario",
    ]
    forbidden_names = [
        "from taller.models import Documento",
        "from taller.models import Cliente",
        "from taller.models import LineaRepuesto",
        "from taller.models import MovimientoInventario",
    ]
    commerce_root = Path(__file__).parent.parent.parent / "commerce"
    violations = []
    for py_file in commerce_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        text = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_modules + forbidden_names:
            if pattern in text:
                violations.append(f"{py_file.relative_to(commerce_root)}: {pattern!r}")

    assert not violations, (
        "Commerce importa modelos ERP transaccionales directamente:\n"
        + "\n".join(violations)
    )


# ── 13. Contract schema valida ────────────────────────────────────────────────

def test_contract_schema_valid_structure():
    """
    El archivo JSON del contrato tiene la estructura mínima requerida.
    No requiere jsonschema instalado — valida propiedades del propio schema.
    """
    schema_path = (
        Path(__file__).parent.parent.parent
        / "contracts/schemas/commerce.order.submitted.v1.schema.json"
    )
    assert schema_path.exists(), "Schema no encontrado"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema.get("type") == "object"
    required_fields = schema.get("required", [])
    for field in ["event_id", "empresa_id", "buyer", "items", "total", "currency"]:
        assert field in required_fields, f"Campo requerido faltante en schema: {field}"

    props = schema.get("properties", {})
    assert "buyer" in props
    assert "items" in props
    buyer_required = props["buyer"].get("required", [])
    assert "full_name" in buyer_required
    assert "email" in buyer_required


# ── 14. manage.py check limpio ───────────────────────────────────────────────

@pytest.mark.django_db
def test_manage_check_passes():
    out = io.StringIO()
    call_command("check", stdout=out, stderr=out)
    assert "no issues" in out.getvalue().lower()


# ── 15. Suites Commerce siguen verdes (smoke test de integración) ─────────────

@pytest.mark.django_db
def test_commerce_order_flow_still_works(empresa):
    """
    Smoke test: el flujo completo de carrito → pedido sigue funcionando
    después de introducir el outbox, sin romper la experiencia del usuario.
    """
    cart, product = fill_cart_and_checkout(empresa, session_key="b" * 32)
    order = OrderService.create_from_cart(cart, {
        "name": "Carlos Pérez",
        "email": "carlos@test.cl",
        "phone": "+56911111111",
        "shipping_address": "Av. Las Condes 1000",
        "notes": "",
    })

    assert order.pk is not None
    assert order.order_number.startswith("ORD-")
    assert order.total == Decimal("9980")

    assert OutboxEvent.objects.filter(
        aggregate_type="commerce_order",
        aggregate_id=str(order.pk),
    ).exists()

    # El carrito quedó vacío
    assert CartService.item_count(CartService.get_or_create(empresa, "b" * 32)) == 0
