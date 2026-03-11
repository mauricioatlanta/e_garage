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
    """
    Repuesto del catálogo. Puede ser de tres naturalezas (tipo_origen):
    - STOCK: comprado para inventario; tiene stock, se descuenta al vender.
    - DIRECT: compra directa para vender sin almacenar; no control de stock.
    - DESARME: pieza de vehículo desarmado; típicamente stock=1, opcional vehiculo_origen.
    """

    TIPO_ORIGEN_CHOICES = [
        ("stock", "En stock"),
        ("direct", "Compra directa"),  # alias: directo
        ("directo", "Compra directa"),
        ("desarme", "Desarme"),
    ]
    ORIGEN_COSTO_CHOICES = [
        ("compra", "Compra"),
        ("desarme", "Desarme"),
        ("consignacion", "Consignación"),
    ]

    part_number = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    nombre = models.CharField(max_length=160, db_index=True)
    categoria = models.ForeignKey(
        CategoriaRepuesto,
        on_delete=models.PROTECT,
        db_index=True,
        null=True,
        blank=True,
    )
    # Naturaleza del repuesto: inventario clásico, venta directa sin stock, o pieza de desarme
    tipo_origen = models.CharField(
        max_length=20,
        choices=TIPO_ORIGEN_CHOICES,
        default="stock",
        db_index=True,
        help_text="STOCK=inventario, DIRECT=compra directa sin almacenar, DESARME=pieza de vehículo desarmado",
    )
    # Origen del costo (para reportes financieros y rentabilidad)
    origen_costo = models.CharField(
        max_length=20,
        choices=ORIGEN_COSTO_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Compra, desarme o consignación",
    )
    # Solo para tipo_origen=desarme: vehículo del que proviene la pieza
    vehiculo_origen = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repuestos_desarme",
        help_text="Vehículo origen (solo para repuestos de desarme)",
    )
    es_usado = models.BooleanField(
        default=False,
        help_text="Pieza usada (típicamente true para desarme)",
    )
    controlar_stock = models.BooleanField(
        default=True,
        help_text="Si False, no se descuenta inventario (ej. compra directa)",
    )
    # Solo para tipo_origen=desarme: estado en checklist de inspección
    ESTADO_PIEZA_CHOICES = [
        ("disponible", "Disponible"),
        ("dañado", "Dañado"),
        ("scrap", "Scrap"),
        ("vendido", "Vendido"),
        ("reservada", "Reservada"),
    ]
    estado_pieza = models.CharField(
        max_length=20,
        choices=ESTADO_PIEZA_CHOICES,
        default="disponible",
        blank=True,
        db_index=True,
        help_text="Solo para repuestos de desarme (checklist de inspección)",
    )
    # Mapa interactivo: zona y vista para repuestos de desarme
    zona_mapa = models.CharField(
        max_length=60,
        blank=True,
        default="",
        db_index=True,
        help_text="Código de zona en el mapa (ej. left_front_door, hood)",
    )
    vista_mapa = models.CharField(
        max_length=30,
        blank=True,
        default="",
        db_index=True,
        help_text="Vista del mapa (frontal, lateral_izq, lateral_der, trasera, motor)",
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
    proveedor = models.CharField(
        max_length=200, null=True, blank=True, help_text="Donde compraste el repuesto"
    )
    observaciones = models.TextField(
        blank=True,
        default="",
        help_text="Notas de inspección (ej. abolladura menor, sin espejo)",
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

    def clean(self):
        super().clean()
        if self.tipo_origen == "desarme" and not self.vehiculo_origen_id:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                {"vehiculo_origen": "Debe indicar el vehículo origen en repuestos de desarme."}
            )
        if self.tipo_origen in ("direct", "directo"):
            self.controlar_stock = False
