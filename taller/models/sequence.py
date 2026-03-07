from django.db import models, transaction

from taller.models.empresa import Empresa


class DocumentSequence(models.Model):
    """Modelo para manejar secuencias de documentos por empresa, tipo y serie"""

    SERIE_CHOICES = [
        ("WORKSHOP", "Workshop"),
        ("PARTS", "Parts"),
        ("MIXED", "Mixed"),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=4)  # 'OT','FAC','PRES'
    serie = models.CharField(max_length=16, default="WORKSHOP", choices=SERIE_CHOICES)
    current = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("empresa", "tipo", "serie")
        verbose_name = "Secuencia de Documento"
        verbose_name_plural = "Secuencias de Documentos"

    @classmethod
    def next(cls, empresa, tipo, serie=None):
        """Obtiene el siguiente número de secuencia de forma segura para concurrencia.
        serie: opcional, ej. 'WORKSHOP', 'PARTS', 'MIXED' (Facturas A/B, etc.)."""
        serie = str(serie or "WORKSHOP").strip().upper()
        if serie not in ("WORKSHOP", "PARTS", "MIXED"):
            serie = "WORKSHOP"
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(
                empresa=empresa, tipo=tipo, serie=serie, defaults={"current": 0}
            )
            obj.current += 1
            obj.save(update_fields=["current"])
            return obj.current

    def __str__(self):
        return f"{self.empresa.nombre} - {self.tipo}/{self.serie}: {self.current}"
