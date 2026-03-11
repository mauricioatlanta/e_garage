"""
taller/backends/egarage_email.py

Backend SMTP "a prueba de fallos":
- Si SMTP está mal configurado o falla, NO tumba la request (evita 500).
"""

import logging
import smtplib

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend

logger = logging.getLogger(__name__)


class EgarageEmailBackend(DjangoSMTPBackend):
    def __init__(self, *args, **kwargs):
        # Fuerza timeout SIEMPRE (evita bloqueos largos y worker timeouts)
        kwargs.setdefault("timeout", getattr(settings, "EMAIL_TIMEOUT", 10))
        super().__init__(*args, **kwargs)

    def send_messages(self, email_messages):
        try:
            return super().send_messages(email_messages)

        # Errores SMTP / red típicos
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException, OSError) as e:
            logger.warning(
                "SMTP falló (no se envió correo). Revisar EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD: %s",
                e,
                exc_info=True,
            )
            return 0

        # SystemExit no hereda de Exception (viene de gunicorn handle_abort)
        except BaseException as e:
            logger.exception("Email BaseException atrapada (return 0, no 500): %s", e)
            return 0
