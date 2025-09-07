from django.db import models


class Marca(models.Model):
    nombre = models.CharField(max_length=50)
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[
            ("CL", "Chile"),
            ("US", "Estados Unidos"),
        ],
        verbose_name="País",
    )

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nombre"]  # Ordenamiento alfabético por defecto
        unique_together = [("country", "nombre")]
        indexes = [
            models.Index(fields=["country", "nombre"]),
        ]

    def __str__(self):
        return self.nombre
