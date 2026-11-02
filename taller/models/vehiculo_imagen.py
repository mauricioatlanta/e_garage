import os
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

from core.models import TenantScoped


class VehiculoImagen(TenantScoped):
    TIPO_CHOICES = [
        ("frontal", "Frontal"),
        ("trasera", "Trasera"),
        ("lateral", "Lateral"),
        ("interior", "Interior"),
        ("motor", "Motor"),
        ("danio", "Daño"),
        ("documento", "Documento"),
        ("pieza", "Pieza"),
        ("otro", "Otro"),
    ]

    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="imagenes",
    )

    imagen = models.ImageField(upload_to="vehiculos/%Y/%m/")

    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        default="otro",
        blank=True,
    )

    orden = models.PositiveIntegerField(default=0)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "-created_at"]

    def __str__(self):
        return f"{self.vehiculo} - {self.tipo}"

    def save(self, *args, **kwargs):
        if self.imagen and not str(self.imagen.name).lower().endswith(".webp"):
            self.imagen = self._optimizar_imagen(self.imagen)
        super().save(*args, **kwargs)

    def _optimizar_imagen(self, imagen):
        img = Image.open(imagen)
        img = ImageOps.exif_transpose(img)

        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")

        max_size = (1280, 1280)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=70, optimize=True)
        buffer.seek(0)

        base_name = os.path.splitext(os.path.basename(imagen.name))[0]
        safe_name = f"{base_name}_{uuid.uuid4().hex[:8]}.webp"

        return ContentFile(buffer.read(), name=safe_name)
