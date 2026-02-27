"""
Registro de kilometraje en ingreso de vehículo (con prueba de vida: foto tablero o motivo de omisión).
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class RegistroKilometraje(models.Model):
    """
    Registro de kilometraje en el flujo de ingreso (kiosk).
    Permite foto del tablero como prueba de vida o omitir con motivo.
    """

    SOURCE_CHOICES = [
        ("ingreso", _("Ingreso")),
        ("manual", _("Manual")),
        ("documento", _("Documento")),
    ]

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="registros_km_ingreso",
        db_index=True,
    )
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="registros_km",
        db_index=True,
    )
    kilometraje = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    foto_tablero = models.ImageField(
        upload_to="ingresos/tablero/%Y/%m/",
        blank=True,
        null=True,
    )
    omitido_motivo = models.CharField(max_length=255, blank=True)
    source = models.CharField(
        max_length=20,
        default="ingreso",
        choices=SOURCE_CHOICES,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="km_creados",
    )

    class Meta:
        ordering = ["-fecha"]
        verbose_name = _("Registro kilometraje ingreso")
        verbose_name_plural = _("Registros kilometraje ingreso")
        indexes = [
            models.Index(fields=["empresa", "vehiculo", "-fecha"]),
        ]

    def __str__(self):
        return f"{self.vehiculo.patente} @ {self.kilometraje} km"

    def clean(self):
        super().clean()
        if self.vehiculo_id and self.empresa_id and self.vehiculo.empresa_id != self.empresa_id:
            raise ValidationError("El vehículo debe pertenecer a la empresa.")
