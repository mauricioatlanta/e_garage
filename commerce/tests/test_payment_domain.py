"""
Tests H1.1 — Dominio de pagos Commerce.

1.  CommerceOrder mantiene separado status y payment_status.
2.  Valores default correctos en CommerceOrder.
3.  Intentos consecutivos usan attempt_number 1, 2, 3.
4.  No se repite attempt_number por order.
5.  Dos órdenes pueden tener attempt_number=1.
6.  Tenant inconsistente lanza ValidationError.
7.  Amount cero o negativo es inválido.
8.  card_last4 inválido es rechazado.
9.  PaymentAttempt no puede editarse.
10. PaymentAttempt no puede eliminarse.
11. CommercePaymentTransaction conserva snapshot raw_response.
12. No existen imports ERP en commerce/models/payment.py.
13. Migración solo modifica tablas Commerce.
14. Admin no permite add/change/delete manual.
15. Suites Commerce y Runtime siguen verdes [implícito en esta ejecución].
"""
import pathlib
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from commerce.models.order import CommerceOrder
from commerce.models.payment import CommercePaymentTransaction, PaymentAttempt


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def empresa(db):
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(nombre_taller="MonteAzul", pais="CL")


@pytest.fixture
def empresa_b(db):
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(nombre_taller="Otro Taller", pais="CL")


def _make_order(empresa, suffix="AAAABBBB"):
    return CommerceOrder.objects.create(
        empresa=empresa,
        order_number=f"ORD-{empresa.pk}-{suffix}",
        customer_name="Test Cliente",
        customer_email="test@example.com",
        total=Decimal("9990"),
    )


def _make_attempt(order, status=PaymentAttempt.INITIATED, amount=9990, **kwargs):
    return PaymentAttempt.objects.create(
        empresa=order.empresa,
        order=order,
        gateway="webpay",
        status=status,
        amount=amount,
        **kwargs,
    )


# ── 1. status logístico y payment_status son ortogonales ─────────────────────


def test_order_status_and_payment_status_are_independent(db, empresa):
    order = _make_order(empresa, "INDEP001")
    order.status = CommerceOrder.SHIPPED
    order.payment_status = CommerceOrder.PAYMENT_PAID
    order.save(update_fields=["status", "payment_status"])
    order.refresh_from_db()
    assert order.status == CommerceOrder.SHIPPED
    assert order.payment_status == CommerceOrder.PAYMENT_PAID


# ── 2. Valores default correctos ─────────────────────────────────────────────


def test_order_payment_field_defaults(db, empresa):
    order = _make_order(empresa, "DEFLT001")
    assert order.status == CommerceOrder.PENDING
    assert order.payment_status == CommerceOrder.PAYMENT_NO_PAYMENT
    assert order.payment_method == ""
    assert order.payment_gateway_ref == ""
    assert order.paid_at is None


# ── 3. Intentos consecutivos: attempt_number 1, 2, 3 ─────────────────────────


def test_payment_attempts_auto_number_sequentially(db, empresa):
    order = _make_order(empresa, "SEQ0001A")
    a1 = _make_attempt(order)
    a2 = _make_attempt(order)
    a3 = _make_attempt(order)
    assert a1.attempt_number == 1
    assert a2.attempt_number == 2
    assert a3.attempt_number == 3


# ── 4. No se repite attempt_number por la misma order ────────────────────────


def test_attempt_number_unique_per_order(db, empresa):
    order = _make_order(empresa, "UNIQ001A")
    PaymentAttempt.objects.create(
        empresa=empresa, order=order, attempt_number=1,
        gateway="webpay", status=PaymentAttempt.INITIATED, amount=9990,
    )
    with pytest.raises(IntegrityError):
        PaymentAttempt.objects.create(
            empresa=empresa, order=order, attempt_number=1,
            gateway="webpay", status=PaymentAttempt.FAILED, amount=9990,
        )


# ── 5. Dos órdenes distintas pueden tener attempt_number=1 ───────────────────


def test_attempt_number_1_allowed_in_multiple_orders(db, empresa):
    order_a = _make_order(empresa, "ORDAA001")
    order_b = _make_order(empresa, "ORDAB001")
    a = PaymentAttempt.objects.create(
        empresa=empresa, order=order_a, attempt_number=1,
        gateway="webpay", status=PaymentAttempt.INITIATED, amount=5000,
    )
    b = PaymentAttempt.objects.create(
        empresa=empresa, order=order_b, attempt_number=1,
        gateway="webpay", status=PaymentAttempt.INITIATED, amount=7000,
    )
    assert a.attempt_number == 1
    assert b.attempt_number == 1


# ── 6. Tenant inconsistente lanza ValidationError ────────────────────────────


def test_attempt_with_wrong_tenant_raises(db, empresa, empresa_b):
    order = _make_order(empresa, "TENNT01A")
    attempt = PaymentAttempt(
        empresa=empresa_b, order=order,
        gateway="webpay", status=PaymentAttempt.INITIATED, amount=9990,
    )
    with pytest.raises(ValidationError):
        attempt.full_clean()


def test_transaction_with_wrong_tenant_raises(db, empresa, empresa_b):
    order = _make_order(empresa, "TENNT01B")
    tx = CommercePaymentTransaction(
        empresa=empresa_b, order=order,
        gateway="webpay", status=CommercePaymentTransaction.INITIATED, amount=9990,
    )
    with pytest.raises(ValidationError):
        tx.full_clean()


# ── 7. Amount cero o negativo es inválido ────────────────────────────────────


