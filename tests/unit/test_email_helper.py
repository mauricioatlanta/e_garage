import pytest
from django.core import mail

from taller.utils.email_helper import (
    get_branded_from_email,
    get_support_reply_to,
    send_email_with_reply_to,
)


@pytest.mark.django_db
def test_get_branded_from_email_adds_egarage_display_name(settings):
    settings.DEFAULT_FROM_EMAIL = "support@egarage.cl"
    settings.SUPPORT_EMAIL = "support@egarage.cl"
    settings.SITE_NAME = "eGarage"

    assert get_branded_from_email() == "eGarage <support@egarage.cl>"


@pytest.mark.django_db
def test_get_branded_from_email_preserves_existing_display_name(settings):
    settings.DEFAULT_FROM_EMAIL = "Soporte eGarage <support@egarage.cl>"

    assert get_branded_from_email() == "Soporte eGarage <support@egarage.cl>"


@pytest.mark.django_db
def test_send_email_with_reply_to_uses_branded_from_and_reply_to(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "support@egarage.cl"
    settings.SUPPORT_EMAIL = "ayuda@egarage.cl"
    settings.SITE_NAME = "eGarage"

    sent = send_email_with_reply_to(
        subject="Prueba branding",
        message="Mensaje de prueba",
        recipient_list=["cliente@example.com"],
        html_message="<p>Mensaje de prueba</p>",
        fail_silently=False,
    )

    assert sent == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].from_email == "eGarage <support@egarage.cl>"
    assert mail.outbox[0].reply_to == ["ayuda@egarage.cl"]
    assert get_support_reply_to() == "ayuda@egarage.cl"


@pytest.mark.django_db
def test_get_support_reply_to_falls_back_to_default_from_when_support_is_legacy(settings):
    settings.DEFAULT_FROM_EMAIL = "support@egarage.cl"
    settings.SUPPORT_EMAIL = "contacto@atlantareciclajes.cl"

    assert get_support_reply_to() == "support@egarage.cl"
