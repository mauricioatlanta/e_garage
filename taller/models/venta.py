from django.db import models
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.documento import Documento

class Venta(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)  # Multiempresa obligatorio
    fecha = models.DateField(auto_now_add=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    documento_relacionado = models.ForeignKey(Documento, on_delete=models.SET_NULL, null=True, blank=True)
    # Puedes agregar más campos según tu lógica de negocio

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente} - {self.total}"
