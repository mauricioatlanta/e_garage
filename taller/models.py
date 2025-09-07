from django.db import models

from taller.utils.query_scopes import ScopeManager


class MarcaManager(ScopeManager):
    def get_queryset(self):
        return super().get_queryset().select_related("empresa")


class Marca(models.Model):
    PAISES = (
        ("CL", "Chile"),
        ("US", "Estados Unidos"),
        ("AR", "Argentina"),
        ("BR", "Brasil"),
        ("PE", "Perú"),
    )

    objects = MarcaManager()
    empresa = models.ForeignKey(
        "Empresa", on_delete=models.CASCADE, related_name="marcas"
    )
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
    empresa = models.ForeignKey(
        "Empresa", on_delete=models.CASCADE, related_name="modelos"
    )

    class Meta:
        unique_together = ("nombre", "marca", "empresa")

    def __str__(self):
        return f"{self.nombre} ({self.marca.nombre})"


# Importar Cliente para que Django lo registre
from .models.clientes import Cliente
