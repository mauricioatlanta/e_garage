# Residuo movido desde taller/models.py (evitar ambigüedad con taller/models/ paquete)
from django.db import models

from taller.utils.query_scopes import ScopeManager


class MarcaManager(ScopeManager):
    def get_queryset(self):
        return super().get_queryset().select_related("empresa")


class Marca(models.Model):
    PAISES = (
        ("CL", "Chile"),
        ("US", "Estados Unidos"),
        ("MX", "México"),
        ("AR", "Argentina"),
        ("UY", "Uruguay"),
        ("BR", "Brasil"),
        ("PE", "Perú"),
    )

    objects = MarcaManager()
    empresa = models.ForeignKey("Empresa", on_delete=models.CASCADE, related_name="marcas")
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, blank=True)
    pais = models.CharField(max_length=2, choices=PAISES, default="CL")

    class Meta:
        unique_together = ("nombre", "pais", "empresa")

    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name="modelos")
    empresa = models.ForeignKey("Empresa", on_delete=models.CASCADE, related_name="modelos")

    class Meta:
        unique_together = ("nombre", "marca", "empresa")

    def __str__(self):
        return f"{self.nombre} ({self.marca.nombre})"
