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
    session_key = models.CharField(max_length=64, blank=True, db_index=True)

    referrer = models.CharField(max_length=500, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    is_mobile = models.BooleanField(default=False, db_index=True)
    is_bot = models.BooleanField(default=False, db_index=True)
    is_internal = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_server = models.BooleanField(default=False, db_index=True)

    utm_source = models.CharField(max_length=120, blank=True, db_index=True)
    utm_medium = models.CharField(max_length=120, blank=True)
    utm_campaign = models.CharField(max_length=160, blank=True, db_index=True)
    utm_content = models.CharField(max_length=160, blank=True)
    utm_term = models.CharField(max_length=160, blank=True)
    landing_initial = models.CharField(max_length=255, blank=True)
    source_label = models.CharField(max_length=120, blank=True, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["page_type", "created_at"]),
            models.Index(fields=["country", "created_at"]),
            models.Index(fields=["path", "created_at"]),
            models.Index(fields=["visitor_hash", "created_at"]),
            models.Index(fields=["is_bot", "created_at"]),
            models.Index(fields=["is_internal", "created_at"]),
            models.Index(fields=["utm_campaign", "created_at"]),
            models.Index(fields=["source_label", "created_at"]),
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
        "infrawatch",
        "zgrab",
        "l9scan",
        "l9tcpid",
        "palo alto networks",
        "visionheight.com/scan",
        "censysinspect",
        "cyberconvoy",
        "python-urllib",
        "vuln_scanner",
        "seo-diagnostic",
        "egarage-diagnostic",
        "modatscanner",
        "netcraftsurveyagent",
        "internetmeasurement",
        "forestengine",
        "leakix",
        "fasthttp",
        "research-scanner",
        "sirius-opendir-research",
        "compatible; odin;",
    )

    if not ua:
        return True

    return any(token in ua for token in indicators)


class PublicAnalyticsEvent(models.Model):
    EVENT_LANDING_VIEW = "landing_view"
    EVENT_CTA_CLICK = "cta_click"
    EVENT_SIGNUP_START = "signup_start"
    EVENT_SIGNUP_COMPLETE = "signup_complete"
    EVENT_ONBOARDING_COMPLETE = "onboarding_complete"
    EVENT_SUBSCRIPTION_PAID = "subscription_paid"

    EVENT_TYPE_CHOICES = [
        (EVENT_LANDING_VIEW, "Landing vista"),
        (EVENT_CTA_CLICK, "CTA presionado"),
        (EVENT_SIGNUP_START, "Registro iniciado"),
        (EVENT_SIGNUP_COMPLETE, "Registro completado"),
        (EVENT_ONBOARDING_COMPLETE, "Onboarding completado"),
        (EVENT_SUBSCRIPTION_PAID, "Suscripción pagada"),
    ]

    event_type = models.CharField(max_length=40, choices=EVENT_TYPE_CHOICES, db_index=True)
    page_view = models.ForeignKey(
        PublicPageView,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
    )
    empresa = models.ForeignKey(
        "taller.Empresa",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="public_analytics_events",
    )

    path = models.CharField(max_length=255, blank=True, db_index=True)
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    visitor_hash = models.CharField(max_length=64, blank=True, db_index=True)
    country = models.CharField(max_length=8, blank=True, db_index=True)
    language = models.CharField(max_length=8, blank=True, db_index=True)
    rubro = models.CharField(max_length=40, blank=True, db_index=True)

    utm_source = models.CharField(max_length=120, blank=True, db_index=True)
    utm_medium = models.CharField(max_length=120, blank=True)
    utm_campaign = models.CharField(max_length=160, blank=True, db_index=True)
    utm_content = models.CharField(max_length=160, blank=True)
    utm_term = models.CharField(max_length=160, blank=True)
    landing_initial = models.CharField(max_length=255, blank=True)
    referrer = models.CharField(max_length=500, blank=True)
    source_label = models.CharField(max_length=120, blank=True, db_index=True)

    is_mobile = models.BooleanField(default=False, db_index=True)
    is_bot = models.BooleanField(default=False, db_index=True)
    is_internal = models.BooleanField(default=False, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_server = models.BooleanField(default=False, db_index=True)

    value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["session_key", "created_at"]),
            models.Index(fields=["utm_campaign", "created_at"]),
            models.Index(fields=["source_label", "created_at"]),
            models.Index(fields=["is_internal", "created_at"]),
        ]
        verbose_name = "Evento de adquisición pública"
        verbose_name_plural = "Eventos de adquisición pública"

    def __str__(self):
        return f"{self.event_type} | {self.path or '-'} | {self.created_at:%Y-%m-%d %H:%M}"
