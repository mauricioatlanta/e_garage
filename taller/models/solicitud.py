from django.db import models
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente

class Solicitud(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)  # Multiempresa obligatorio
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=100)
    detalle = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=50, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # Puedes agregar más campos según tu lógica de negocio

    def __str__(self):
        return f"Solicitud #{self.id} - {self.tipo} - {self.estado}"