@pytest.mark.parametrize("bad_amount", [0, -1, -9999])
def test_payment_attempt_amount_must_be_positive(db, empresa, bad_amount):
    order = _make_order(empresa, "AMNT001A")
    attempt = PaymentAttempt(
        empresa=empresa, order=order,
        gateway="webpay", status=PaymentAttempt.INITIATED, amount=bad_amount,
    )
    with pytest.raises(ValidationError):
        attempt.full_clean()


@pytest.mark.parametrize("bad_amount", [0, -1])
def test_transaction_amount_must_be_positive(db, empresa, bad_amount):
    order = _make_order(empresa, "AMNT001B")
    tx = CommercePaymentTransaction(
        empresa=empresa, order=order,
        gateway="webpay", status=CommercePaymentTransaction.INITIATED, amount=bad_amount,
    )
    with pytest.raises(ValidationError):
        tx.full_clean()


# ── 8. card_last4 inválido es rechazado ──────────────────────────────────────


@pytest.mark.parametrize("bad_last4", ["12", "abcd", "12345", "123a", " 234"])
def test_card_last4_invalid_is_rejected(db, empresa, bad_last4):
    order = _make_order(empresa, "CARD001A")
    tx = CommercePaymentTransaction(
        empresa=empresa, order=order, gateway="webpay",
        status=CommercePaymentTransaction.INITIATED,
        amount=9990, card_last4=bad_last4,
    )
    with pytest.raises(ValidationError):
        tx.full_clean()


@pytest.mark.parametrize("good_last4", ["", "1234", "0000", "9999"])
def test_card_last4_valid_values_accepted(db, empresa, good_last4):
    order = _make_order(empresa, "CARD001B")
    tx = CommercePaymentTransaction(
        empresa=empresa, order=order, gateway="webpay",
        status=CommercePaymentTransaction.INITIATED,
        amount=9990, card_last4=good_last4,
        raw_response={},
    )
    tx.full_clean()  # no debe lanzar


# ── 9. PaymentAttempt no puede editarse ──────────────────────────────────────


def test_payment_attempt_is_immutable_on_edit(db, empresa):
    order = _make_order(empresa, "IMMUT01A")
    attempt = _make_attempt(order)
    assert attempt.pk is not None
    attempt.gateway = "bank_transfer"
    with pytest.raises(ValidationError, match="inmutable"):
        attempt.full_clean()


# ── 10. PaymentAttempt no puede eliminarse ───────────────────────────────────


def test_payment_attempt_cannot_be_deleted(db, empresa):
    order = _make_order(empresa, "DELET01A")
    attempt = _make_attempt(order)
    with pytest.raises(TypeError, match="inmutable"):
        attempt.delete()


# ── 11. CommercePaymentTransaction conserva snapshot ─────────────────────────


def test_payment_transaction_preserves_raw_response(db, empresa):
    order = _make_order(empresa, "SNAP001A")
    snapshot = {
        "response_code": 0,
        "status": "AUTHORIZED",
        "authorization_code": "ABC123",
        "amount": 9990,
        "card_detail": {"card_number": "XXXX1234"},
    }
    tx = CommercePaymentTransaction.objects.create(
        empresa=empresa, order=order,
        gateway="webpay",
        status=CommercePaymentTransaction.AUTHORIZED,
        amount=9990,
        gateway_ref="ABC123",
        raw_response=snapshot,
        card_last4="1234",
    )
    tx.refresh_from_db()
    assert tx.raw_response == snapshot
    assert tx.card_last4 == "1234"
    assert tx.gateway_ref == "ABC123"
    assert tx.initiated_at == tx.created_at


# ── 12. No existen imports ERP en commerce/models/payment.py ─────────────────


def test_no_erp_imports_in_payment_model():
    source = pathlib.Path("commerce/models/payment.py").read_text()
    assert "from taller" not in source, (
        "payment.py importa desde taller — violación de boundary ERP/Commerce"
    )
    assert "import taller" not in source, (
        "payment.py importa taller directamente — violación de boundary"
    )


# ── 13. Migración solo modifica tablas Commerce ──────────────────────────────


def test_migration_only_touches_commerce_tables():
    migrations_dir = pathlib.Path("commerce/migrations")
    migration_files = sorted(migrations_dir.glob("0005_*.py"))
    assert migration_files, "Migración 0005 no encontrada en commerce/migrations/"
    content = migration_files[0].read_text()
    assert "CommercePaymentTransaction" in content
    assert "PaymentAttempt" in content
    erp_business_tables = ["documento", "repuesto", "cliente", "tecnico", "suscripcion"]
    for table in erp_business_tables:
        assert table not in content.lower(), (
            f"La migración 0005 referencia la tabla ERP '{table}'"
        )


# ── 14. Admin no permite add/change/delete manual ────────────────────────────


def test_admin_is_read_only_for_payment_models():
    from unittest.mock import MagicMock
    from django.contrib.admin.sites import AdminSite
    from commerce.admin import CommercePaymentTransactionAdmin, PaymentAttemptAdmin

    site = AdminSite()
    request = MagicMock()

    for AdminClass, Model in [
        (CommercePaymentTransactionAdmin, CommercePaymentTransaction),
        (PaymentAttemptAdmin, PaymentAttempt),
    ]:
        admin_instance = AdminClass(Model, site)
        assert admin_instance.has_add_permission(request) is False, (
            f"{AdminClass.__name__} no debe permitir add"
        )
        assert admin_instance.has_change_permission(request) is False, (
            f"{AdminClass.__name__} no debe permitir change"
        )
        assert admin_instance.has_delete_permission(request) is False, (
            f"{AdminClass.__name__} no debe permitir delete"
        )
        assert admin_instance.get_actions(request) == {}, (
            f"{AdminClass.__name__} no debe tener acciones masivas"
        )
