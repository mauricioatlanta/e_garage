"""
Tests H1.2 — PaymentGateway protocol: WebPayGateway + BankTransferGateway sandbox.

1.  PaymentInitiation es un dataclass frozen con los campos correctos.
2.  PaymentConfirmation es un dataclass frozen con los campos correctos.
3.  PaymentGateway.resolve("webpay") devuelve una instancia de WebPayGateway.
4.  PaymentGateway.resolve("bank_transfer") devuelve BankTransferGateway.
5.  PaymentGateway.resolve con clave desconocida lanza KeyError.
6.  WebPayGateway.initiate llama a Transaction.create con los parámetros correctos.
7.  WebPayGateway.initiate devuelve PaymentInitiation con token y URL.
8.  WebPayGateway.confirm autorizado devuelve success=True y fields correctos.
9.  WebPayGateway.confirm fallido devuelve success=False.
10. WebPayGateway.confirm extrae card_last4 del card_detail.
11. BankTransferGateway.initiate devuelve PaymentInitiation sin I/O externo.
12. BankTransferGateway.initiate genera token único (bt_ prefix).
13. BankTransferGateway.confirm lanza NotImplementedError.
14. WebPayGateway usa sandbox credentials por defecto (TBK_PRODUCTION no configurado).
15. No existen imports ERP en commerce/payments/.
"""
import pathlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from commerce.payments.bank_transfer import BankTransferGateway
from commerce.payments.gateway import PaymentConfirmation, PaymentGateway, PaymentInitiation
from commerce.payments.webpay import WebPayGateway


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_create_response(token="01abcdef12345678", url="https://webpay.example.com/init"):
    r = MagicMock()
    r.token = token
    r.url = url
    return r


def _mock_commit_response(
    response_code=0,
    authorization_code="AUTH001",
    amount=9990,
    status="AUTHORIZED",
    buy_order="ORD-001",
    session_id="sess-001",
    card_number="XXXX1234",
):
    card = MagicMock()
    card.card_number = card_number

    r = MagicMock()
    r.response_code = response_code
    r.authorization_code = authorization_code
    r.amount = amount
    r.status = status
    r.buy_order = buy_order
    r.session_id = session_id
    r.payment_type_code = "VN"
    r.card_detail = card
    return r


# ── 1. PaymentInitiation dataclass ───────────────────────────────────────────

def test_payment_initiation_is_frozen_dataclass():
    now = datetime.now(tz=timezone.utc)
    p = PaymentInitiation(
        redirect_url="https://example.com/pay",
        gateway_token="TOKEN123",
        expires_at=now,
    )
    assert p.redirect_url == "https://example.com/pay"
    assert p.gateway_token == "TOKEN123"
    assert p.expires_at == now
    with pytest.raises((AttributeError, TypeError)):
        p.gateway_token = "OTHER"  # type: ignore[misc]


# ── 2. PaymentConfirmation dataclass ─────────────────────────────────────────

def test_payment_confirmation_is_frozen_dataclass():
    p = PaymentConfirmation(
        success=True,
        gateway_ref="REF001",
        authorization_code="AUTH001",
        card_last4="1234",
        amount=9990,
        raw_response={"response_code": 0},
    )
    assert p.success is True
    assert p.card_last4 == "1234"
    assert p.raw_response == {"response_code": 0}
    with pytest.raises((AttributeError, TypeError)):
        p.success = False  # type: ignore[misc]


# ── 3–5. PaymentGateway.resolve ──────────────────────────────────────────────

def test_resolve_webpay_returns_webpay_instance():
    gw = PaymentGateway.resolve("webpay")
    assert isinstance(gw, WebPayGateway)


def test_resolve_bank_transfer_returns_bank_transfer_instance():
    gw = PaymentGateway.resolve("bank_transfer")
    assert isinstance(gw, BankTransferGateway)


def test_resolve_unknown_key_raises_key_error():
    with pytest.raises(KeyError, match="no registrado"):
        PaymentGateway.resolve("nonexistent_gateway_xyz")


# ── 6–7. WebPayGateway.initiate ──────────────────────────────────────────────

def test_webpay_initiate_calls_transaction_create_with_correct_params():
    mock_create = _mock_create_response()
    with patch("commerce.payments.webpay.Transaction") as MockTx:
        MockTx.return_value.create.return_value = mock_create
        gw = WebPayGateway.from_settings()
        gw.initiate(
            buy_order="ORD-1-TEST001",
            session_id="sess-abc",
            amount=9990,
            return_url="https://example.com/return",
        )
        MockTx.return_value.create.assert_called_once_with(
            buy_order="ORD-1-TEST001",
            session_id="sess-abc",
            amount=9990,
            return_url="https://example.com/return",
        )


