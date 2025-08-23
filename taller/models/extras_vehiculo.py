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
    country = models.CharField(
        max_length=2, 
        default='CL',
        choices=[
            ('CL', 'Chile'),
            ('US', 'Estados Unidos'),
        ],
        verbose_name="País"
    )

    class Meta:
        unique_together = [('country', 'modelo', 'nombre')]
        ordering = ['nombre']
        verbose_name = "Motor"
        verbose_name_plural = "Motores"
        indexes = [
            models.Index(fields=['country', 'modelo', 'nombre']),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Asegurar que el country coincida con el del modelo
        if hasattr(self, 'modelo') and self.modelo:
            self.country = self.modelo.country
        super().save(*args, **kwargs)


class CajaVehiculo(models.Model):
    nombre = models.CharField(max_length=100)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, related_name="cajas")
    country = models.CharField(
        max_length=2, 
        default='CL',
        choices=[
            ('CL', 'Chile'),
            ('US', 'Estados Unidos'),
        ],
        verbose_name="País"
    )

    class Meta:
        unique_together = [('country', 'modelo', 'nombre')]
        ordering = ['nombre']
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        indexes = [
            models.Index(fields=['country', 'modelo', 'nombre']),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Asegurar que el country coincida con el del modelo
        if hasattr(self, 'modelo') and self.modelo:
            self.country = self.modelo.country
        super().save(*args, **kwargs)
