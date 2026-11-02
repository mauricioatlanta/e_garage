"""
Tests H2 — CommercePaymentService.

1.  initiate() crea PaymentAttempt con status=INITIATED y los campos correctos.
2.  initiate() actualiza order.payment_status a PAYMENT_INITIATED (en BD y en memoria).
3.  initiate() guarda gateway_key en order.payment_method.
4.  initiate() devuelve el PaymentInitiation producido por el gateway.
5.  initiate() en pedido ya PAID lanza PaymentAlreadyAuthorizedError.
6.  Cada llamada a initiate() crea un PaymentAttempt nuevo (reintentos numerados).
7.  confirm() autorizado actualiza el PaymentAttempt a AUTHORIZED.
8.  confirm() autorizado crea CommercePaymentTransaction con los datos correctos.
9.  confirm() autorizado actualiza order a PAYMENT_PAID con paid_at y gateway_ref.
10. confirm() autorizado emite OutboxEvent commerce.order.paid con schema v1.0.0.
11. confirm() autorizado devuelve True.
12. confirm() fallido actualiza el PaymentAttempt a FAILED con error_message.
13. confirm() fallido emite OutboxEvent commerce.order.payment_failed.
14. confirm() fallido devuelve False.
15. confirm() fallido NO crea CommercePaymentTransaction.
16. confirm() fallido NO cambia order.payment_status (sigue en INITIATED).
17. confirm() en pedido ya PAID lanza PaymentAlreadyAuthorizedError (idempotencia).
18. confirm() con token desconocido lanza PaymentAttemptNotFoundError.
19. confirm() hace rollback completo si _enqueue_event lanza excepción.
20. No existen imports ERP en commerce/services/payment_service.py.
"""
from __future__ import annotations

import pathlib
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from commerce.models.order import CommerceOrder
from commerce.models.payment import CommercePaymentTransaction, PaymentAttempt
from commerce.payments.gateway import PaymentConfirmation, PaymentInitiation
from commerce.services.payment_service import (
    CommercePaymentService,
    PaymentAlreadyAuthorizedError,
    PaymentAttemptNotFoundError,
)
from runtime.models.outbox_event import OutboxEvent


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def empresa(db):
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(nombre_taller="MonteAzulTest", pais="CL")


@pytest.fixture
def order(db, empresa):
    return CommerceOrder.objects.create(
        empresa=empresa,
        order_number=f"ORD-{empresa.pk}-SVCTEST1",
        customer_name="Cliente Test",
        customer_email="cliente@test.com",
        total=Decimal("9990"),
        session_key="sess-svc-001",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

RETURN_URL = "https://monteazul.cl/storefront/monteazul/payment/return/"
GW_KEY = "webpay"


def _initiation(token="TKWP001"):
    return PaymentInitiation(
        redirect_url=f"https://webpay.example.com?token_ws={token}",
        gateway_token=token,
        expires_at=datetime.now(tz=timezone.utc),
    )


def _confirmation_success(
    gateway_ref="AUTH123456", amount=9990, card_last4="1234"
):
    return PaymentConfirmation(
        success=True,
        gateway_ref=gateway_ref,
        authorization_code=gateway_ref,
        card_last4=card_last4,
        amount=amount,
        raw_response={
            "response_code": 0,
            "authorization_code": gateway_ref,
            "status": "AUTHORIZED",
            "amount": float(amount),
            "card_number": f"XXXX{card_last4}",
        },
    )


def _confirmation_failure(response_code=-1):
    return PaymentConfirmation(
        success=False,
        gateway_ref="",
        authorization_code="",
        card_last4="",
        amount=9990,
        raw_response={
            "response_code": response_code,
            "authorization_code": "",
            "status": "FAILED",
        },
    )


def _mock_gateway(initiation=None, confirmation=None):
    gw = MagicMock()
    gw.initiate.return_value = initiation or _initiation()
    gw.confirm.return_value = confirmation or _confirmation_success()
    return gw


def _patch_gw(gw):
    """Context manager que parchea PaymentGateway.resolve para devolver gw."""
    return patch(
        "commerce.services.payment_service.PaymentGateway",
        **{"resolve.return_value": gw},
    )


# ── 1–6. initiate() ───────────────────────────────────────────────────────────


def test_initiate_creates_payment_attempt(db, empresa, order):
    gw = _mock_gateway(initiation=_initiation("TK_INIT_01"))
    with _patch_gw(gw):
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)

    attempt = PaymentAttempt.objects.get(order=order)
    assert attempt.status == PaymentAttempt.INITIATED
    assert attempt.gateway == GW_KEY
    assert attempt.gateway_token == "TK_INIT_01"
    assert attempt.amount == 9990
    assert attempt.empresa == empresa


