import smtplib
import logging
logger = logging.getLogger(__name__)

class EgarageEmailBackend(...):
    ...

    def send_messages(self, email_messages):
        try:
            return super().send_messages(email_messages)
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPException) as e:
            logger.exception("SMTP error (no tumbar request): %s", e)
            return 0
        except Exception as e:
            logger.exception("Email error inesperado (no tumbar request): %s", e)
            return 0
