import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from commerce.models.cart import CommerceCart
from commerce.models.order import CommerceOrder, CommerceOrderItem
from commerce.services.cart_service import CartService


def _generate_order_number(empresa_id: int) -> str:
    short = uuid.uuid4().hex[:8].upper()
    return f"ORD-{empresa_id}-{short}"


def _build_outbox_payload(order: CommerceOrder, items: list) -> dict:
    event_id = uuid.uuid4()
    return event_id, {
        "event_id": str(event_id),
        "occurred_at": timezone.now().isoformat(),
        "schema_version": "1.0.0",
        "empresa_id": order.empresa_id,
        "commerce_order_id": order.pk,
        "order_number": order.order_number,
        "buyer": {
            "full_name": order.customer_name,
            "email": order.customer_email,
            "phone": order.customer_phone,
        },
        "items": [
            {
                "commerce_order_item_id": item.pk,
                "product_reference": item.product.slug if item.product_id else "",
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "line_total": str(item.subtotal),
                "repuesto_id": item.product.repuesto_id if item.product_id else None,
            }
            for item in items
        ],
        "subtotal": str(order.total),
        "tax_total": "0.00",
        "total": str(order.total),
        "currency": "CLP",
    }


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_from_cart(cart: CommerceCart, customer_data: dict) -> CommerceOrder:
        """
        Crea un CommerceOrder desde el carrito activo.

        Congela SKU, nombre y precio en cada CommerceOrderItem.
        Publica un OutboxEvent en la misma transacción para que el
        Contract Runtime pueda crear el Documento ERP PTS BORRADOR.
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

        order_items = CommerceOrderItem.objects.bulk_create([
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

        # Publicar evento al outbox en la misma transacción atómica.
        # Si esto falla, el Order y las líneas hacen rollback también.
        from runtime.services.outbox_service import OutboxService
        event_id, payload = _build_outbox_payload(order, order_items)
        OutboxService.enqueue(
            event_id=event_id,
            aggregate_type="commerce_order",
            aggregate_id=str(order.pk),
            event_type="commerce.order.submitted",
            payload=payload,
        )

        return order
