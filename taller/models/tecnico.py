# taller/models/tecnico.py
from django.db import models

from .empresa import Empresa


class Tecnico(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="tecnicos",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono de contacto del técnico",
    )
    direccion = models.TextField(
        blank=True, null=True, help_text="Dirección del técnico"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        estado = "✅" if self.activo else "❌"
        return f"{estado} {self.nombre}"

    class Meta:
        unique_together = ["empresa", "nombre"]  # Evitar duplicados por empresa
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"
        ordering = ["-activo", "nombre"]
