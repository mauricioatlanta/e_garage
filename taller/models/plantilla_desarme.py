"""
Plantillas de desarme: generación automática de piezas vendibles por vehículo.

- PlantillaDesarme: empresa=null → global; empresa no null → específica del suscriptor.
- PlantillaPieza: piezas de la plantilla (nombre, orden, etc.).
"""

from decimal import Decimal

from django.db import models
from django.db.models import Index


class PlantillaDesarme(models.Model):
    """
    Plantilla de piezas para vehículos de desarme.
    - empresa=null: plantilla global del sistema (Sedan, SUV, etc.).
    - empresa no null: plantilla personalizada del suscriptor.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        help_text="NULL=plantilla global; no null=plantilla del suscriptor",
    )
    nombre = models.CharField(max_length=120, db_index=True)
    descripcion = models.TextField(blank=True, default="")
    activa = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Plantilla de desarme"
        verbose_name_plural = "Plantillas de desarme"
        ordering = ["nombre"]
        indexes = [
            Index(fields=["empresa", "activa"]),
        ]

    def __str__(self):
        return self.nombre


class PlantillaPieza(models.Model):
    """Pieza incluida en una plantilla de desarme."""

    plantilla = models.ForeignKey(
        PlantillaDesarme,
        on_delete=models.CASCADE,
        related_name="piezas",
    )
    nombre_pieza = models.CharField(max_length=160, db_index=True)
    categoria = models.ForeignKey(
        "taller.CategoriaRepuesto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    orden = models.PositiveIntegerField(default=0)
    codigo_base = models.CharField(max_length=64, blank=True, default="")
    activo = models.BooleanField(default=True)
    lado = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="left, right o vacío si no aplica",
    )
    zona_mapa = models.CharField(
        max_length=60,
        blank=True,
        default="",
        help_text="Código de zona en mapa (ej. left_front_door, hood)",
    )
    vista_mapa = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="Vista del mapa: frontal, lateral_izq, lateral_der, trasera, motor",
    )

    class Meta:
        verbose_name = "Pieza de plantilla"
        verbose_name_plural = "Piezas de plantilla"
        ordering = ["plantilla", "orden", "id"]
        indexes = [
            Index(fields=["plantilla", "orden"]),
        ]

    def __str__(self):
        return f"{self.plantilla.nombre}: {self.nombre_pieza}"
