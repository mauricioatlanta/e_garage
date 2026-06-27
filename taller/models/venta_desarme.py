from decimal import Decimal

from django.db import models


ESTADO_EMITIDA = "EMITIDA"
ESTADO_ANULADA = "ANULADA"

ESTADO_VENTA_CHOICES = [
    (ESTADO_EMITIDA, "Emitida"),
    (ESTADO_ANULADA, "Anulada"),
]


class VentaDesarme(models.Model):
    empresa = models.ForeignKey(
        "taller.Empresa", on_delete=models.CASCADE, related_name="ventas_desarme"
    )
    numero = models.PositiveIntegerField(null=True, editable=False)
    fecha = models.DateTimeField(auto_now_add=True)
    cliente_nombre = models.CharField(max_length=200, blank=True, default="")
    vendedor = models.ForeignKey(
        "taller.VendedorDesarme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ventas",
    )
    estado = models.CharField(
        max_length=10, choices=ESTADO_VENTA_CHOICES, default=ESTADO_EMITIDA
    )
    notas = models.TextField(blank=True, default="")
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    class Meta:
        app_label = "taller"
        ordering = ["-fecha"]

    def __str__(self):
        num = f"#{self.numero}" if self.numero else f"ID {self.pk}"
        cliente = self.cliente_nombre or "Sin nombre"
        return f"Venta {num} — {cliente}"

    def save(self, *args, **kwargs):
        if not self.numero and self.empresa_id:
            ultimo = (
                VentaDesarme.objects.filter(empresa=self.empresa)
                .exclude(pk=self.pk)
                .aggregate(models.Max("numero"))["numero__max"]
            ) or 0
            self.numero = ultimo + 1
        super().save(*args, **kwargs)


class LineaVentaDesarme(models.Model):
    venta = models.ForeignKey(
        VentaDesarme, on_delete=models.CASCADE, related_name="lineas"
    )
    pieza = models.ForeignKey(
        "taller.PiezaDesarme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lineas_venta_desarme",
    )
    nombre_pieza = models.CharField(max_length=255)
    codigo_pieza = models.CharField(max_length=100, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        app_label = "taller"

    def save(self, *args, **kwargs):
        self.subtotal = Decimal(str(self.precio_unitario)) * self.cantidad
        super().save(*args, **kwargs)
