from django.db import models


class Modelo(models.Model):
    nombre = models.CharField(max_length=50)
    marca = models.ForeignKey("taller.Marca", on_delete=models.CASCADE)
    country = models.CharField(
        max_length=2,
        default="CL",
        choices=[
            ("CL", "Chile"),
            ("US", "Estados Unidos"),
            ("MX", "México"),
            ("PE", "Perú"),
            ("CO", "Colombia"),
            ("EC", "Ecuador"),
            ("BR", "Brasil"),
            ("VE", "Venezuela"),
        ],
        verbose_name="País",
    )

    class Meta:
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"
        unique_together = [("country", "marca", "nombre")]
        indexes = [
            models.Index(fields=["country", "marca", "nombre"]),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Asegurar que el country coincida con el de la marca
        if hasattr(self, "marca") and self.marca:
            self.country = self.marca.country
        super().save(*args, **kwargs)
