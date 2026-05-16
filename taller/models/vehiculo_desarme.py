"""
Modelo VehiculoDesarme: vehículos comprados por el taller para desarme.
Entidad separada de Vehiculo (cliente/reparación).
"""

from django.core.exceptions import ValidationError
from django.db import models

from core.models import TenantScoped

from .extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo
from .marca import Marca
from .modelo import Modelo

ESTADO_DESARME_CHOICES = [
    ("INGRESADO", "Ingresado"),
    ("DESARMANDO", "Desarmando"),
    ("DESARMADO", "Desarmado"),
    ("AGOTADO", "Agotado"),
    ("RECUPERADO", "Recuperado"),
    ("CERRADO", "Cerrado"),
    ("BAJA", "Baja"),
]


class VehiculoDesarme(TenantScoped):
    """
    Vehículo comprado por el taller para desarme.
    Solo para flujo inventario/compra/despiece; no para reparación.
    """

    # Campo temporal de migración: ID del Vehiculo origen (mapeo por ID).
    vehiculo_origen_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID del Vehiculo origen (solo para migración; null en registros nuevos).",
    )

    # Identificación (espejo de Vehiculo para desarme)
    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Marca del vehículo (Chile: FK; USA: usar marca_texto).",
    )
    marca_texto = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Marca como texto (USA catálogo global).",
    )
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Modelo del vehículo (Chile: FK; USA: usar modelo_texto).",
    )
    modelo_texto = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Modelo como texto (USA catálogo global).",
    )
    patente = models.CharField(
        max_length=20,
        db_index=True,
        blank=True,
        default="",
        help_text="Patente o placa; vacío si solo VIN.",
    )
    anio = models.PositiveIntegerField(
        verbose_name="Año",
        null=True,
        blank=True,
        help_text="No inventar valores; copiar tal cual del origen.",
    )
    color = models.ForeignKey(
        ColorVehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    vin = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    motor = models.ForeignKey(
        MotorVehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    caja = models.ForeignKey(
        CajaVehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    millas = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Millas/Kilometraje",
    )

    # Campos de desarme
    costo_adquisicion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    fecha_ingreso_desarme = models.DateField(null=True, blank=True)
    estado_desarme = models.CharField(
        max_length=20,
        choices=ESTADO_DESARME_CHOICES,
        null=True,
        blank=True,
    )
    ubicacion_fisica = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="Ubicación en la yarda (ej: fila 3, posición 12).",
    )
    fecha_baja_desarme = models.DateField(null=True, blank=True)
    observaciones_desarme = models.TextField(blank=True, null=True)

    def __str__(self):
        marca_str = self.get_marca_display()
        modelo_str = self.get_modelo_display()
        ident = self.patente or self.vin or f"ID {self.pk}"
        return f"{ident} - {marca_str} {modelo_str}".strip()

    def get_marca_display(self):
        if self.marca_texto:
            return self.marca_texto
        if self.marca:
            return str(self.marca)
        return "Sin marca"

    def get_modelo_display(self):
        if self.modelo_texto:
            return self.modelo_texto
        if self.modelo:
            return str(self.modelo)
        return "Sin modelo"

    def clean(self):
        super().clean()
        if not (self.patente and str(self.patente).strip()) and not (
            self.vin and str(self.vin).strip()
        ):
            raise ValidationError("Debe registrar al menos VIN o Patente.")

    class Meta(TenantScoped.Meta):
        ordering = ["-fecha_ingreso_desarme", "-id"]
        verbose_name = "Vehículo de desarme"
        verbose_name_plural = "Vehículos de desarme"
        indexes = [
            models.Index(fields=["empresa"]),
            models.Index(fields=["empresa", "estado_desarme"]),
            models.Index(fields=["vehiculo_origen_id"]),
        ]
