import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.services.suscripcion_transaccion_service import (
    approve_transaction,
    create_gateway_transaction,
)


User = get_user_model()


@pytest.fixture(autouse=True)
def _service_settings(settings, monkeypatch):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "support@egarage.cl"
    settings.SUPPORT_EMAIL = "support@egarage.cl"
    media_root = Path("C:/Users/Mauricio/.codex/memories/tmp_test_media_tx_service")
    shutil.rmtree(media_root, ignore_errors=True)
    media_root.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_root)

    monkeypatch.setattr(
        "taller.utils.notificaciones_suscripcion.enviar_whatsapp",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "taller.whatsapp.admin_notifications.notify_admin_new_subscription",
        lambda *args, **kwargs: True,
    )

    yield

    shutil.rmtree(media_root, ignore_errors=True)


def _empresa(username="tx-service", email="tx-service@example.com", pais="CL"):
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
def test_approve_transaction_sends_unified_confirmation_email():
    _user, empresa = _empresa()
    transaccion = create_gateway_transaction(
        empresa=empresa,
        source_type="flow",
        payment_method="flow",
        amount=Decimal("10000.00"),
        currency="CLP",
        billing_cycle="mensual",
        plan_code="basic",
        reference="SUB-EMAIL-001",
        external_transaction_id="FLOW-EMAIL-001",
        customer_email=empresa.email,
        description="Suscripcion eGarage - Mensual",
        gateway_payload={"gateway": "flow"},
    )

    approve_transaction(transaccion, processed_by="test_admin")

    empresa.refresh_from_db()

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    html_message = email.alternatives[0][0]

    assert "eGarage" in email.subject
    assert "Pago confirmado" in html_message
    assert empresa.nombre_taller in html_message
    assert "$10,000 CLP" in html_message
    assert "Flow" in html_message
    assert "Vigencia" in html_message
    assert str(empresa.fecha_expiracion.year) in html_message
