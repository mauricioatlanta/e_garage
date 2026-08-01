import uuid

from django.db import models


class OutboxEvent(models.Model):
    """
    Transactional Outbox para eventos del dominio Commerce → ERP.

    Cada evento se persiste en la misma transaction.atomic() que el aggregate
    que lo originó. El comando process_outbox lo lee y despacha a los
    consumidores registrados. Ver ADR-002.
    """

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

    STATUS_CHOICES = [
        (PENDING, "Pendiente"),
        (PROCESSING, "En proceso"),
        (PROCESSED, "Procesado"),
        (FAILED, "Fallido"),
    ]

    event_id = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="UUID único del evento. Garantiza idempotencia en el consumer.",
    )
    aggregate_type = models.CharField(max_length=50)   # "commerce_order"
    aggregate_id = models.CharField(max_length=50)     # str(order.pk)
    event_type = models.CharField(max_length=100, db_index=True)  # "commerce.order.submitted"
    payload = models.JSONField()
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=PENDING, db_index=True
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Outbox Event"
        verbose_name_plural = "Outbox Events"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.event_type} [{self.status}] {self.event_id}"
