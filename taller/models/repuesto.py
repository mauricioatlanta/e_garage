from django.db import models
from .tienda import Tienda  # si es necesario

class Repuesto(models.Model):
    # Este campo conecta cada registro con la empresa dueña del dato
    empresa = models.ForeignKey('taller.Empresa', on_delete=models.CASCADE)  # Multiempresa obligatorio
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    nombre_repuesto = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100)
    precio_venta = models.IntegerField()
    precio_compra = models.IntegerField()
    stock = models.IntegerField()
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('tienda', 'part_number')
        ordering = ['nombre_repuesto']

    def __str__(self):
        return f"{self.nombre_repuesto} ({self.part_number})"
# Aquí va el modelo Repuesto
