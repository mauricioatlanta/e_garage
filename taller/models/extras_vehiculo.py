from django.db import models

from .modelo import Modelo


class ColorVehiculo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    hex = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text="Código de color hexadecimal (#FF0000)",
    )
    # TEMPORAL: Campo country comentado hasta aplicar migración
    # country = models.CharField(
    #     max_length=2,
    #     default='CL',
    #     choices=[
    #         ('CL', 'Chile'),
    #         ('US', 'Estados Unidos'),
    #     ],
    #     verbose_name="País",
    #     null=True,
    #     blank=True
    # )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Color"
        verbose_name_plural = "Colores"

    def __str__(self):
        return self.nombre

    @classmethod
    def get_colores_para_pais(cls, country="CL"):
        """Obtiene colores apropiados para el país especificado"""
        # TEMPORAL: Sin campo country en DB, usar filtrado por nombres
        if country == "CL":
            # Crear colores en español para Chile si no existen
            colores_español = [
                "Blanco",
                "Negro",
                "Rojo",
                "Azul",
                "Verde",
                "Amarillo",
                "Gris",
                "Plateado",
                "Dorado",
                "Café",
                "Morado",
                "Naranja",
            ]

            # Crear colores si no existen
            for color_nombre in colores_español:
                cls.objects.get_or_create(nombre=color_nombre)

            # Filtrar colores que están en español
            colores_españoles = cls.objects.filter(nombre__in=colores_español).order_by(
                "nombre"
            )

            if colores_españoles.exists():
                return colores_españoles

        # Para otros países o fallback, devolver todos los colores
        return cls.objects.all().order_by("nombre")


class MotorVehiculo(models.Model):
    nombre = models.CharField(max_length=100)
    modelos = models.ManyToManyField(Modelo, related_name="motores", blank=True)
    # TEMPORAL: Campo country comentado hasta aplicar migración
    # country = models.CharField(
    #     max_length=2,
    #     default='CL',
    #     choices=[
    #         ('CL', 'Chile'),
    #         ('US', 'Estados Unidos'),
    #     ],
    #     verbose_name="País"
    # )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Motor"
        verbose_name_plural = "Motores"
        # indexes = [
        #     models.Index(fields=['country', 'nombre']),
        # ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # TEMPORAL: Sin campo country hasta migración
        super().save(*args, **kwargs)


class CajaVehiculo(models.Model):
    nombre = models.CharField(max_length=100)
    modelos = models.ManyToManyField(Modelo, related_name="cajas", blank=True)
    # TEMPORAL: Campo country comentado hasta aplicar migración
    # country = models.CharField(
    #     max_length=2,
    #     default='CL',
    #     choices=[
    #         ('CL', 'Chile'),
    #         ('US', 'Estados Unidos'),
    #     ],
    #     verbose_name="País"
    # )

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        # indexes = [
        #     models.Index(fields=['country', 'nombre']),
        # ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # TEMPORAL: Sin campo country hasta migración
        super().save(*args, **kwargs)
