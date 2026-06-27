"""
InterchangePieza: conocimiento de compatibilidad entre piezas de distintos vehículos,
registrado manualmente por vendedores de la empresa. Es privado por empresa (multi-tenant).
"""
from django.db import models

from core.models import TenantScoped


class InterchangePieza(TenantScoped):
    """
    Registro de que una pieza identificada por codigo_pieza en un auto origen
    es compatible (intercambiable) con el mismo tipo de pieza en un auto compatible.
    El vendedor lo registra a partir de su experiencia; veces_confirmado sube cada
    vez que otro vendedor verifica la misma combinación.
    """

    codigo_pieza = models.CharField(max_length=50, db_index=True)
    nombre_pieza = models.CharField(max_length=200, blank=True)

    # Vehículo origen (el auto del que proviene la pieza)
    marca_origen = models.CharField(max_length=100)
    modelo_origen = models.CharField(max_length=100)
    anio_origen_desde = models.PositiveIntegerField()
    anio_origen_hasta = models.PositiveIntegerField()

    # Vehículo compatible (el auto en que también sirve)
    marca_compatible = models.CharField(max_length=100)
    modelo_compatible = models.CharField(max_length=100)
    anio_compatible_desde = models.PositiveIntegerField()
    anio_compatible_hasta = models.PositiveIntegerField()

    confirmado_por_vendedor = models.BooleanField(default=True)
    veces_confirmado = models.PositiveIntegerField(default=1)
    notas = models.TextField(blank=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Interchange de pieza"
        verbose_name_plural = "Interchanges de piezas"
        indexes = [
            models.Index(fields=["empresa", "codigo_pieza"], name="interchange_emp_codigo_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "empresa",
                    "codigo_pieza",
                    "marca_origen", "modelo_origen",
                    "marca_compatible", "modelo_compatible",
                ],
                name="unique_interchange_por_empresa_combinacion",
            )
        ]

    def __str__(self):
        return (
            f"{self.codigo_pieza} | "
            f"{self.marca_origen} {self.modelo_origen} "
            f"({self.anio_origen_desde}-{self.anio_origen_hasta}) → "
            f"{self.marca_compatible} {self.modelo_compatible} "
            f"({self.anio_compatible_desde}-{self.anio_compatible_hasta})"
        )
