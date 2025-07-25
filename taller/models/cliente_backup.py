from django.db import models
from taller.models.empresa import Empresa

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)  # NUEVO
    # ...otros campos...

    def __str__(self):
        return f"{self.nombre} ({self.email})"
