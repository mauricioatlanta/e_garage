import logging

import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = (getattr(settings, "RESEND_API_KEY", "") or "").strip()
        if not api_key:
            logger.error(
                "ResendBackend: RESEND_API_KEY no configurada — emails no enviados."
            )
            if not self.fail_silently:
                raise ValueError("RESEND_API_KEY no está configurada en settings")
            return 0

        resend.api_key = api_key
        sent_count = 0

        for message in email_messages:
            try:
                html_content = ""
                if hasattr(message, "alternatives") and message.alternatives:
                    for alt in message.alternatives:
                        if alt[1] == "text/html":
                            html_content = alt[0]
                            break

                if not html_content:
                    html_content = f"<p>{message.body}</p>".replace("\n", "<br>")

                params = {
                    "from": getattr(settings, "DEFAULT_FROM_EMAIL", "support@egarage.cl"),
                    "to": message.to,
                    "subject": message.subject,
                    "html": html_content,
                }
                resend.Emails.send(params)
                sent_count += 1
            except Exception as e:
                logger.error(
                    "ResendBackend: error enviando a %s — %s",
                    message.to,
                    e,
                    exc_info=True,
                )
                if not self.fail_silently:
                    raise

        return sent_count
