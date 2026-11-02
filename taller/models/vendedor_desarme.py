"""
Vendedor/proveedor de compra para desarme.

Entidad estructurada para evitar duplicados por texto libre.
Relación por empresa, búsqueda y creación controlada con validación anti-duplicado.
"""

from django.db import models


class VendedorDesarme(models.Model):
    """
    Vendedor o proveedor del cual se compra un vehículo para desarme.
    Por empresa. Permite reportes confiables por vendedor.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="vendedores_desarme",
        db_index=True,
    )
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Documento / Tax ID",
    )
    lugar_compra = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Dónde se compró normalmente",
    )
    id_imagen = models.ImageField(
        upload_to="desarme_vendedor_id/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Imagen I.D.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Vendedor desarme"
        verbose_name_plural = "Vendedores desarme"
        indexes = [
            models.Index(fields=["empresa", "nombre"]),
        ]

    def __str__(self):
        parts = [self.nombre]
        if self.telefono:
            parts.append(self.telefono)
        return " | ".join(parts)
