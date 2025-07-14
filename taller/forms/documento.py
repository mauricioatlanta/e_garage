from django.db import models
from .clientes import Cliente
from taller.models.vehiculos import Vehiculo  # ✅ forma correcta desde otro archivo
from taller.models.mecanico import Mecanico


class Documento(models.Model):
    TIPOS_DOCUMENTO = [
        ('Presupuesto', 'Presupuesto'),
        ('Orden de trabajo', 'Orden de trabajo'),
        ('Factura', 'Factura'),
    ]

    tipo_documento = models.CharField(max_length=50, choices=TIPOS_DOCUMENTO)
    numero_documento = models.CharField(max_length=50, unique=True, blank=True)
    fecha = models.DateField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    kilometraje = models.PositiveIntegerField()
    observaciones = models.TextField(blank=True)
    mecanico = models.ForeignKey(Mecanico, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.tipo_documento} #{self.numero_documento}"

class RepuestoDocumento(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='repuestos')
    codigo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField()
    precio = models.PositiveIntegerField()

    @property
    def total(self):
        return self.cantidad * self.precio

class ServicioDocumento(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='servicios')
    nombre = models.CharField(max_length=255)
    precio = models.PositiveIntegerField()
