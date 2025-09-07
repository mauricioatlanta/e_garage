from decimal import Decimal

from django.db import models

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import (LineaOtroServicio, LineaRepuesto,
                                            LineaServicio)
from taller.models.vehiculos import Vehiculo

Documento = Documento


class DetalleDocumento(models.Model):
    documento = models.ForeignKey(
        Documento, on_delete=models.CASCADE, related_name="detalles"
    )
    tipo_item = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    precio_venta = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, default=Decimal("0.00")
    )

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_venta * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_item}: {self.nombre}"