def test_initiate_updates_order_payment_status_in_db(db, empresa, order):
    gw = _mock_gateway()
    with _patch_gw(gw):
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)

    order.refresh_from_db()
    assert order.payment_status == CommerceOrder.PAYMENT_INITIATED


def test_initiate_updates_order_payment_status_in_memory(db, empresa, order):
    gw = _mock_gateway()
    with _patch_gw(gw):
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)

    assert order.payment_status == CommerceOrder.PAYMENT_INITIATED


def test_initiate_sets_payment_method(db, empresa, order):
    gw = _mock_gateway()
    with _patch_gw(gw):
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)

    order.refresh_from_db()
    assert order.payment_method == GW_KEY


def test_initiate_returns_payment_initiation(db, empresa, order):
    expected = _initiation("TK_RETURN")
    gw = _mock_gateway(initiation=expected)
    with _patch_gw(gw):
        result = CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)

    assert isinstance(result, PaymentInitiation)
    assert result.gateway_token == "TK_RETURN"


def test_initiate_on_paid_order_raises(db, empresa, order):
    order.payment_status = CommerceOrder.PAYMENT_PAID
    order.save(update_fields=["payment_status"])

    with pytest.raises(PaymentAlreadyAuthorizedError):
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)


def test_initiate_creates_new_attempt_per_retry(db, empresa, order):
    gw = _mock_gateway()
    gw.initiate.side_effect = [
        _initiation("TK_RETRY_1"),
        _initiation("TK_RETRY_2"),
        _initiation("TK_RETRY_3"),
    ]
    with _patch_gw(gw):
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)
        CommercePaymentService.initiate(order, GW_KEY, RETURN_URL)

    attempts = PaymentAttempt.objects.filter(order=order).order_by("attempt_number")
    assert attempts.count() == 3
    assert list(attempts.values_list("attempt_number", flat=True)) == [1, 2, 3]
    assert list(attempts.values_list("gateway_token", flat=True)) == [
        "TK_RETRY_1", "TK_RETRY_2", "TK_RETRY_3"
    ]


# ── 7–11. confirm() autorizado ────────────────────────────────────────────────


def _setup_initiated_order(order, empresa, token="TK_CONF_OK"):
    """Prepara el order con un PaymentAttempt INITIATED listo para confirm()."""
    PaymentAttempt.objects.create(
        empresa=empresa,
        order=order,
        gateway=GW_KEY,
        status=PaymentAttempt.INITIATED,
        amount=int(order.total),
        gateway_token=token,
    )
    CommerceOrder.objects.filter(pk=order.pk).update(
        payment_status=CommerceOrder.PAYMENT_INITIATED,
        payment_method=GW_KEY,
    )
    order.payment_status = CommerceOrder.PAYMENT_INITIATED
    order.payment_method = GW_KEY


def test_confirm_authorized_updates_attempt_to_authorized(db, empresa, order):
    _setup_initiated_order(order, empresa)
    gw = _mock_gateway(confirmation=_confirmation_success(gateway_ref="AUTH001"))

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_CONF_OK")

    attempt = PaymentAttempt.objects.get(order=order)
    assert attempt.status == PaymentAttempt.AUTHORIZED
    assert attempt.gateway_ref == "AUTH001"
    assert attempt.raw_status == "AUTHORIZED"
    assert attempt.completed_at is not None


def test_confirm_authorized_creates_transaction(db, empresa, order):
    _setup_initiated_order(order, empresa)
    gw = _mock_gateway(
        confirmation=_confirmation_success(
            gateway_ref="AUTH002", amount=9990, card_last4="5678"
        )
    )

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_CONF_OK")

    tx = CommercePaymentTransaction.objects.get(order=order)
    assert tx.gateway == GW_KEY
    assert tx.gateway_ref == "AUTH002"
    assert tx.status == CommercePaymentTransaction.AUTHORIZED
    assert tx.amount == 9990
    assert tx.card_last4 == "5678"
    assert tx.confirmed_at is not None
    assert tx.empresa == empresa


def test_confirm_authorized_updates_order_to_paid(db, empresa, order):
    _setup_initiated_order(order, empresa)
    gw = _mock_gateway(confirmation=_confirmation_success(gateway_ref="AUTH003"))

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_CONF_OK")

    order.refresh_from_db()
    assert order.payment_status == CommerceOrder.PAYMENT_PAID
    assert order.payment_gateway_ref == "AUTH003"
    assert order.paid_at is not None


def test_confirm_authorized_emits_order_paid_event(db, empresa, order):
    _setup_initiated_order(order, empresa)
    gw = _mock_gateway(confirmation=_confirmation_success(gateway_ref="AUTH004"))

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_CONF_OK")

    event = OutboxEvent.objects.get(event_type="commerce.order.paid")
    assert event.aggregate_type == "commerce_order"
    assert event.aggregate_id == str(order.pk)
    payload = event.payload
    assert payload["order_number"] == order.order_number
    assert payload["empresa_id"] == empresa.pk
    assert payload["gateway_ref"] == "AUTH004"
    assert payload["currency"] == "CLP"
    assert payload["schema_version"] == "1.0.0"
    assert "paid_at" in payload


