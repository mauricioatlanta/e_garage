"""
Catálogo global de marcas y modelos de vehículos
Fuente: Scraping de VehiclesAPI (USA 1970-presente)
Multi-tenant: datos globales compartidos entre todas las empresas
"""

from django.db import models
from django.db.models import Q


class CatalogoModeloAuto(models.Model):
    """
    Catálogo global de marcas y modelos de vehículos
    No depende de Empresa - es una referencia compartida para autocompletado
    """

    marca = models.CharField(max_length=120, db_index=True)
    modelo = models.CharField(max_length=150, db_index=True)
    activo = models.BooleanField(default=True, help_text="Si false, no aparece en autocompletado")

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    anio_desde = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Año inicial del rango",
    )
    anio_hasta = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Año final del rango",
    )

    class Meta:
        verbose_name = "Catálogo Marca-Modelo"
        verbose_name_plural = "Catálogo Marcas-Modelos"
        unique_together = (("marca", "modelo", "anio_desde", "anio_hasta"),)
        indexes = [
            models.Index(fields=["marca"], name="idx_catalogo_marca"),
            models.Index(fields=["modelo"], name="idx_catalogo_modelo"),
            models.Index(fields=["activo"], name="idx_catalogo_activo"),
            models.Index(fields=["anio_desde", "anio_hasta"], name="idx_catalogo_anio"),
        ]
        ordering = ["marca", "modelo", "anio_desde", "anio_hasta"]

    def __str__(self):
        if self.anio_desde or self.anio_hasta:
            return f"{self.marca} {self.modelo} ({self.anio_desde or '?'}-{self.anio_hasta or '?'})"
        return f"{self.marca} {self.modelo}"

    def clean(self):
        super().clean()
        if self.marca:
            self.marca = self.marca.strip()
        if self.modelo:
            self.modelo = self.modelo.strip()
        if self.anio_desde and self.anio_hasta and self.anio_desde > self.anio_hasta:
            from django.core.exceptions import ValidationError

            raise ValidationError("anio_desde no puede ser mayor que anio_hasta")

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
        """Retorna modelos para una marca específica (sin filtro por año)"""
        return (
            cls.objects.filter(marca__iexact=marca, activo=True)
            .values_list("modelo", flat=True)
            .distinct()
            .order_by("modelo")
        )

    @classmethod
    def get_marcas_por_anio(cls, anio):
        """Marcas únicas con al menos un modelo activo en el año dado"""
        qs = cls.objects.filter(activo=True)
        qs = qs.filter(Q(anio_desde__lte=anio) | Q(anio_desde__isnull=True)).filter(
            Q(anio_hasta__gte=anio) | Q(anio_hasta__isnull=True)
        )
        return qs.values_list("marca", flat=True).distinct().order_by("marca")

    @classmethod
    def get_modelos_por_marca_anio(cls, marca, anio):
        """Modelos para marca y año, filtrados por rango"""
        qs = cls.objects.filter(marca__iexact=marca, activo=True)
        qs = qs.filter(Q(anio_desde__lte=anio) | Q(anio_desde__isnull=True)).filter(
            Q(anio_hasta__gte=anio) | Q(anio_hasta__isnull=True)
        )
        return qs.values_list("modelo", flat=True).distinct().order_by("modelo")
