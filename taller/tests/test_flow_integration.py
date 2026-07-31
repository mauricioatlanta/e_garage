import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion_transaccion import SuscripcionTransaccion
from taller.services.suscripcion_transaccion_service import create_gateway_transaction
from taller.utils.flow_helper import create_payment_order, get_flow_signature


User = get_user_model()


class DummyResponse:
    def __init__(self, *, status_code=200, data=None, text=""):
        self.status_code = status_code
        self._data = data or {}
        self.text = text

    def json(self):
        return self._data


class DummyFlowSession:
    def __init__(self, response):
        self.response = response
        self.last_post_url = None
        self.last_post_data = None
        self.last_timeout = None

    def post(self, url, data=None, timeout=None):
        self.last_post_url = url
        self.last_post_data = data
        self.last_timeout = timeout
        return self.response


@pytest.fixture(autouse=True)
def _flow_settings(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.FLOW_API_KEY = "flow-api-key"
    settings.FLOW_SECRET_KEY = "flow-secret"
    settings.FLOW_API_URL = "https://sandbox.flow.cl/api"
    settings.FLOW_ENABLED = True
    settings.FLOW_TIMEOUT = 15
    media_root = Path("C:/Users/Mauricio/.codex/memories/tmp_test_media_flow")
    shutil.rmtree(media_root, ignore_errors=True)
    media_root.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_root)
    yield
    shutil.rmtree(media_root, ignore_errors=True)


def _empresa(username="flow-user", email="flow@example.com", pais="CL"):
    from taller.tests.factories import EmpresaFactory
    empresa = EmpresaFactory(
        nombre_taller=f"Taller {username}",
        email=email,
        telefono="+56911112222",
        pais=pais,
        plan="trial",
        suscripcion_activa=False,
        fecha_inicio=timezone.now() - timedelta(days=35),
        fecha_fin=timezone.now() - timedelta(days=1),
        valor_mensual=Decimal("0.00"),
    )
    return empresa.user, empresa


@pytest.mark.django_db
def test_get_flow_signature_matches_expected_value(settings):
    settings.FLOW_SECRET_KEY = "flow-secret"

    signature = get_flow_signature(
        {
            "apiKey": "abc",
            "amount": 5000,
            "currency": "CLP",
        }
    )

    assert signature == "ba4dc7fb4197cfa5d5d496a6e05bb70500ffa8c6b9168b8baa81020586e232c9"


@pytest.mark.django_db
def test_create_payment_order_persists_flow_token():
    _user, empresa = _empresa(username="flow-create", email="flow-create@example.com")
    transaccion = create_gateway_transaction(
        empresa=empresa,
        source_type="flow",
        payment_method="flow",
        amount=Decimal("10000.00"),
        currency="CLP",
        billing_cycle="mensual",
        plan_code="basic",
        reference="SUB-TEST-001",
        customer_email=empresa.email,
        description="Suscripcion eGarage - Mensual",
        gateway_payload={"gateway": "flow"},
    )

    session = DummyFlowSession(
        DummyResponse(
            data={
                "token": "FLOW-TOKEN-123",
                "url": "https://www.flow.cl/app/web/pay.php",
                "flowOrder": 12345,
            }
        )
    )

    checkout_url = create_payment_order(
        transaccion,
        return_url="https://egarage.cl/flow/return/",
        confirmation_url="https://egarage.cl/webhooks/flow/",
        session=session,
    )

    transaccion.refresh_from_db()

    assert session.last_post_url == "https://sandbox.flow.cl/api/payment/create"
    assert session.last_post_data["commerceOrder"] == "SUB-TEST-001"
    assert session.last_post_data["urlReturn"] == "https://egarage.cl/flow/return/"
    assert session.last_post_data["urlConfirmation"] == "https://egarage.cl/webhooks/flow/"
    assert checkout_url == "https://www.flow.cl/app/web/pay.php?token=FLOW-TOKEN-123"
    assert transaccion.external_transaction_id == "FLOW-TOKEN-123"
    assert transaccion.checkout_url == checkout_url
    assert transaccion.gateway_payload["flow_create_response"]["flowOrder"] == 12345


@pytest.mark.django_db
def test_start_flow_payment_creates_transaction_and_redirects(client, monkeypatch):
    user, _empresa_obj = _empresa(username="flow-start", email="flow-start@example.com")
    client.force_login(user)

    monkeypatch.setattr(
        "taller.views_extra.payment_views.create_payment_order",
        lambda transaccion, **kwargs: "https://www.flow.cl/app/web/pay.php?token=FLOW-REDIRECT",
    )

    response = client.post("/cl/es/suscripcion/pago/flow/", {"plan": "mensual"})

    assert response.status_code == 302
    assert response["Location"] == "https://www.flow.cl/app/web/pay.php?token=FLOW-REDIRECT"

    transaccion = SuscripcionTransaccion.objects.get(source_type="flow")
    assert transaccion.payment_method == "flow"
    assert transaccion.billing_cycle == "mensual"
    assert transaccion.plan_code == "basic"
    assert transaccion.customer_email == "flow-start@example.com"


@pytest.mark.django_db
def test_flow_webhook_approves_transaction_idempotently(client, monkeypatch):
    monkeypatch.setattr(
        "taller.utils.notificaciones_suscripcion.notificar_nueva_suscripcion",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "taller.utils.notificaciones_suscripcion.notificar_cambio_plan",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "taller.utils.notificaciones_suscripcion.notificar_renovacion_exitosa",
        lambda **kwargs: None,
    )

    _user, empresa = _empresa(username="flow-webhook", email="flow-webhook@example.com")
    transaccion = create_gateway_transaction(
        empresa=empresa,
        source_type="flow",
        payment_method="flow",
        amount=Decimal("55000.00"),
        currency="CLP",
        billing_cycle="semestral",
        plan_code="premium",
        reference="SUB-WEBHOOK-001",
        external_transaction_id="FLOW-TOKEN-OK",
        customer_email=empresa.email,
        description="Suscripcion eGarage - Semestral",
        gateway_payload={"gateway": "flow"},
    )

    monkeypatch.setattr(
        "taller.views_extra.payment_views.get_payment_status",
        lambda token: {
            "token": token,
            "commerceOrder": "SUB-WEBHOOK-001",
            "status": 2,
            "amount": 55000,
            "currency": "CLP",
            "payer": empresa.email,
        },
    )

    response = client.post("/webhooks/flow/", {"token": "FLOW-TOKEN-OK"})
    assert response.status_code == 200

    empresa.refresh_from_db()
    transaccion.refresh_from_db()
    first_fecha_fin = empresa.fecha_fin

    assert transaccion.status == "approved"
    assert transaccion.processed_by == "flow_webhook"
    assert transaccion.subscription_applied_at is not None
    assert empresa.suscripcion_activa is True
    assert empresa.plan == "premium"
    assert empresa.valor_mensual == Decimal("55000.00")
    assert empresa.fecha_fin > timezone.now() + timedelta(days=170)

    second_response = client.post("/webhooks/flow/", {"token": "FLOW-TOKEN-OK"})
    assert second_response.status_code == 200

    empresa.refresh_from_db()
    transaccion.refresh_from_db()

    assert empresa.fecha_fin == first_fecha_fin
    assert transaccion.status == "approved"
