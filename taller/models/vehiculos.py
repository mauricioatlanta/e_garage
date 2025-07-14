from django.db import models

from .marca import Marca
from .modelo import Modelo
from .clientes import Cliente
from .extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo


class Vehiculo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True)
    patente = models.CharField(max_length=20)
    anio = models.PositiveIntegerField(verbose_name="Año")
    color = models.ForeignKey(ColorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    vin = models.CharField(max_length=50, blank=True, null=True)
    motor = models.ForeignKey(MotorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    caja = models.ForeignKey(CajaVehiculo, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.patente} - {self.modelo}"

    class Meta:
        ordering = ['marca', 'modelo', 'patente']
        verbose_name = "Vehículo"
