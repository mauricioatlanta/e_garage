from django.db import models
from django.contrib.auth.models import User
from .region_ciudad import TallerRegion, TallerCiudad



class AuditModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_%(class)s"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="updated_%(class)s"
    )

    class Meta:
        abstract = True


class Cliente(models.Model):
    # Este campo conecta cada registro con la empresa dueña del dato
    empresa = models.ForeignKey('taller.Empresa', on_delete=models.CASCADE)  # Campo obligatorio
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    region = models.ForeignKey(TallerRegion, models.DO_NOTHING, blank=True, null=True)
    ciudad = models.ForeignKey(TallerCiudad, models.DO_NOTHING, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        db_table = 'taller_cliente'
        managed = True

    def __str__(self):
        nombre = self.nombre or ''
        apellido = self.apellido or ''
        texto = (nombre + ' ' + apellido).strip()

        if texto:
            return texto

        if self.email:
            return f"{self.email}"
        if self.telefono:
            return f"Cliente {self.telefono}"
        return f"Cliente #{self.pk}"
