
from django.db import models

class Tienda(models.Model):
    # ...existing code...
    telefono = models.CharField(max_length=20, blank=True, null=True)
    # ...existing code...