import base64
import logging
from email.message import EmailMessage
from pathlib import Path

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailAPIEmailBackend(BaseEmailBackend):
    """
    Backend Django para enviar correos vía Gmail API (HTTPS), evitando SMTP.
    Requiere:
      - GMAIL_CREDENTIALS_FILE
      - GMAIL_TOKEN_FILE
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.credentials_file = getattr(settings, "GMAIL_CREDENTIALS_FILE", None)
        self.token_file = getattr(settings, "GMAIL_TOKEN_FILE", None)
        self.user_id = getattr(settings, "GMAIL_USER_ID", "me")

    def _load_credentials(self) -> Credentials:
        if not self.credentials_file:
            raise RuntimeError("Falta GMAIL_CREDENTIALS_FILE en settings.")
        if not self.token_file:
            raise RuntimeError("Falta GMAIL_TOKEN_FILE en settings.")

        credentials_path = Path(self.credentials_file)
        token_path = Path(self.token_file)

        if not credentials_path.exists():
            raise RuntimeError(f"No existe credentials file: {credentials_path}")
        if not token_path.exists():
            raise RuntimeError(f"No existe token file: {token_path}")

        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json(), encoding="utf-8")
            else:
                raise RuntimeError(
                    "El token Gmail no es válido y no se puede refrescar. "
                    "Regenera el token OAuth."
                )

        return creds

    def _build_message(self, email_message):
        msg = EmailMessage()
        msg["To"] = ", ".join(email_message.to or [])
        if email_message.cc:
            msg["Cc"] = ", ".join(email_message.cc)
        if email_message.bcc:
            msg["Bcc"] = ", ".join(email_message.bcc)
        msg["From"] = email_message.from_email or settings.DEFAULT_FROM_EMAIL
        msg["Subject"] = email_message.subject or ""

        reply_to = getattr(email_message, "reply_to", None)
        if reply_to:
            msg["Reply-To"] = ", ".join(reply_to)

        if email_message.content_subtype == "html":
            msg.set_content("Este correo contiene una versión HTML.")
            msg.add_alternative(email_message.body or "", subtype="html")
        else:
            msg.set_content(email_message.body or "")

        for attachment in email_message.attachments:
            if isinstance(attachment, tuple):
                filename, content, mimetype = attachment
                if mimetype:
                    maintype, subtype = mimetype.split("/", 1)
                else:
                    maintype, subtype = "application", "octet-stream"
                if isinstance(content, str):
                    content = content.encode("utf-8")
                msg.add_attachment(
                    content,
                    maintype=maintype,
                    subtype=subtype,
                    filename=filename,
                )

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        return {"raw": raw}

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        try:
            creds = self._load_credentials()
            service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        except Exception:
            if self.fail_silently:
                return 0
            raise

        sent_count = 0

        for email_message in email_messages:
            try:
                payload = self._build_message(email_message)
                service.users().messages().send(
                    userId=self.user_id,
                    body=payload,
                ).execute()
                sent_count += 1
            except Exception:
                logger.exception("Error enviando correo con Gmail API.")
                if not self.fail_silently:
                    raise

        return sent_count
