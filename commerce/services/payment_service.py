"""
CommercePaymentService — orquesta el ciclo de vida del pago de un CommerceOrder.

Invariante: este módulo nunca importa modelos ERP (taller.*).
Toda comunicación con el ERP es exclusivamente mediante OutboxService (ADR-004).
"""
from __future__ import annotations

import logging
import uuid

from django.db import transaction
from django.utils import timezone

from commerce.models.order import CommerceOrder
from commerce.models.payment import CommercePaymentTransaction, PaymentAttempt
from commerce.payments import PaymentConfirmation, PaymentGateway, PaymentInitiation

logger = logging.getLogger(__name__)


class PaymentAlreadyAuthorizedError(Exception):
    """El pedido ya tiene un pago autorizado. No se puede procesar un segundo pago."""


class PaymentAttemptNotFoundError(Exception):
    """No existe PaymentAttempt con el gateway_token indicado para este pedido."""


class CommercePaymentService:

    @staticmethod
    def initiate(
        order: CommerceOrder,
        gateway_key: str,
        return_url: str,
    ) -> PaymentInitiation:
        """
        Inicia un pago contra el gateway indicado.

        Puede llamarse múltiples veces en el mismo pedido — cada llamada
        crea un PaymentAttempt independiente (soporta reintentos).
        Lanza PaymentAlreadyAuthorizedError si el pedido ya está PAID.
        """
        if order.payment_status == CommerceOrder.PAYMENT_PAID:
            raise PaymentAlreadyAuthorizedError(
                f"El pedido {order.order_number} ya está pagado."
            )

        gateway = PaymentGateway.resolve(gateway_key)
        initiation = gateway.initiate(
            buy_order=order.order_number,
            session_id=order.session_key or order.order_number,
            amount=int(order.total),
            return_url=return_url,
        )

        with transaction.atomic():
            PaymentAttempt.objects.create(
                empresa=order.empresa,
                order=order,
                gateway=gateway_key,
                status=PaymentAttempt.INITIATED,
                amount=int(order.total),
                gateway_token=initiation.gateway_token,
            )
            CommerceOrder.objects.filter(pk=order.pk).update(
                payment_status=CommerceOrder.PAYMENT_INITIATED,
                payment_method=gateway_key,
            )

        order.payment_status = CommerceOrder.PAYMENT_INITIATED
        order.payment_method = gateway_key
        return initiation

    @staticmethod
    def confirm(order: CommerceOrder, gateway_token: str) -> bool:
        """
        Confirma el resultado de un pago ya iniciado.

        Llama a gateway.confirm() fuera de la transacción (I/O externo).
        Todos los cambios en BD se aplican dentro de transaction.atomic():
        si cualquiera falla, el bloque completo hace rollback.

        Returns True si el pago fue autorizado, False si fue rechazado.
        Lanza PaymentAlreadyAuthorizedError si el pedido ya está PAID (idempotencia).
        Lanza PaymentAttemptNotFoundError si no existe intento con ese token.
        """
        if order.payment_status == CommerceOrder.PAYMENT_PAID:
            raise PaymentAlreadyAuthorizedError(
                f"El pedido {order.order_number} ya está pagado."
            )

        attempt = PaymentAttempt.objects.filter(
            order=order, gateway_token=gateway_token
        ).first()
        if attempt is None:
            raise PaymentAttemptNotFoundError(
                f"No se encontró PaymentAttempt para token: {gateway_token!r}"
            )

        gateway = PaymentGateway.resolve(attempt.gateway)
        confirmation = gateway.confirm(gateway_token)
        now = timezone.now()

        with transaction.atomic():
            if confirmation.success:
                _apply_success(order, attempt, confirmation, now)
            else:
                _apply_failure(order, attempt, confirmation, now)

        return confirmation.success


# ── Helpers privados ───────────────────────────────────────────────────────────

def _apply_success(
    order: CommerceOrder,
    attempt: PaymentAttempt,
    confirmation: PaymentConfirmation,
    now,
) -> None:
    attempt.status = PaymentAttempt.AUTHORIZED
    attempt.gateway_ref = confirmation.gateway_ref
    attempt.raw_status = "AUTHORIZED"
    attempt.completed_at = now
    attempt.save(update_fields=["status", "gateway_ref", "raw_status", "completed_at"])

    CommercePaymentTransaction.objects.create(
        empresa=order.empresa,
        order=order,
        gateway=attempt.gateway,
        gateway_token=attempt.gateway_token,
        gateway_ref=confirmation.gateway_ref,
        status=CommercePaymentTransaction.AUTHORIZED,
        amount=confirmation.amount,
        card_last4=confirmation.card_last4,
        raw_response=confirmation.raw_response,
        confirmed_at=now,
    )

    CommerceOrder.objects.filter(pk=order.pk).update(
        payment_status=CommerceOrder.PAYMENT_PAID,
        payment_gateway_ref=confirmation.gateway_ref,
        paid_at=now,
    )
    order.payment_status = CommerceOrder.PAYMENT_PAID
    order.payment_gateway_ref = confirmation.gateway_ref
    order.paid_at = now

    _enqueue_event(
        event_type="commerce.order.paid",
        order=order,
        extra={
            "gateway": attempt.gateway,
            "gateway_ref": confirmation.gateway_ref,
            "amount": confirmation.amount,
            "currency": "CLP",
            "card_last4": confirmation.card_last4,
            "paid_at": now.isoformat(),
            "items": _collect_item_snapshots(order),
        },
    )


def _apply_failure(
    order: CommerceOrder,
    attempt: PaymentAttempt,
    confirmation: PaymentConfirmation,
    now,
) -> None:
    error_msg = (
        confirmation.raw_response.get("error_message")
        or f"response_code={confirmation.raw_response.get('response_code', 'unknown')}"
    )
    attempt.status = PaymentAttempt.FAILED
    attempt.raw_status = str(confirmation.raw_response.get("status") or "FAILED")
    attempt.error_message = error_msg
    attempt.completed_at = now
    attempt.save(update_fields=["status", "raw_status", "error_message", "completed_at"])

    # order.payment_status permanece en PAYMENT_INITIATED: el cliente puede reintentar
    # vía una nueva llamada a initiate(), que creará un nuevo PaymentAttempt.

    _enqueue_event(
        event_type="commerce.order.payment_failed",
        order=order,
        extra={
            "attempt_number": attempt.attempt_number,
            "gateway": attempt.gateway,
            "error_message": error_msg,
        },
    )


def _collect_item_snapshots(order: CommerceOrder) -> list:
    return [
        {
            "commerce_order_item_id": item.pk,
            "sku": item.sku,
            "name": item.name,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
            "repuesto_id": item.product.repuesto_id if item.product_id else None,
        }
        for item in order.items.all()
    ]


def _enqueue_event(event_type: str, order: CommerceOrder, extra: dict) -> None:
    from runtime.services.outbox_service import OutboxService

    event_id = uuid.uuid4()
    OutboxService.enqueue(
        event_id=event_id,
        aggregate_type="commerce_order",
        aggregate_id=str(order.pk),
        event_type=event_type,
        payload={
            "event_id": str(event_id),
            "occurred_at": timezone.now().isoformat(),
            "schema_version": "1.0.0",
            "empresa_id": order.empresa_id,
            "commerce_order_id": order.pk,
            "order_number": order.order_number,
            **extra,
        },
    )
