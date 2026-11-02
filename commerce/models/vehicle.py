from django.db import models
from core.models import TenantScoped


class CommerceVehicleBrand(TenantScoped):
    name = models.CharField(max_length=80)
    external_id = models.IntegerField(null=True, blank=True, help_text="ID en la BD origen (MonteAzul SQLite)")

    class Meta(TenantScoped.Meta):
        verbose_name = "Marca de vehículo"
        verbose_name_plural = "Marcas de vehículo"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "name"],
                name="uq_commerce_vehiclebrand_empresa_name",
            ),
        ]

    def __str__(self):
        return self.name


class CommerceVehicleModel(TenantScoped):
    brand = models.ForeignKey(
        CommerceVehicleBrand,
        on_delete=models.CASCADE,
        related_name="models",
    )
    name = models.CharField(max_length=120)
    external_id = models.IntegerField(null=True, blank=True, help_text="ID en la BD origen (MonteAzul SQLite)")

    class Meta(TenantScoped.Meta):
        verbose_name = "Modelo de vehículo"
        verbose_name_plural = "Modelos de vehículo"
        ordering = ["name"]

    def __str__(self):
        return f"{self.brand.name} {self.name}"
