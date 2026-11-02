"""
Catálogo global de marcas y modelos de vehículos
Fuente: Scraping de VehiclesAPI (USA 1970-presente)
Multi-tenant: datos globales compartidos entre todas las empresas
"""

from django.db import models


class CatalogoModeloAuto(models.Model):
    """
    Catálogo global de marcas y modelos de vehículos
    No depende de Empresa - es una referencia compartida para autocompletado
    """

    marca = models.CharField(
        max_length=100, db_index=True, help_text="Marca del vehículo (ej: Toyota)"
    )
    modelo = models.CharField(
        max_length=150, db_index=True, help_text="Modelo del vehículo (ej: Camry)"
    )

    # Metadatos para mejor rendimiento y validación
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, help_text="Si false, no aparece en autocompletado")

    class Meta:
        verbose_name = "Catálogo Marca-Modelo"
        verbose_name_plural = "Catálogo Marcas-Modelos"
        unique_together = (("marca", "modelo"),)
        indexes = [
            models.Index(fields=["marca", "modelo"], name="idx_marca_modelo"),
            models.Index(fields=["marca"], name="idx_marca_only"),
            models.Index(fields=["activo"], name="idx_catalogo_activo"),
        ]
        ordering = ["marca", "modelo"]

    def __str__(self):
        return f"{self.marca} {self.modelo}"

    @classmethod
    def get_marcas_activas(cls):
        """Retorna lista única de marcas activas ordenadas"""
        return (
            cls.objects.filter(activo=True)
            .values_list("marca", flat=True)
            .distinct()
            .order_by("marca")
        )

    @classmethod
    def get_modelos_por_marca(cls, marca):
        """Retorna modelos para una marca específica"""
        return (
            cls.objects.filter(marca__iexact=marca, activo=True)
            .values_list("modelo", flat=True)
            .order_by("modelo")
        )

    def clean(self):
        """Validación y normalización"""
        if self.marca:
            self.marca = self.marca.strip().title()
        if self.modelo:
            self.modelo = self.modelo.strip()
