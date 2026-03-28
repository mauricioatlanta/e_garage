"""
Email backend para Resend.

Implementa django.core.mail.backends.base.BaseEmailBackend para que Django/allauth
envien correos via API HTTPS sin depender de SMTP local.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib import error, request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)
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

    def send_messages(self, email_messages: list[Any] | None) -> int:
        if not email_messages:
            return 0

        api_key = getattr(settings, "RESEND_API_KEY", "") or ""
        if not api_key:
            logger.error("RESEND_API_KEY no configurada; no se enviaran correos.")
            return 0

        sent_count = 0
        for message in email_messages:
            if self._send_one(message, api_key):
                sent_count += 1
        return sent_count

    def _send_one(self, message: Any, api_key: str) -> bool:
        recipients = list(getattr(message, "to", None) or [])
        recipients.extend(getattr(message, "cc", None) or [])
        recipients.extend(getattr(message, "bcc", None) or [])

        if not recipients:
            return False

        try:
            from_email = _validate_emailish_field(
                "from", message.from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "")
            )
            recipients = [_validate_emailish_field("to", recipient) for recipient in recipients]
        except ValueError:
            logger.exception("Payload de email invalido antes de enviar a Resend.")
            return False

        payload: dict[str, Any] = {
            "from": from_email,
            "to": recipients,
            "subject": message.subject or "",
            "text": message.body or "",
        }

        for content, mimetype in getattr(message, "alternatives", []) or []:
            if mimetype == "text/html":
                payload["html"] = content
                break

        reply_to = getattr(message, "reply_to", None) or []
        if reply_to:
            try:
                payload["reply_to"] = [
                    _validate_emailish_field("reply_to", value) for value in reply_to
                ]
            except ValueError:
                logger.exception("reply_to invalido; se omite envio por seguridad.")
                return False

        raw = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.api_url,
            data=raw,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=getattr(settings, "EMAIL_TIMEOUT", 30)) as resp:
                if 200 <= resp.status < 300:
                    return True
                logger.error("Resend devolvio status no exitoso: %s", resp.status)
                return False
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            logger.exception("HTTPError enviando correo por Resend: %s - %s", exc.code, detail)
            return False
        except Exception:
            logger.exception("Error inesperado enviando correo por Resend.")
            return False
