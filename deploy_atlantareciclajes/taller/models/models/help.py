"""
Modelos para el Centro de Ayuda de eGarage
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class HelpCategory(models.Model):
    """Categoría de artículos de ayuda"""

    nombre = models.CharField(max_length=100, unique=True)
    icono = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nombre del icono (ej: 'fa-home', 'fa-users', 'fa-file-invoice')",
    )
    slug = models.SlugField(unique=True, max_length=100)
    descripcion = models.TextField(blank=True, help_text="Descripción breve de la categoría")
    orden = models.IntegerField(default=0, help_text="Orden de visualización")
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría de Ayuda"
        verbose_name_plural = "Categorías de Ayuda"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("help:categoria", kwargs={"slug": self.slug})


class HelpArticle(models.Model):
    """Artículo individual del Centro de Ayuda"""

    categoria = models.ForeignKey(HelpCategory, related_name="articulos", on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    contenido = models.TextField(help_text="Contenido del artículo (HTML permitido)")
    orden = models.IntegerField(default=0, help_text="Orden dentro de la categoría")
    activo = models.BooleanField(default=True)
    visitas = models.IntegerField(default=0, help_text="Contador de visitas")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Artículo de Ayuda"
        verbose_name_plural = "Artículos de Ayuda"
        ordering = ["categoria", "orden", "titulo"]
        indexes = [
            models.Index(fields=["categoria", "activo"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.categoria.nombre} - {self.titulo}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("help:articulo", kwargs={"slug": self.slug})

    def incrementar_visitas(self):
        """Incrementa el contador de visitas"""
        self.visitas += 1
        self.save(update_fields=["visitas"])
