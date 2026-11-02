from django.db import models
from django.utils import timezone


class SnapshotQueueItem(models.Model):
    """Item simple de cola para generación de snapshots.

    Almacena referencia a `Documento` cuyo cambio requiere regenerar snapshots
    de vehículos relacionados.
    """

    documento = models.ForeignKey(
        "taller.Documento", on_delete=models.CASCADE, related_name="snapshot_queue_items"
    )
    empresa = models.ForeignKey("taller.Empresa", on_delete=models.CASCADE, related_name="snapshot_queue")
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(default=timezone.now, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    locked_at = models.DateTimeField(null=True, blank=True, db_index=True)
    worker_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    attempts = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Snapshot Queue Item"
        verbose_name_plural = "Snapshot Queue Items"
        indexes = [models.Index(fields=["documento", "scheduled_at"])]

    def mark_processed(self):
        self.processed_at = timezone.now()
        self.locked_at = None
        self.worker_id = None
        self.save(update_fields=["processed_at", "locked_at", "worker_id"])
