from django.db import models


class PublicAnalyticsBackfillCheckpoint(models.Model):
    STATUS_READY = "READY"
    STATUS_RUNNING = "RUNNING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_READY, "Ready"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    key = models.CharField(max_length=80, unique=True)
    cutoff_event_pk = models.BigIntegerField(null=True, blank=True)
    cutoff_pageview_pk = models.BigIntegerField(null=True, blank=True)
    captured_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    owner_token = models.CharField(max_length=64, null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Public analytics backfill checkpoint"
        verbose_name_plural = "Public analytics backfill checkpoints"
