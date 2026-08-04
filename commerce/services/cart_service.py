from django.db.models import Sum

from commerce.models.cart import CommerceCart, CommerceCartItem
from commerce.models.product import CommerceProduct


class CartService:

    @staticmethod
    def get_or_create(empresa, session_key: str) -> CommerceCart:
        if not session_key:
            raise ValueError("session_key requerido para crear un carrito.")
        cart, _ = CommerceCart.objects.get_or_create(
            empresa=empresa,
            session_key=session_key,
        )
        return cart

    @staticmethod
    def add_item(cart: CommerceCart, product: CommerceProduct, quantity: int = 1) -> CommerceCartItem:
        if quantity < 1:
            raise ValueError("La cantidad debe ser mayor a cero.")
        item, created = CommerceCartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        return item

    @staticmethod
    def update_item(cart: CommerceCart, product: CommerceProduct, quantity: int):
        if quantity <= 0:
            CartService.remove_item(cart, product)
            return
        CommerceCartItem.objects.filter(cart=cart, product=product).update(quantity=quantity)

    @staticmethod
    def remove_item(cart: CommerceCart, product: CommerceProduct):
        CommerceCartItem.objects.filter(cart=cart, product=product).delete()

    @staticmethod
    def clear(cart: CommerceCart):
        cart.items.all().delete()

    @staticmethod
    def get_items(cart: CommerceCart):
        return (
            cart.items
            .select_related("product__repuesto", "product__category")
            .prefetch_related("product__images")
            .all()
        )

    @staticmethod
    def total(cart: CommerceCart):
        return sum(item.subtotal for item in CartService.get_items(cart))

    @staticmethod
    def item_count(cart: CommerceCart) -> int:
        result = cart.items.aggregate(n=Sum("quantity"))["n"]
        return result or 0
