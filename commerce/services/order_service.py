import uuid

from django.db import transaction

from commerce.models.cart import CommerceCart
from commerce.models.order import CommerceOrder, CommerceOrderItem
from commerce.services.cart_service import CartService


def _generate_order_number(empresa_id: int) -> str:
    short = uuid.uuid4().hex[:8].upper()
    return f"ORD-{empresa_id}-{short}"


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_from_cart(cart: CommerceCart, customer_data: dict) -> CommerceOrder:
        """
        Crea un CommerceOrder desde el carrito activo.

        Congela SKU, nombre y precio en cada CommerceOrderItem.
        Vacía el carrito al terminar.

        customer_data keys:
            name (str, requerido)
            email (str, requerido)
            phone (str, opcional)
            shipping_address (str, opcional)
            notes (str, opcional)
        """
        items = list(CartService.get_items(cart))
        if not items:
            raise ValueError("El carrito está vacío.")

        total = CartService.total(cart)

        order = CommerceOrder.objects.create(
            empresa=cart.empresa,
            order_number=_generate_order_number(cart.empresa_id),
            session_key=cart.session_key,
            customer_name=customer_data["name"],
            customer_email=customer_data["email"],
            customer_phone=customer_data.get("phone", ""),
            shipping_address=customer_data.get("shipping_address", ""),
            notes=customer_data.get("notes", ""),
            total=total,
        )

        CommerceOrderItem.objects.bulk_create([
            CommerceOrderItem(
                order=order,
                product=item.product,
                sku=item.product.part_number or "",
                name=item.product.nombre,
                unit_price=item.product.precio_venta,
                quantity=item.quantity,
            )
            for item in items
        ])

        CartService.clear(cart)
        return order
