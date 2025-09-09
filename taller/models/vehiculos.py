from django.db import models
from django.urls import reverse

from core.models import TenantManager, TenantScoped

from .clientes import Cliente
from .extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo
from .marca import Marca
from .modelo import Modelo


class Vehiculo(TenantScoped):
    # empresa viene de TenantScoped (inicialmente nullable en migración)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    # Campo marca flexible: puede ser ForeignKey a Marca (Chile) o CharField (USA catálogo global)
    marca = models.ForeignKey(
        Marca,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Marca del vehículo (Chile: referencia a modelo Marca, USA: texto del catálogo)",
    )
    marca_texto = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Marca como texto (para USA catálogo global)",
    )

    # Campo modelo flexible: puede ser ForeignKey a Modelo (Chile) o CharField (USA catálogo global)
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Modelo del vehículo (Chile: referencia a modelo Modelo, USA: texto del catálogo)",
    )
    modelo_texto = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Modelo como texto (para USA catálogo global)",
    )

    patente = models.CharField(max_length=20, db_index=True)
    anio = models.PositiveIntegerField(verbose_name="Año")
    color = models.ForeignKey(
        ColorVehiculo, on_delete=models.SET_NULL, null=True, blank=True
    )
    vin = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    motor = models.ForeignKey(
        MotorVehiculo, on_delete=models.SET_NULL, null=True, blank=True
    )
    caja = models.ForeignKey(
        CajaVehiculo, on_delete=models.SET_NULL, null=True, blank=True
    )
    millas = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Millas/Kilometraje"
    )

    objects = TenantManager()

    def __str__(self):
        # Mostrar marca y modelo según el sistema usado
        marca_str = self.get_marca_display()
        modelo_str = self.get_modelo_display()
        return f"{self.patente} - {marca_str} {modelo_str}".strip()

    def get_marca_display(self):
        """Obtener el nombre de la marca según el sistema usado"""
        if self.marca_texto:
            return self.marca_texto
        elif self.marca:
            return str(self.marca)
        return "Sin marca"

    def get_modelo_display(self):
        """Obtener el nombre del modelo según el sistema usado"""
        if self.modelo_texto:
            return self.modelo_texto
        elif self.modelo:
            return str(self.modelo)
        return "Sin modelo"

    def get_absolute_url(self):  # usado por CreateView en tests
        try:
            return reverse("vehiculos:ver_vehiculo", args=[self.pk])
        except Exception:
            return "/vehiculos-core/"  # fallback seguro

    class Meta(TenantScoped.Meta):
        ordering = ["marca", "modelo", "patente"]
        verbose_name = "Vehículo"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "patente"], name="uq_empresa_patente"
            )
        ]
        indexes = [
            models.Index(fields=["empresa"]),
            models.Index(fields=["empresa", "patente"]),
            models.Index(fields=["empresa", "vin"]),
            models.Index(
                fields=["marca_texto"]
            ),  # Índice para búsquedas por marca texto
            models.Index(
                fields=["modelo_texto"]
            ),  # Índice para búsquedas por modelo texto
        ]
