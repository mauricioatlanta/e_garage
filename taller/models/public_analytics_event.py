from django.db import models
from django.utils import timezone


class PublicAnalyticsEvent(models.Model):
    # Production event names stay valid while the canonical event vocabulary is introduced.
    EVENT_LANDING_VIEW = "landing_view"
    EVENT_CTA_CLICK = "cta_click"
    EVENT_SIGNUP_START = "signup_start"
    EVENT_SIGNUP_COMPLETE = "signup_complete"
    EVENT_ONBOARDING_COMPLETE = "onboarding_complete"
    EVENT_SUBSCRIPTION_PAID = "subscription_paid"

    EVENT_HUMAN_VISIT = "human_visit"
    EVENT_SCROLL_50 = "scroll_50"
    EVENT_SCROLL_90 = "scroll_90"
    EVENT_CTA_WHATSAPP_CLICK = "cta_whatsapp_click"
    EVENT_CTA_TRIAL_30_CLICK = "cta_trial_30_click"
    EVENT_SIGNUP_STARTED = "signup_started"
    EVENT_SIGNUP_COMPLETED = "signup_completed"
    EVENT_COMPANY_CREATED = "company_created"
    EVENT_FIRST_LOGIN = "first_login"

    EVENT_TYPE_CHOICES = [
        (EVENT_LANDING_VIEW, "Landing vista"),
        (EVENT_CTA_CLICK, "CTA presionado"),
        (EVENT_SIGNUP_START, "Registro iniciado"),
        (EVENT_SIGNUP_COMPLETE, "Registro completado"),
        (EVENT_ONBOARDING_COMPLETE, "Onboarding completado"),
        (EVENT_SUBSCRIPTION_PAID, "Suscripción pagada"),
    ]

    session = models.ForeignKey(
        "taller.PublicAnalyticsSession",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="events",
    )
    page_view = models.ForeignKey(
        "taller.PublicPageView",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    event_type = models.CharField(max_length=40, choices=EVENT_TYPE_CHOICES, db_index=True)
    path = models.CharField(max_length=255, blank=True, db_index=True)
    dedupe_key = models.CharField(max_length=120, db_index=True, null=True, blank=True)

    # Legacy acquisition fields remain readable during 0180-0182 transition.
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

    occurred_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="public_analytics_events",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"], name="taller_publ_event_t_5b7fb7_idx"),
            models.Index(fields=["session_key", "created_at"], name="taller_publ_session_b4b74f_idx"),
            models.Index(fields=["utm_campaign", "created_at"], name="taller_publ_utm_cam_9430d0_idx"),
            models.Index(fields=["source_label", "created_at"], name="taller_publ_source__22ca5a_idx"),
            models.Index(fields=["is_internal", "created_at"], name="taller_publ_is_inte_4f0ef3_idx"),
            models.Index(fields=["event_type", "occurred_at"], name="taller_publ_event_occur_idx"),
            models.Index(fields=["path", "occurred_at"], name="taller_publ_path_occur_idx"),
            models.Index(fields=["session", "event_type"], name="taller_publ_session_event_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "event_type", "dedupe_key"],
                condition=models.Q(session__isnull=False) & models.Q(dedupe_key__isnull=False),
                name="uniq_public_session_event_dedupe",
            ),
        ]
        verbose_name = "Evento de adquisición pública"
        verbose_name_plural = "Eventos de adquisición pública"

    def __str__(self):
        timestamp = self.occurred_at or self.created_at
        return f"{self.event_type} | {self.path or '-'} | {timestamp:%Y-%m-%d %H:%M}"
