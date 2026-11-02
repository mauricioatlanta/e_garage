from decimal import Decimal

from django.db import models


class SmartYardGlobalMetric(models.Model):

    marca = models.ForeignKey(
        "taller.Marca",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    modelo = models.ForeignKey(
        "taller.Modelo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    country = models.CharField(
        max_length=2,
        default="CL",
        db_index=True,
    )

    anio = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
    )

    vehiculos_analizados = models.PositiveIntegerField(
        default=0
    )

    roi_promedio = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("0")
    )

    dias_recuperacion_promedio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0")
    )

    ganancia_promedio = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0")
    )

    piezas_promedio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0")
    )

    nivel_confianza = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0")
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Smart Yard Global Metric"
        verbose_name_plural = "Smart Yard Global Metrics"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "marca",
                    "modelo",
                    "country",
                    "anio",
                ],
                name="unique_smart_yard_global_metric",
            )
        ]

    def __str__(self):
        return (
            f"{self.marca} {self.modelo} "
            f"{self.anio} ({self.country})"
        )
