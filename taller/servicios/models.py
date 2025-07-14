from taller.models.documento import Documento
from django.db import models

class CategoriaServicio(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class SubcategoriaServicio(models.Model):
    categoria = models.ForeignKey(CategoriaServicio, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    subcategoria = models.ForeignKey(SubcategoriaServicio, on_delete=models.CASCADE, related_name='servicios')

    def __str__(self):
        return self.nombre
