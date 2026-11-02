import requests
import re
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

EMAIL_PATTERN = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")
NAME_EMAIL_PATTERN = re.compile(r"^.+<\s*([^@\s<>]+@[^@\s<>]+\.[^@\s<>]+)\s*>$")


def _looks_like_markdown_or_url(value: str) -> bool:
    lower = value.lower()
    return (
        "[" in value
        and "](" in value
        or "mailto:" in lower
        or "http://" in lower
        or "https://" in lower
    )


def _validate_emailish_field(field_name: str, value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"Campo {field_name} vacio")
    if _looks_like_markdown_or_url(cleaned):
        raise ValueError(f"Campo {field_name} invalido: parece markdown/url ({cleaned!r})")

    if EMAIL_PATTERN.match(cleaned):
        return cleaned

    match = NAME_EMAIL_PATTERN.match(cleaned)
    if match:
        return cleaned

    raise ValueError(f"Campo {field_name} invalido: {cleaned!r}")


class ResendEmailBackend(BaseEmailBackend):
    api_url = "https://api.resend.com/emails"

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "RESEND_API_KEY", "") or ""
        if not api_key:
            if self.fail_silently:
                return 0
            raise ValueError("RESEND_API_KEY no esta configurada")

        sent_count = 0

        for message in email_messages:
            from_email = message.from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None)
            to_emails = list(message.to or [])

            if not from_email:
                if self.fail_silently:
                    continue
                raise ValueError("No hay from_email configurado")

            if not to_emails:
                continue

            try:
                from_email = _validate_emailish_field("from", from_email)
                to_emails = [_validate_emailish_field("to", email) for email in to_emails]
            except ValueError:
                if self.fail_silently:
                    continue
                raise

            payload = {"from": from_email, "to": to_emails, "subject": message.subject or ""}

            if message.body:
                if message.content_subtype == "html":
                    payload["html"] = message.body
                else:
                    payload["text"] = message.body

            if getattr(message, "alternatives", None):
                for alt_body, mimetype in message.alternatives:
                    if mimetype == "text/html":
                        payload["html"] = alt_body

            if message.cc:
                payload["cc"] = list(message.cc)

            if message.bcc:
                payload["bcc"] = list(message.bcc)

            if message.reply_to:
                payload["reply_to"] = [
                    _validate_emailish_field("reply_to", email) for email in list(message.reply_to)
                ]

            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if 200 <= response.status_code < 300:
                sent_count += 1
            else:
                if self.fail_silently:
                    continue
                raise Exception(f"Resend API error {response.status_code}: {response.text}")

        return sent_count
