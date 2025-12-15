"""
taller/backends/egarage_email.py

Backend SMTP "a prueba de fallos":
- Si SMTP está mal configurado o falla, NO tumba la request (evita 500).
"""

import logging
import smtplib

from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend

logger = logging.getLogger(__name__)


class EgarageEmailBackend(DjangoSMTPBackend):
    def send_messages(self, email_messages):
        try:
            return super().send_messages(email_messages)
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException, OSError) as e:
            logger.exception("SMTP error (return 0, no 500): %s", e)
            return 0
        except Exception as e:
            logger.exception("Email error inesperado (return 0, no 500): %s", e)
            return 0
