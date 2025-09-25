from django.db import models


class TallerMecanico(models.Model):
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    empresa = models.ForeignKey(
        "taller.Empresa", on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        db_table = "taller_mecanico"
        unique_together = (("empresa", "nombre"),)
