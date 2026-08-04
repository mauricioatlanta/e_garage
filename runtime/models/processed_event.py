from django.db import models


class ProcessedEvent(models.Model):
    """
    Log de idempotencia: registra qué evento originó qué resultado ERP.

    Antes de procesar un OutboxEvent, el consumer comprueba si ya existe
    un ProcessedEvent con el mismo event_id. Si existe, lo descarta sin
    crear duplicados.

    Correlación: event_id ↔ resultado ERP (tipo + id del objeto creado).
    """

    event_id = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="Mismo UUID que OutboxEvent.event_id.",
    )
    consumer = models.CharField(
        max_length=100,
        help_text="Identificador del consumer que procesó el evento.",
    )
    result_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text='Tipo del objeto ERP creado. Ej: "documento".',
    )
    result_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="PK del objeto ERP creado.",
    )
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Processed Event"
        verbose_name_plural = "Processed Events"

    def __str__(self):
        return f"{self.event_id} → {self.result_type}#{self.result_id}"
