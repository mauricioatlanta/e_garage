from django.db import models
from taller.models.empresa import Empresa

class Compra(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)  # Multiempresa obligatorio
    proveedor = models.CharField(max_length=255)
    fecha = models.DateField(auto_now_add=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    detalle = models.TextField(blank=True, null=True)
    # Puedes agregar más campos según tu lógica de negocio

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor} - {self.monto_total}"
