from django.db import models
from django.contrib.auth.models import User

class TallerInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='taller_info')
    nombre_taller = models.CharField(max_length=255)
    telefono = models.CharField(max_length=32)
    ha_usado_prueba = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre_taller} ({self.user.email})"
