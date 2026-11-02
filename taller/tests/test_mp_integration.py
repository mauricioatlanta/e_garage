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
from taller.utils.mp_helper import create_mp_preference


User = get_user_model()


class DummyResponse:
    def __init__(self, *, status_code=200, data=None, text=""):
        self.status_code = status_code
        self._data = data or {}
        self.text = text

    def json(self):
        return self._data


class DummyMPSession:
    def __init__(self, response):
        self.response = response
        self.last_post_url = None
        self.last_post_json = None
        self.last_headers = None
        self.last_timeout = None

    def post(self, url, json=None, headers=None, timeout=None):
        self.last_post_url = url
        self.last_post_json = json
        self.last_headers = headers
        self.last_timeout = timeout
        return self.response


@pytest.fixture(autouse=True)
def _mp_settings(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.MP_ACCESS_TOKEN = "mp-access-token"
    settings.MP_PUBLIC_KEY = "mp-public-key"
    settings.MP_ENABLED = True
    settings.MP_URL_SUCCESS = "https://egarage.cl/mp/return/"
    settings.MP_URL_FAILURE = "https://egarage.cl/mp/return/"
    settings.MP_URL_PENDING = "https://egarage.cl/mp/return/"
    settings.MP_URL_WEBHOOK = "https://egarage.cl/webhooks/mercadopago/"
    settings.MP_TIMEOUT = 15
    media_root = Path("C:/Users/Mauricio/.codex/memories/tmp_test_media_mp")
    shutil.rmtree(media_root, ignore_errors=True)
    media_root.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_root)
    yield
    shutil.rmtree(media_root, ignore_errors=True)


def _empresa(username="mp-user", email="mp@example.com", pais="CL"):
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
def test_create_mp_preference_persists_preference_id():
    _user, empresa = _empresa(username="mp-create", email="mp-create@example.com")
    transaccion = create_gateway_transaction(
        empresa=empresa,
        source_type="mercadopago",
        payment_method="mercadopago",
        amount=Decimal("10000.00"),
        currency="CLP",
        billing_cycle="mensual",
        plan_code="basic",
        reference="",
        customer_email=empresa.email,
        description="Suscripcion eGarage - Mensual",
        gateway_payload={"gateway": "mercadopago"},
    )

    session = DummyMPSession(
        DummyResponse(
            status_code=201,
            data={
                "id": "PREF-123",
                "init_point": "https://www.mercadopago.cl/checkout/v1/redirect?pref_id=PREF-123",
            },
        )
    )

    init_point = create_mp_preference(
        transaccion,
        success_url="https://egarage.cl/mp/return/",
        failure_url="https://egarage.cl/mp/return/",
        pending_url="https://egarage.cl/mp/return/",
        webhook_url="https://egarage.cl/webhooks/mercadopago/",
        session=session,
    )

    transaccion.refresh_from_db()

    assert session.last_post_url == "https://api.mercadopago.com/checkout/preferences"
    assert session.last_headers["Authorization"] == "Bearer mp-access-token"
    assert session.last_post_json["external_reference"] == str(transaccion.id)
    assert session.last_post_json["back_urls"]["success"] == "https://egarage.cl/mp/return/"
    assert init_point.endswith("pref_id=PREF-123")
    assert transaccion.external_transaction_id == "PREF-123"
    assert transaccion.checkout_url == init_point
    assert transaccion.gateway_payload["mp_preference_response"]["id"] == "PREF-123"


@pytest.mark.django_db
def test_start_mp_payment_creates_transaction_and_redirects(client, monkeypatch):
    user, _empresa_obj = _empresa(username="mp-start", email="mp-start@example.com")
    client.force_login(user)

    monkeypatch.setattr(
        "taller.views_extra.payment_views.create_mp_preference",
        lambda transaccion, **kwargs: "https://www.mercadopago.cl/checkout/v1/redirect?pref_id=PREF-REDIRECT",
    )

    response = client.post("/cl/es/suscripcion/pago/mp/", {"plan": "mensual"})

    assert response.status_code == 302
    assert response["Location"] == "https://www.mercadopago.cl/checkout/v1/redirect?pref_id=PREF-REDIRECT"

    transaccion = SuscripcionTransaccion.objects.get(source_type="mercadopago")
    assert transaccion.payment_method == "mercadopago"
    assert transaccion.billing_cycle == "mensual"
    assert transaccion.plan_code == "basic"
    assert transaccion.reference == str(transaccion.id)


@pytest.mark.django_db
def test_mp_webhook_approves_transaction_idempotently(client, monkeypatch):
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

    _user, empresa = _empresa(username="mp-webhook", email="mp-webhook@example.com")
    transaccion = create_gateway_transaction(
        empresa=empresa,
        source_type="mercadopago",
        payment_method="mercadopago",
        amount=Decimal("55000.00"),
        currency="CLP",
        billing_cycle="semestral",
        plan_code="premium",
        reference=str(9999),
        external_transaction_id="PREF-XYZ",
        customer_email=empresa.email,
        description="Suscripcion eGarage - Semestral",
        gateway_payload={"gateway": "mercadopago"},
    )

    monkeypatch.setattr(
        "taller.views_extra.payment_views.get_mp_payment",
        lambda payment_id: {
            "id": int(payment_id),
            "status": "approved",
            "external_reference": str(transaccion.id),
            "preference_id": "PREF-XYZ",
        },
    )

    response = client.post("/webhooks/mercadopago/?data.id=123&type=payment")
    assert response.status_code == 200

    empresa.refresh_from_db()
    transaccion.refresh_from_db()
    first_fecha_fin = empresa.fecha_fin

    assert transaccion.status == "approved"
    assert transaccion.processed_by == "mp_webhook"
    assert transaccion.subscription_applied_at is not None
    assert empresa.suscripcion_activa is True
    assert empresa.plan == "premium"
    assert empresa.valor_mensual == Decimal("55000.00")

    second_response = client.post("/webhooks/mercadopago/?data.id=123&type=payment")
    assert second_response.status_code == 200

    empresa.refresh_from_db()
    transaccion.refresh_from_db()

    assert empresa.fecha_fin == first_fecha_fin
    assert transaccion.status == "approved"
