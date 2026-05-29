"""
Modelos para el Marketplace de eGarage
Permite gestionar catálogos de casas de repuestos sin que el cliente final vea precios ni proveedores
"""

from decimal import Decimal

from django.db import models
from django.db.models import Index, Q, UniqueConstraint

from core.models import TenantScoped


class CasaRepuestos(TenantScoped):
    """
    Casa de repuestos proveedora.
    Ejemplo: Indra, Bosch, NGK, etc.
    """

    nombre = models.CharField(
        max_length=200, db_index=True, help_text="Nombre de la casa de repuestos"
    )
    contacto = models.CharField(
        max_length=200, blank=True, null=True, help_text="Contacto o persona responsable"
    )
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activa = models.BooleanField(default=True, help_text="Si la casa de repuestos está activa")

    class Meta(TenantScoped.Meta):
        app_label = "marketplace"
        verbose_name = "Casa de Repuestos"
        verbose_name_plural = "Casas de Repuestos"
        indexes = [
            Index(fields=["empresa", "nombre"]),
            Index(fields=["empresa", "activa"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "nombre"],
                condition=Q(nombre__isnull=False) & ~Q(nombre=""),
                name="uq_casa_repuestos_empresa_nombre",
            ),
        ]

    def __str__(self):
        return self.nombre


class ProductoCatalogo(TenantScoped):
    """
    Producto del catálogo del marketplace.
    Este modelo contiene información de precios y proveedores que NO debe ser visible para el cliente final.

    IMPORTANTE: visibilidad_cliente = False asegura que esta información nunca se muestre
    en el Portal del Cliente, solo en el sistema interno del taller.
    """

    # Relación con casa de repuestos
    casa_repuestos = models.ForeignKey(
        CasaRepuestos,
        on_delete=models.PROTECT,
        related_name="productos",
        help_text="Casa de repuestos que provee este producto",
    )

    # Part number para relacionar con repuestos
    part_number = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Part number del repuesto (debe coincidir con el part_number del Repuesto)",
    )

    nombre = models.CharField(max_length=255, db_index=True, help_text="Nombre del producto")

    # Precios - NUNCA visibles para el cliente
    precio_referencia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Precio de referencia de la casa de repuestos (solo para el taller, no visible para cliente)",
    )

    precio_compra_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio mínimo de compra (opcional)",
    )

    # Estado y disponibilidad
    activo = models.BooleanField(
        default=True, help_text="Si el producto está disponible en el catálogo"
    )

    disponible = models.BooleanField(
        default=True, help_text="Si el producto está actualmente disponible en stock"
    )

    # Información adicional (solo para taller)
    observaciones = models.TextField(
        blank=True, null=True, help_text="Observaciones internas (no visibles para cliente)"
    )

    # Metadata
    ultima_actualizacion_precio = models.DateTimeField(
        auto_now=True, help_text="Última vez que se actualizó el precio"
    )

    class Meta(TenantScoped.Meta):
        app_label = "marketplace"
        verbose_name = "Producto del Catálogo"
        verbose_name_plural = "Productos del Catálogo"
        indexes = [
            Index(fields=["empresa", "part_number"]),
            Index(fields=["empresa", "casa_repuestos"]),
            Index(fields=["empresa", "activo"]),
            Index(fields=["empresa", "part_number", "casa_repuestos"]),  # Para búsquedas rápidas
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "part_number", "casa_repuestos"],
                name="uq_producto_catalogo_empresa_partnumber_casa",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.part_number}) - {self.casa_repuestos.nombre}"

    @property
    def visibilidad_cliente(self):
        """
        Campo crucial: siempre False.
        Esto garantiza que este modelo nunca se muestre en el Portal del Cliente.
        """
        return False


class WhatsAppEnvio(models.Model):
    """
    Registro de envíos de WhatsApp para control de rate limiting.
    Previene spam y protege la reputación del número de WhatsApp.
    """

    empresa = models.ForeignKey(
        "taller.Empresa", on_delete=models.CASCADE, related_name="whatsapp_envios", db_index=True
    )
    telefono_destino = models.CharField(max_length=50, db_index=True)
    tipo_envio = models.CharField(
        max_length=20,
        choices=[
            ("cliente", "Cliente"),
            ("proveedor", "Proveedor"),
        ],
        db_index=True,
    )
    documento_id = models.IntegerField(null=True, blank=True, db_index=True)
    mensaje_enviado = models.TextField(blank=True)
    fecha_envio = models.DateTimeField(auto_now_add=True, db_index=True)
    mensaje_id = models.CharField(max_length=255, blank=True, null=True)
    exito = models.BooleanField(default=True)

    class Meta:
        app_label = "marketplace"
        verbose_name = "Envío de WhatsApp"
        verbose_name_plural = "Envíos de WhatsApp"
        indexes = [
            Index(fields=["empresa", "telefono_destino", "fecha_envio"]),
            Index(fields=["empresa", "tipo_envio", "fecha_envio"]),
        ]
        ordering = ["-fecha_envio"]

    def __str__(self):
        return f"{self.tipo_envio} - {self.telefono_destino} - {self.fecha_envio}"
