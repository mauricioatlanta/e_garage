from django.db import models
from .clientes import Cliente


class Suscripcion(models.Model):
    PLANES = [
        ("Básico", "Básico"),
        ("Premium", "Premium"),
    ]
    ESTADOS = [
        ("Activa", "Activa"),
        ("Vencida", "Vencida"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    plan = models.CharField(max_length=50, choices=PLANES)
    fecha_inicio = models.DateField("Fecha de inicio")
    fecha_vencimiento = models.DateField("Fecha de vencimiento")
    estado = models.CharField(max_length=20, choices=ESTADOS)

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.cliente} - {self.plan} ({self.estado})"
