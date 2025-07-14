from django.db import models

class HistorialStock(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    repuesto = models.ForeignKey("Repuesto", on_delete=models.CASCADE)
    documento = models.ForeignKey("Documento", on_delete=models.SET_NULL, null=True, blank=True)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} de {self.repuesto} ({self.cantidad})"

    class Meta:
        verbose_name = "Historial de Stock"
        verbose_name_plural = "Historial de Stock"
