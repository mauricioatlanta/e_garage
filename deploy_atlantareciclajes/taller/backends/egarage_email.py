import logging
import os
import smtplib

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

        # Timeout por defecto más largo (30 segundos) para evitar timeouts
        # El timeout por defecto de smtplib es 10 segundos, que puede ser insuficiente
        smtp_timeout = timeout if timeout is not None else getattr(settings, "EMAIL_TIMEOUT", 30)

        if not smtp_user:
            logger.warning("EMAIL_HOST_USER no configurado.")
        if not smtp_pass:
            logger.error("EMAIL_HOST_PASSWORD no configurado. No se podrá enviar correo.")

        super().__init__(
            host=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            use_tls=smtp_use_tls,
            fail_silently=fail_silently,
            use_ssl=smtp_use_ssl,
            timeout=smtp_timeout,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            **kwargs,
        )

    def open(self):
        """
        Override para manejar passwords con caracteres UTF-8 (como ñ)
        que causan problemas con smtplib en Python 3.13

        El error 'ascii' codec can't encode character ocurre porque smtplib
        usa el método de autenticación PLAIN que requiere ASCII puro.
        """
        if self.connection:
            return False

        connection_params = {}
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout
        if self.use_ssl:
            connection_params["context"] = self.ssl_context

        try:
            self.connection = smtplib.SMTP_SSL(self.host, self.port, **connection_params)

            # SOLUCIÓN: Verificar si el password tiene caracteres no-ASCII
            # y advertir al usuario que debe cambiar el password del servidor
            if self.username and self.password:
                try:
                    # Intentar codificar el password como ASCII
                    self.password.encode("ascii")
                    # Si funciona, hacer login normal
                    self.connection.login(self.username, self.password)
                except UnicodeEncodeError as ue:
                    # El password contiene caracteres especiales (ñ, á, etc.)
                    logger.error(
                        "❌ ERROR CRÍTICO: La contraseña del email contiene caracteres "
                        "especiales que no son compatibles con SMTP AUTH PLAIN.\n"
                        f"   Character problemático: {ue}\n"
                        "   SOLUCIÓN: Cambiar la contraseña de la cuenta "
                        f"'{self.username}' en el panel de cPanel para usar solo:\n"
                        "   - Letras (a-z, A-Z)\n"
                        "   - Números (0-9)\n"
                        "   - Símbolos básicos (!@#$%^&*-_=+)"
                    )
                    # Cerrar conexión
                    if self.connection:
                        try:
                            self.connection.quit()
                        except:
                            pass
                    self.connection = None
                    raise RuntimeError(
                        "Email password contains non-ASCII characters (like 'ñ'). "
                        "Please change the email account password to use only ASCII characters."
                    )
            return True
        except TimeoutError as e:
            logger.error(
                f"⏱️  Timeout al conectar con servidor SMTP {self.host}:{self.port}. "
                f"Timeout configurado: {self.timeout}s. Error: {e}"
            )
            if not self.fail_silently:
                raise
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP al conectar: {e}")
            if not self.fail_silently:
                raise
            return False
        except Exception as e:
            logger.error(f"Error al conectar con el servidor SMTP: {e}")
            if not self.fail_silently:
                raise
            return False

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
        except TimeoutError as e:
            logger.error(
                f"⏱️  Timeout al enviar emails. El servidor SMTP no respondió a tiempo. "
                f"Timeout: {self.timeout}s. Error: {e}"
            )
            if not self.fail_silently:
                raise
            return 0
        except Exception as e:
            logger.exception("❌ Error al enviar emails via SMTP.")
            if not self.fail_silently:
                raise
            return 0
