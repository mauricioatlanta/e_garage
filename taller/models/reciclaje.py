"""
taller/models/reciclaje.py — Reciclaje / chatarra electrónica y catalíticos.

Dominio separado de Repuesto/PiezaDesarme: CategoriaChatarra, ProductoChatarra
y Catalitico son inventario de material reciclable (vendido a granel o por
unidad para su valor en metales), no repuestos funcionales para reinstalar
en un vehículo. No comparten tabla ni FK con el flujo de desarmaduría.
"""

from decimal import Decimal

from django.db import models
from django.db.models import Index, Q, UniqueConstraint

from core.models import TenantScoped


class CategoriaChatarra(TenantScoped):
    nombre = models.CharField(max_length=120, db_index=True)
    descripcion = models.TextField(blank=True, default="")

    class Meta(TenantScoped.Meta):
        verbose_name = "Categoría de Chatarra"
        verbose_name_plural = "Categorías de Chatarra"
        indexes = [
            Index(fields=["empresa", "nombre"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "nombre"],
                condition=Q(nombre__isnull=False) & ~Q(nombre=""),
                name="uq_categoria_chatarra_empresa_nombre_present",
            ),
        ]

    def __str__(self):
        return self.nombre or f"Categoría #{self.pk}"


class ProductoChatarra(TenantScoped):
    """
    Material de chatarra electrónica (cables, placas, aluminio, cobre, etc.)
    comprado/vendido típicamente a granel por peso.
    """

    UNIDAD_KG = "KG"
    UNIDAD_UNIDAD = "UNIDAD"
    UNIDAD_CHOICES = [
        (UNIDAD_KG, "Kilogramo"),
        (UNIDAD_UNIDAD, "Unidad"),
    ]

    codigo = models.CharField(max_length=64, db_index=True)
    nombre = models.CharField(max_length=160, db_index=True)
    categoria = models.ForeignKey(
        CategoriaChatarra,
        on_delete=models.PROTECT,
        db_index=True,
        null=True,
        blank=True,
    )
    unidad_medida = models.CharField(
        max_length=10, choices=UNIDAD_CHOICES, default=UNIDAD_KG
    )
    precio_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio de compra por unidad de medida.",
    )
    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio de venta por unidad de medida.",
    )
    cantidad_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Cantidad disponible en stock (kg o unidades según unidad_medida).",
    )
    stock_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )
    proveedor = models.CharField(max_length=200, null=True, blank=True)
    origen_importacion = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="Referencia del lote/archivo CSV de origen, si el registro fue importado.",
    )
    activo = models.BooleanField(default=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Producto de Chatarra"
        verbose_name_plural = "Productos de Chatarra"
        indexes = [
            Index(fields=["empresa", "codigo"]),
            Index(fields=["empresa", "nombre"]),
            Index(fields=["empresa", "categoria"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "codigo"],
                condition=Q(codigo__isnull=False) & ~Q(codigo=""),
                name="uq_producto_chatarra_empresa_codigo_present",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Catalitico(TenantScoped):
    """
    Convertidor catalítico individual. Se modela aparte de Repuesto/PiezaDesarme
    porque no es una pieza de reemplazo funcional: es material de acopio
    valorizado por su contenido de metales preciosos.
    """

    TIPO_CERAMICO = "CERAMICO"
    TIPO_METALICO = "METALICO"
    TIPO_DESCONOCIDO = "DESCONOCIDO"
    TIPO_CHOICES = [
        (TIPO_CERAMICO, "Cerámico"),
        (TIPO_METALICO, "Metálico"),
        (TIPO_DESCONOCIDO, "Desconocido"),
    ]

    ESTADO_DISPONIBLE = "DISPONIBLE"
    ESTADO_RESERVADO = "RESERVADO"
    ESTADO_VENDIDO = "VENDIDO"
    ESTADO_CHOICES = [
        (ESTADO_DISPONIBLE, "Disponible"),
        (ESTADO_RESERVADO, "Reservado"),
        (ESTADO_VENDIDO, "Vendido"),
    ]

    codigo = models.CharField(max_length=64, db_index=True)
    nombre = models.CharField(max_length=160, blank=True, default="")
    marca_vehiculo = models.CharField(max_length=100, blank=True, default="")
    modelo_vehiculo = models.CharField(max_length=150, blank=True, default="")
    tipo_catalizador = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default=TIPO_DESCONOCIDO
    )
    peso_kg = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    precio_compra = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    precio_venta = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    cantidad_stock = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default=ESTADO_DISPONIBLE, db_index=True
    )
    imagen = models.ImageField(
        upload_to="cataliticos/",
        null=True,
        blank=True,
        help_text="Foto del catalítico. No se completa en la importación masiva inicial.",
    )
    ubicacion_fisica = models.CharField(max_length=120, null=True, blank=True)
    observaciones = models.TextField(blank=True, default="")
    activo = models.BooleanField(default=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Catalítico"
        verbose_name_plural = "Catalíticos"
        indexes = [
            Index(fields=["empresa", "codigo"]),
            Index(fields=["empresa", "estado"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "codigo"],
                condition=Q(codigo__isnull=False) & ~Q(codigo=""),
                name="uq_catalitico_empresa_codigo_present",
            ),
        ]

    def __str__(self):
        return f"{self.nombre or 'Catalítico'} ({self.codigo})"
