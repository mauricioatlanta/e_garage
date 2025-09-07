from django.db import models


class Estado(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    zip_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.nombre}, {self.estado}"
