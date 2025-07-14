from django.db import models
from .modelo import Modelo


class ColorVehiculo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Color"
        verbose_name_plural = "Colores"

    def __str__(self):
        return self.nombre


class MotorVehiculo(models.Model):
    nombre = models.CharField(max_length=100)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, related_name="motores")

    class Meta:
        unique_together = ('nombre', 'modelo')
        ordering = ['nombre']
        verbose_name = "Motor"
        verbose_name_plural = "Motores"

    def __str__(self):
        return self.nombre


class CajaVehiculo(models.Model):
    nombre = models.CharField(max_length=100)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, related_name="cajas")

    class Meta:
        unique_together = ('nombre', 'modelo')
        ordering = ['nombre']
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"

    def __str__(self):
        return self.nombre
