import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.pago import PagoPendiente


User = get_user_model()


def _create_empresa(username, email, pais):
    user = User.objects.create_user(username=username, email=email, password="pass12345")
    empresa = Empresa.objects.create(
        user=user,
        nombre_taller=f"Taller {pais}",
        email=email,
        telefono="+56911112222",
        pais=pais,
        plan="trial",
        suscripcion_activa=False,
        fecha_inicio=timezone.now() - timedelta(days=40),
        fecha_fin=timezone.now() - timedelta(days=1),
        valor_mensual=Decimal("0.00"),
    )
    return user, empresa


@pytest.fixture(autouse=True)
def _billing_settings(settings):
    settings.SECURE_SSL_REDIRECT = False
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    media_root = Path("C:/Users/Mauricio/.codex/memories/tmp_test_media_billing")
    shutil.rmtree(media_root, ignore_errors=True)
    media_root.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_root)
    yield
    shutil.rmtree(media_root, ignore_errors=True)


@pytest.mark.django_db
def test_payment_chile_uses_configured_transfer_details(client, settings):
    settings.SUBSCRIPTION_CL_BANK_NAME = "Banco de Chile"
    settings.SUBSCRIPTION_CL_ACCOUNT_TYPE = "Cuenta Corriente"
    settings.SUBSCRIPTION_CL_ACCOUNT_HOLDER = "eGarage SpA"
    settings.SUBSCRIPTION_CL_TAX_ID = "76.123.456-7"
    settings.SUBSCRIPTION_CL_ACCOUNT_NUMBER = "1234567890"
    settings.SUBSCRIPTION_CL_CONFIRMATION_EMAIL = "pagos@egarage.cl"

    user, _empresa = _create_empresa("billing-cl", "billing-cl@example.com", "CL")
    client.force_login(user)

    response = client.get("/cl/es/suscripcion/pago/?plan=mensual")

    assert response.status_code == 200
    assert response.context["datos_banco"] == {
        "banco": "Banco de Chile",
        "tipo_cuenta": "Cuenta Corriente",
        "titular": "eGarage SpA",
        "rut": "76.123.456-7",
        "numero_cuenta": "1234567890",
        "email_confirmacion": "pagos@egarage.cl",
        "tax_id_label": "RUT",
        "account_number_label": "Numero de cuenta",
    }
    assert "Atlanta Reciclajes" not in response.content.decode()


@pytest.mark.django_db
def test_payment_usa_uses_registered_paypal_webhook(client, settings):
    settings.PAYPAL_BUSINESS_EMAIL = "billing@egarage.cl"

    user, _empresa = _create_empresa("billing-us", "billing-us@example.com", "US")
    client.force_login(user)

    response = client.get("/us/en/subscription/payment/?plan=mensual")

    assert response.status_code == 200
    paypal_config = response.context["paypal_config"]
    assert paypal_config["business_email"] == "billing@egarage.cl"
    assert paypal_config["notify_url"].endswith("/webhooks/paypal/")


@pytest.mark.django_db
def test_pago_pendiente_aprobar_pago_activa_suscripcion(monkeypatch):
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

    _user, empresa = _create_empresa("billing-approve", "billing-approve@example.com", "CL")
    admin = User.objects.create_user(username="billing-admin", password="pass12345")
    old_fecha_fin = empresa.fecha_fin

    pago = PagoPendiente.objects.create(
        empresa=empresa,
        plan="mensual",
        monto=Decimal("10000.00"),
        comprobante=SimpleUploadedFile(
            "voucher.pdf",
            b"%PDF-1.4 test voucher",
            content_type="application/pdf",
        ),
        estado="pendiente",
    )

    pago.aprobar_pago(admin)
    pago.refresh_from_db()
    empresa.refresh_from_db()

    assert pago.estado == "procesado"
    assert pago.verificado_por == admin
    assert empresa.suscripcion_activa is True
    assert empresa.plan == "basic"
    assert empresa.valor_mensual == Decimal("10000.00")
    assert empresa.fecha_fin > old_fecha_fin
