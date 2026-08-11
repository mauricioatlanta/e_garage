import hashlib

from django.db import models
from django.utils import timezone


class PublicPageView(models.Model):
    """
    Telemetría first-party para páginas públicas de eGarage.

    No depende de usuarios autenticados.
    No almacena la IP en texto plano: solo un hash diario.
    """

    PAGE_HOME = "home"
    PAGE_WELCOME = "welcome"
    PAGE_LANDING = "landing"

    PAGE_TYPE_CHOICES = [
        (PAGE_HOME, "Página principal"),
        (PAGE_WELCOME, "Bienvenida"),
        (PAGE_LANDING, "Landing"),
    ]

    path = models.CharField(max_length=255, db_index=True)
    page_type = models.CharField(
        max_length=20,
        choices=PAGE_TYPE_CHOICES,
        db_index=True,
    )

    country = models.CharField(max_length=8, blank=True, db_index=True)
    language = models.CharField(max_length=8, blank=True, db_index=True)

    visitor_hash = models.CharField(max_length=64, db_index=True)

    referrer = models.CharField(max_length=500, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    is_mobile = models.BooleanField(default=False, db_index=True)
    is_bot = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["page_type", "created_at"]),
            models.Index(fields=["country", "created_at"]),
            models.Index(fields=["path", "created_at"]),
            models.Index(fields=["visitor_hash", "created_at"]),
            models.Index(fields=["is_bot", "created_at"]),
        ]
        verbose_name = "Visita pública"
        verbose_name_plural = "Visitas públicas"

    def __str__(self):
        return f"{self.path} | {self.country or '-'} | {self.created_at:%Y-%m-%d %H:%M}"

    @staticmethod
    def build_visitor_hash(ip: str, user_agent: str, date_key: str) -> str:
        """
        Identificador aproximado diario sin conservar la IP original.
        """
        raw = f"{date_key}|{ip}|{user_agent}"
        return hashlib.sha256(
            raw.encode("utf-8", errors="replace")
        ).hexdigest()


def is_probable_bot(user_agent: str) -> bool:
    ua = (user_agent or "").lower()

    indicators = (
        "bot",
        "spider",
        "crawler",
        "slurp",
        "bingpreview",
        "facebookexternalhit",
        "headless",
        "curl/",
        "wget/",
        "python-requests",
        "python/",
        "go-http-client",
        "httpclient",
        "uptimerobot",
        "monitoring",
    )

    if not ua:
        return True

    return any(token in ua for token in indicators)
