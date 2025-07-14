from django.db import models

# Create your models here.

class Tienda(models.Model):
    # ...existing code...
    telefono = models.CharField(max_length=20, blank=True, null=True)
    # ...existing code...