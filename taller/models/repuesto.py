from decimal import Decimal

from django.db import models
from django.db.models import Index, Q, UniqueConstraint

from core.models import TenantScoped


class CategoriaRepuesto(TenantScoped):
    nombre = models.CharField(max_length=120, db_index=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Categoría de Repuesto"
        verbose_name_plural = "Categorías de Repuesto"
        indexes = [
            Index(fields=["empresa", "nombre"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "nombre"],
                condition=Q(nombre__isnull=False) & ~Q(nombre=""),
                name="uq_categoria_repuesto_empresa_nombre_present",
            ),
        ]

    def __str__(self):
        return self.nombre or f"Categoría #{self.pk}"


class Repuesto(TenantScoped):
    part_number = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    nombre = models.CharField(max_length=160, db_index=True)
    categoria = models.ForeignKey(
        CategoriaRepuesto,
        on_delete=models.PROTECT,
        db_index=True,
        null=True,
        blank=True,
    )
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio al que compraste el repuesto",
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio al que vendes el repuesto",
    )
    cantidad_stock = models.PositiveIntegerField(
        default=0, help_text="Cantidad disponible en stock"
    )
    stock_minimo = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Stock minimo recomendado para reabastecimiento",
    )
    proveedor = models.CharField(
        max_length=200, null=True, blank=True, help_text="Donde compraste el repuesto"
    )

    class Meta(TenantScoped.Meta):
        indexes = [
            Index(fields=["empresa", "part_number"]),
            Index(fields=["empresa", "nombre"]),
            Index(fields=["empresa", "categoria"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "part_number"],
                condition=Q(part_number__isnull=False) & ~Q(part_number=""),
                name="uq_repuesto_empresa_partnumber_present",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.part_number})"
