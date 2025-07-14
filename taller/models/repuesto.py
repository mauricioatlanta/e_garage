from django.db import models
from .tienda import Tienda  # si es necesario

class Repuesto(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    nombre_repuesto = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('tienda', 'part_number')
        ordering = ['nombre_repuesto']

    def __str__(self):
        return f"{self.nombre_repuesto} ({self.part_number})"
# Aquí va el modelo Repuesto