def test_confirm_authorized_returns_true(db, empresa, order):
    _setup_initiated_order(order, empresa)
    gw = _mock_gateway(confirmation=_confirmation_success())

    with _patch_gw(gw):
        result = CommercePaymentService.confirm(order, "TK_CONF_OK")

    assert result is True


# ── 12–16. confirm() fallido ──────────────────────────────────────────────────


def test_confirm_failed_updates_attempt_to_failed(db, empresa, order):
    _setup_initiated_order(order, empresa, token="TK_FAIL_01")
    gw = _mock_gateway(confirmation=_confirmation_failure())

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_FAIL_01")

    attempt = PaymentAttempt.objects.get(order=order)
    assert attempt.status == PaymentAttempt.FAILED
    assert attempt.completed_at is not None
    assert attempt.error_message != ""


def test_confirm_failed_emits_payment_failed_event(db, empresa, order):
    _setup_initiated_order(order, empresa, token="TK_FAIL_02")
    gw = _mock_gateway(confirmation=_confirmation_failure(response_code=-2))

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_FAIL_02")

    event = OutboxEvent.objects.get(event_type="commerce.order.payment_failed")
    assert event.aggregate_type == "commerce_order"
    payload = event.payload
    assert payload["order_number"] == order.order_number
    assert payload["gateway"] == GW_KEY
    assert payload["schema_version"] == "1.0.0"
    assert "error_message" in payload


def test_confirm_failed_returns_false(db, empresa, order):
    _setup_initiated_order(order, empresa, token="TK_FAIL_03")
    gw = _mock_gateway(confirmation=_confirmation_failure())

    with _patch_gw(gw):
        result = CommercePaymentService.confirm(order, "TK_FAIL_03")

    assert result is False


def test_confirm_failed_does_not_create_transaction(db, empresa, order):
    _setup_initiated_order(order, empresa, token="TK_FAIL_04")
    gw = _mock_gateway(confirmation=_confirmation_failure())

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_FAIL_04")

    assert not CommercePaymentTransaction.objects.filter(order=order).exists()


def test_confirm_failed_does_not_change_order_payment_status(db, empresa, order):
    _setup_initiated_order(order, empresa, token="TK_FAIL_05")
    gw = _mock_gateway(confirmation=_confirmation_failure())

    with _patch_gw(gw):
        CommercePaymentService.confirm(order, "TK_FAIL_05")

    order.refresh_from_db()
    assert order.payment_status == CommerceOrder.PAYMENT_INITIATED


# ── 17–19. Idempotencia, error y rollback ─────────────────────────────────────


def test_confirm_already_paid_raises(db, empresa, order):
    order.payment_status = CommerceOrder.PAYMENT_PAID
    order.save(update_fields=["payment_status"])

    with pytest.raises(PaymentAlreadyAuthorizedError):
        CommercePaymentService.confirm(order, "any_token")


def test_confirm_unknown_token_raises(db, empresa, order):
    with pytest.raises(PaymentAttemptNotFoundError):
        CommercePaymentService.confirm(order, "TOKEN_INEXISTENTE")


def test_confirm_atomic_rollback_on_enqueue_failure(db, empresa, order):
    _setup_initiated_order(order, empresa, token="TK_ATOMIC")
    gw = _mock_gateway(confirmation=_confirmation_success(gateway_ref="AUTH_ATOMIC"))

    with _patch_gw(gw):
        with patch(
            "commerce.services.payment_service._enqueue_event",
            side_effect=RuntimeError("DB error en outbox"),
        ):
            with pytest.raises(RuntimeError, match="DB error en outbox"):
                CommercePaymentService.confirm(order, "TK_ATOMIC")

    # Rollback: attempt sigue INITIATED, sin transaction, order sigue INITIATED
    attempt = PaymentAttempt.objects.get(order=order, gateway_token="TK_ATOMIC")
    assert attempt.status == PaymentAttempt.INITIATED
    assert attempt.completed_at is None
    assert not CommercePaymentTransaction.objects.filter(order=order).exists()
    order.refresh_from_db()
    assert order.payment_status == CommerceOrder.PAYMENT_INITIATED


# ── 20. Boundary ERP ──────────────────────────────────────────────────────────


def test_no_erp_imports_in_payment_service():
    source = pathlib.Path("commerce/services/payment_service.py").read_text()
    assert "from taller" not in source, (
        "payment_service.py importa desde taller — violación de boundary ERP/Commerce (ADR-004)"
    )
    assert "import taller" not in source, (
        "payment_service.py importa taller directamente"
    )
