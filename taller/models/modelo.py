from django.db import models

class Modelo(models.Model):
    nombre = models.CharField(max_length=50)
    marca = models.ForeignKey('taller.Marca', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"

    def __str__(self):
        return self.nombre
