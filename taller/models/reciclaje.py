"""
taller/models/reciclaje.py — Reciclaje / chatarra electrónica y catalíticos.

Dominio separado de Repuesto/PiezaDesarme: CategoriaChatarra, ProductoChatarra
y Catalitico son inventario de material reciclable (vendido a granel o por
unidad para su valor en metales), no repuestos funcionales para reinstalar
en un vehículo. No comparten tabla ni FK con el flujo de desarmaduría.
"""

from decimal import Decimal

from django.conf import settings
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


# ─────────────────────────────────────────────────────────────────────────────
# Compra / Venta — el corazón del negocio: adquirir material de un cliente que
# llega con catalíticos/chatarra, y luego revenderlo.
#
# Catalitico y ProductoChatarra son, ambos, SKU con cantidad_stock — no hay una
# fila por unidad física única. Comprar INCREMENTA cantidad_stock (creando el
# SKU si el código todavía no existe); vender DECREMENTA cantidad_stock y, si
# llega a 0, marca el Catalitico como VENDIDO (ProductoChatarra no tiene ese
# concepto de estado, solo cantidad). Por eso los 4 modelos de detalle son
# simétricos: compra/venta × catalítico/chatarra, cada uno con FK al SKU +
# cantidad + precio_unitario.
# ─────────────────────────────────────────────────────────────────────────────


class CompraReciclaje(TenantScoped):
    """Encabezado de una compra de material reciclable a un cliente (walk-in
    o registrado). Las líneas viven en DetalleCompraCatalitico/Chatarra."""

    cliente = models.ForeignKey(
        "taller.Cliente",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="compras_reciclaje",
        help_text="Vacío = cliente de mostrador (Cliente.get_or_create_mostrador).",
    )
    region = models.ForeignKey(
        "taller.Estado", on_delete=models.SET_NULL, null=True, blank=True
    )
    ciudad = models.ForeignKey(
        "taller.Ciudad", on_delete=models.SET_NULL, null=True, blank=True
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compras_reciclaje_creadas",
    )
    notas = models.TextField(blank=True, default="")

    class Meta(TenantScoped.Meta):
        verbose_name = "Compra de Reciclaje"
        verbose_name_plural = "Compras de Reciclaje"
        indexes = [Index(fields=["empresa", "created_at"])]

    def total(self) -> Decimal:
        total_catalitico = sum(
            (d.subtotal() for d in self.detalles_catalitico.all()), Decimal("0")
        )
        total_chatarra = sum(
            (d.subtotal() for d in self.detalles_chatarra.all()), Decimal("0")
        )
        return total_catalitico + total_chatarra

    def __str__(self):
        return f"Compra #{self.pk} — {self.cliente or 'Mostrador'}"


class DetalleCompraCatalitico(models.Model):
    """Una línea de compra = cantidad de un Catalitico (SKU) adquirida
    (incrementa cantidad_stock del catalítico; lo crea si el código es nuevo)."""

    compra = models.ForeignKey(
        CompraReciclaje, on_delete=models.CASCADE, related_name="detalles_catalitico"
    )
    catalitico = models.ForeignKey(
        Catalitico, on_delete=models.PROTECT, related_name="compras_detalle"
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.catalitico.codigo} x{self.cantidad}"

    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario


class DetalleCompraChatarra(models.Model):
    """Una línea de compra = cantidad de un ProductoChatarra adquirida
    (incrementa cantidad_stock del producto)."""

    compra = models.ForeignKey(
        CompraReciclaje, on_delete=models.CASCADE, related_name="detalles_chatarra"
    )
    producto = models.ForeignKey(
        ProductoChatarra, on_delete=models.PROTECT, related_name="compras_detalle"
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario


class VentaReciclaje(TenantScoped):
    """Encabezado de una venta de material reciclable (reventa de catalíticos
    ya comprados / chatarra en stock a un comprador externo)."""

    comprador = models.ForeignKey(
        "taller.Cliente",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ventas_reciclaje",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_reciclaje_creadas",
    )
    notas = models.TextField(blank=True, default="")

    class Meta(TenantScoped.Meta):
        verbose_name = "Venta de Reciclaje"
        verbose_name_plural = "Ventas de Reciclaje"
        indexes = [Index(fields=["empresa", "created_at"])]

    def total(self) -> Decimal:
        total_catalitico = sum(
            (d.subtotal() for d in self.detalles_catalitico.all()), Decimal("0")
        )
        total_chatarra = sum(
            (d.subtotal() for d in self.detalles_chatarra.all()), Decimal("0")
        )
        return total_catalitico + total_chatarra

    def __str__(self):
        return f"Venta #{self.pk} — {self.comprador or 'Sin comprador'}"


class DetalleVentaCatalitico(models.Model):
    """Una línea de venta = cantidad de un Catalitico (SKU) vendida
    (decrementa cantidad_stock; si llega a 0, el catalítico pasa a VENDIDO)."""

    venta = models.ForeignKey(
        VentaReciclaje, on_delete=models.CASCADE, related_name="detalles_catalitico"
    )
    catalitico = models.ForeignKey(
        Catalitico, on_delete=models.PROTECT, related_name="ventas_detalle"
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.catalitico.codigo} x{self.cantidad}"

    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario


class DetalleVentaChatarra(models.Model):
    """Una línea de venta = cantidad de un ProductoChatarra vendida
    (decrementa cantidad_stock del producto)."""

    venta = models.ForeignKey(
        VentaReciclaje, on_delete=models.CASCADE, related_name="detalles_chatarra"
    )
    producto = models.ForeignKey(
        ProductoChatarra, on_delete=models.PROTECT, related_name="ventas_detalle"
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    def subtotal(self) -> Decimal:
        return self.cantidad * self.precio_unitario
