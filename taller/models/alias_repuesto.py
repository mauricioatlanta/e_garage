from django.db import models


class AliasRepuesto(models.Model):
    """
    Sinónimos y variantes regionales para nombres de piezas.
    Permite que la búsqueda del kiosko encuentre la misma pieza con distintos términos.

    La pieza se guarda con su nombre canónico (ej: "alternador"). Esta tabla
    amplía qué términos de búsqueda la encuentran, sin tocar PiezaDesarme ni Part.
    """

    pieza_canonica = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Nombre interno único de la pieza. Ej: 'alternador'",
    )
    termino_busqueda = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Sinónimo o variante regional. Ej: 'generador', 'alternadora'",
    )
    pais = models.CharField(
        max_length=2,
        blank=True,
        help_text="Código de país (CL, MX, US…). Vacío = aplica a todos los mercados.",
    )

    class Meta:
        verbose_name = "Alias de repuesto"
        verbose_name_plural = "Aliases de repuestos"
        unique_together = [("pieza_canonica", "termino_busqueda", "pais")]
        indexes = [
            models.Index(fields=["pais", "termino_busqueda"]),
        ]

    def __str__(self):
        scope = f" [{self.pais}]" if self.pais else " [global]"
        return f"{self.termino_busqueda} → {self.pieza_canonica}{scope}"
