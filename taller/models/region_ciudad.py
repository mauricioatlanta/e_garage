from django.db import models

class TallerRegion(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'taller_region'

    def __str__(self):
        return self.nombre

class TallerCiudad(models.Model):
    nombre = models.CharField(max_length=100)
    region = models.ForeignKey(TallerRegion, on_delete=models.CASCADE, related_name='ciudades')

    class Meta:
        db_table = 'taller_ciudad'

    def __str__(self):
        return self.nombre
