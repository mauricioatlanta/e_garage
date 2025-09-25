import logging
import os

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger(__name__)


class EgarageEmailBackend(EmailBackend):
    """
    Backend SMTP para eGarage. Usa SMTP sobre SSL (465) por defecto.
    Configura credenciales vía variables de entorno o settings.
    """

    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        use_tls=None,
        fail_silently=False,
        use_ssl=None,
        timeout=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        **kwargs,
    ):
        # Lee de settings o entorno, sin hardcodear credenciales
        smtp_host = host or getattr(settings, "EMAIL_HOST", "srv24.cpanelhost.cl")
        smtp_port = port or getattr(settings, "EMAIL_PORT", 465)
        smtp_user = (
            username
            or os.environ.get("EMAIL_HOST_USER")
            or getattr(settings, "EMAIL_HOST_USER", None)
        )
        smtp_pass = (
            password
            or os.environ.get("EMAIL_HOST_PASSWORD")
            or getattr(settings, "EMAIL_HOST_PASSWORD", None)
        )

        # Seguridad por defecto para 465
        smtp_use_ssl = True if use_ssl is None else use_ssl
        smtp_use_tls = False if use_tls is None else use_tls

        if not smtp_user:
            logger.warning("EMAIL_HOST_USER no configurado.")
        if not smtp_pass:
            logger.error(
                "EMAIL_HOST_PASSWORD no configurado. No se podrá enviar correo."
            )

        super().__init__(
            host=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            use_tls=smtp_use_tls,
            fail_silently=fail_silently,
            use_ssl=smtp_use_ssl,
            timeout=timeout,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            **kwargs,
        )

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        # Log mínimo (sin cuerpos para evitar PII)
        try:
            for m in email_messages:
                logger.info(
                    "Enviando email real | to=%s | subject=%s",
                    ",".join(m.to),
                    m.subject,
                )

            sent = super().send_messages(email_messages)
            logger.info("✅ %s email(s) enviado(s) correctamente.", sent)
            return sent
        except Exception:
            logger.exception("❌ Error al enviar emails via SMTP.")
            if not self.fail_silently:
                raise
            return 0