def test_webpay_initiate_returns_payment_initiation():
    mock_create = _mock_create_response(token="MYTOKEN", url="https://tbk.cl/init")
    with patch("commerce.payments.webpay.Transaction") as MockTx:
        MockTx.return_value.create.return_value = mock_create
        gw = WebPayGateway.from_settings()
        result = gw.initiate(
            buy_order="ORD-1-TEST002",
            session_id="sess-def",
            amount=15000,
            return_url="https://example.com/return",
        )

    assert isinstance(result, PaymentInitiation)
    assert result.gateway_token == "MYTOKEN"
    assert result.redirect_url == "https://tbk.cl/init"
    assert result.expires_at is not None


# ── 8–10. WebPayGateway.confirm ──────────────────────────────────────────────

def test_webpay_confirm_authorized_returns_success():
    mock_commit = _mock_commit_response(
        response_code=0,
        authorization_code="AUTH789",
        amount=9990,
        card_number="XXXX1234",
    )
    with patch("commerce.payments.webpay.Transaction") as MockTx:
        MockTx.return_value.commit.return_value = mock_commit
        gw = WebPayGateway.from_settings()
        result = gw.confirm("MYTOKEN")

    assert isinstance(result, PaymentConfirmation)
    assert result.success is True
    assert result.authorization_code == "AUTH789"
    assert result.gateway_ref == "AUTH789"
    assert result.amount == 9990
    assert result.raw_response["response_code"] == 0


def test_webpay_confirm_failed_returns_not_success():
    mock_commit = _mock_commit_response(
        response_code=-1,
        authorization_code="",
        status="FAILED",
        card_number="",
    )
    with patch("commerce.payments.webpay.Transaction") as MockTx:
        MockTx.return_value.commit.return_value = mock_commit
        gw = WebPayGateway.from_settings()
        result = gw.confirm("FAILTOKEN")

    assert result.success is False
    assert result.card_last4 == ""


def test_webpay_confirm_extracts_card_last4():
    mock_commit = _mock_commit_response(card_number="XXXX5678")
    with patch("commerce.payments.webpay.Transaction") as MockTx:
        MockTx.return_value.commit.return_value = mock_commit
        gw = WebPayGateway.from_settings()
        result = gw.confirm("TOKEN")

    assert result.card_last4 == "5678"


# ── 11–13. BankTransferGateway ───────────────────────────────────────────────

def test_bank_transfer_initiate_returns_payment_initiation():
    gw = BankTransferGateway.from_settings()
    result = gw.initiate(
        buy_order="ORD-1-BT001",
        session_id="sess-bt",
        amount=25000,
        return_url="https://example.com/return",
    )
    assert isinstance(result, PaymentInitiation)
    assert result.redirect_url != ""
    assert result.expires_at is not None


def test_bank_transfer_initiate_token_has_bt_prefix():
    gw = BankTransferGateway.from_settings()
    result = gw.initiate("ORD-001", "sess", 5000, "https://example.com/return")
    assert result.gateway_token.startswith("bt_")


def test_bank_transfer_initiate_tokens_are_unique():
    gw = BankTransferGateway.from_settings()
    tokens = {
        gw.initiate(f"ORD-{i}", f"sess-{i}", 1000, "https://example.com/return").gateway_token
        for i in range(10)
    }
    assert len(tokens) == 10


def test_bank_transfer_confirm_raises_not_implemented():
    gw = BankTransferGateway.from_settings()
    with pytest.raises(NotImplementedError):
        gw.confirm("any_token")


# ── 14. Sandbox por defecto ──────────────────────────────────────────────────

def test_webpay_uses_sandbox_by_default(settings):
    settings.TBK_PRODUCTION = False
    from transbank.common.integration_type import IntegrationType

    gw = WebPayGateway.from_settings()
    assert gw._options.integration_type == IntegrationType.TEST


# ── 15. Sin imports ERP en commerce/payments/ ────────────────────────────────

def test_no_erp_imports_in_payments_package():
    payments_dir = pathlib.Path("commerce/payments")
    for py_file in payments_dir.glob("*.py"):
        source = py_file.read_text()
        assert "from taller" not in source, (
            f"{py_file.name} importa desde taller — violación de boundary ERP/Commerce"
        )
        assert "import taller" not in source, (
            f"{py_file.name} importa taller directamente"
        )
