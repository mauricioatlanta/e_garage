from django.db import models
from django.utils import timezone


class PublicAnalyticsSession(models.Model):
    ATTRIBUTION_UTM = "utm"
    ATTRIBUTION_PAID_CLICK_ID = "paid_click_id"
    ATTRIBUTION_REFERRER = "referrer"
    ATTRIBUTION_DIRECT = "direct"
    ATTRIBUTION_UNKNOWN = "unknown"

    ATTRIBUTION_TYPE_CHOICES = [
        (ATTRIBUTION_UTM, "UTM"),
        (ATTRIBUTION_PAID_CLICK_ID, "Paid click ID"),
        (ATTRIBUTION_REFERRER, "Referrer"),
        (ATTRIBUTION_DIRECT, "Direct"),
        (ATTRIBUTION_UNKNOWN, "Unknown"),
    ]

    anonymous_visitor_hash = models.CharField(max_length=64, db_index=True)
    anonymous_session_hash = models.CharField(max_length=64, unique=True, db_index=True)
    first_path = models.CharField(max_length=255)
    last_path = models.CharField(max_length=255, blank=True)
    landing_path = models.CharField(max_length=255, blank=True, db_index=True)
    country = models.CharField(max_length=8, blank=True, db_index=True)
    language = models.CharField(max_length=8, blank=True, db_index=True)
    vertical_key = models.CharField(max_length=40, blank=True, db_index=True)
    page_type = models.CharField(max_length=20, blank=True, db_index=True)
    initial_referrer = models.CharField(max_length=500, blank=True)
    last_referrer = models.CharField(max_length=500, blank=True)
    utm_source = models.CharField(max_length=100, blank=True, db_index=True)
    utm_medium = models.CharField(max_length=100, blank=True, db_index=True)
    utm_campaign = models.CharField(max_length=150, blank=True, db_index=True)
    utm_term = models.CharField(max_length=150, blank=True)
    utm_content = models.CharField(max_length=150, blank=True)
    gclid = models.CharField(max_length=150, blank=True)
    fbclid = models.CharField(max_length=150, blank=True)
    msclkid = models.CharField(max_length=150, blank=True)
    attribution_type = models.CharField(
        max_length=20,
        choices=ATTRIBUTION_TYPE_CHOICES,
        default=ATTRIBUTION_UNKNOWN,
        db_index=True,
    )
    user_agent = models.CharField(max_length=500, blank=True)
    is_mobile = models.BooleanField(default=False, db_index=True)
    is_bot = models.BooleanField(default=False, db_index=True)
    is_internal = models.BooleanField(default=False, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True, db_index=True)
    first_seen_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-first_seen_at"]
        indexes = [
            models.Index(fields=["is_bot", "is_internal", "first_seen_at"]),
            models.Index(fields=["vertical_key", "country", "first_seen_at"]),
            models.Index(fields=["utm_source", "utm_campaign", "first_seen_at"]),
            models.Index(fields=["anonymous_visitor_hash", "first_seen_at"]),
            models.Index(fields=["landing_path", "first_seen_at"]),
            models.Index(fields=["expires_at"]),
        ]
        verbose_name = "Sesión pública de analytics"
        verbose_name_plural = "Sesiones públicas de analytics"

    def __str__(self):
        return f"{self.landing_path or self.first_path} | {self.first_seen_at:%Y-%m-%d %H:%M}"
