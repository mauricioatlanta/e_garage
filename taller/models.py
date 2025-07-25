from django.db import models

class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Modelo(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='modelos')

    class Meta:
        unique_together = ('nombre', 'marca')

    def __str__(self):
        return f"{self.nombre} ({self.marca.nombre})"
