"""
Costo adicional de vehículo de desarme.

Permite registrar costos flexibles (peaje, flete extra, mano de obra, etc.)
sin agregar columnas al modelo Vehiculo.
"""

from decimal import Decimal

from django.db import models

from core.models import TenantScoped


class CostoVehiculoDesarme(TenantScoped):
    """Costo adicional asociado a un vehículo de desarme."""

    TIPO_COSTO_CHOICES = [
        ("transporte", "Transporte"),
        ("grua", "Grúa"),
        ("papeles", "Papeles"),
        ("mano_obra", "Mano de obra"),
        ("reparacion", "Reparación"),
        ("otro", "Otro"),
    ]

    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="costos_desarme",
    )
    tipo_costo = models.CharField(
        max_length=30,
        choices=TIPO_COSTO_CHOICES,
        default="otro",
    )
    descripcion = models.CharField(max_length=255, blank=True, default="")
    fecha = models.DateField()
    monto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
    )

    class Meta(TenantScoped.Meta):
        verbose_name = "Costo de vehículo desarme"
        verbose_name_plural = "Costos de vehículos desarme"
        ordering = ["-fecha", "-id"]
        indexes = [
            models.Index(fields=["empresa", "vehiculo"]),
            models.Index(fields=["fecha"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_costo_display()} - {self.monto} ({self.fecha})"

    def save(self, *args, **kwargs):
        if not self.empresa_id and self.vehiculo_id:
            self.empresa = self.vehiculo.empresa
        super().save(*args, **kwargs)
