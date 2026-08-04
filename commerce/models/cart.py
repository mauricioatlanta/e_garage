from django.db import models

from core.models import TenantScoped

from .product import CommerceProduct


class CommerceCart(TenantScoped):
    """Carrito anónimo vinculado a session_key + empresa."""

    session_key = models.CharField(max_length=40, db_index=True)

    class Meta(TenantScoped.Meta):
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "session_key"],
                name="uq_commerce_cart_empresa_session",
            )
        ]

    def __str__(self):
        return f"Carrito {self.session_key[:8]}… ({self.empresa})"


class CommerceCartItem(models.Model):
    cart = models.ForeignKey(CommerceCart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(CommerceProduct, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "Ítem de carrito"
        verbose_name_plural = "Ítems de carrito"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="uq_commerce_cartitem_cart_product",
            )
        ]

    def __str__(self):
        return f"{self.product} × {self.quantity}"

    @property
    def subtotal(self):
        return self.product.precio_venta * self.quantity
