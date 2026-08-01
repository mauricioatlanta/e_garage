from django.db import models

from core.models import TenantScoped

from .product import CommerceProduct


class CommerceOrder(TenantScoped):

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (PENDING, "Pendiente"),
        (CONFIRMED, "Confirmado"),
        (PROCESSING, "En proceso"),
        (SHIPPED, "Despachado"),
        (DELIVERED, "Entregado"),
        (CANCELLED, "Cancelado"),
    ]

    order_number = models.CharField(max_length=40, unique=True, db_index=True)
    session_key = models.CharField(max_length=40, db_index=True, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True, default="")
    shipping_address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    # Total congelado al crear el pedido
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta(TenantScoped.Meta):
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido {self.order_number} — {self.customer_name}"


class CommerceOrderItem(models.Model):
    """Snapshot congelado de cada línea al momento de crear el pedido."""

    order = models.ForeignKey(CommerceOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        CommerceProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    # Datos congelados — no cambian aunque el producto se edite o elimine
    sku = models.CharField(max_length=100, blank=True, default="")
    name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "Ítem de pedido"
        verbose_name_plural = "Ítems de pedido"

    def __str__(self):
        return f"{self.name} × {self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
