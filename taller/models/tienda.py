from django.db import models
from .empresa import Empresa

class Tienda(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='tiendas')
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tienda'
        verbose_name_plural = 'Tiendas'
        db_table = 'taller_tienda'

    def __str__(self):
        return self.nombre
