from django.db import models
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo

class Inspeccion(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)  # Multiempresa obligatorio
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    detalle = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=50, default='pendiente')
    fecha_inspeccion = models.DateField()
    observaciones = models.TextField(blank=True, null=True)
    # Puedes agregar más campos según tu lógica de negocio

    def __str__(self):
        return f"Inspección #{self.id} - {self.vehiculo} - {self.estado}"
