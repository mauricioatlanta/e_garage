"""
OutboxService — interfaz para publicar y procesar eventos del outbox.

Uso desde un aggregate (dentro de transaction.atomic):
    OutboxService.enqueue(
        event_id=uuid.uuid4(),
        aggregate_type="commerce_order",
        aggregate_id=str(order.pk),
        event_type="commerce.order.submitted",
        payload={...},
    )

El proceso de dispatch vive en process_outbox.py.
"""
from __future__ import annotations

import importlib
import logging
import uuid as _uuid
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

if TYPE_CHECKING:
    from runtime.models.outbox_event import OutboxEvent

logger = logging.getLogger(__name__)

# Mapa event_type → import path del consumer
_CONSUMER_REGISTRY: dict[str, str] = {
    "commerce.order.submitted": "runtime.consumers.commerce_order_consumer.CommerceOrderConsumer",
    "commerce.order.paid": "runtime.consumers.commerce_paid_consumer.CommercePaidConsumer",
}

MAX_ATTEMPTS = 3


class OutboxService:

    @staticmethod
    def enqueue(
        *,
        event_id: _uuid.UUID,
        aggregate_type: str,
        aggregate_id: str,
        event_type: str,
        payload: dict,
    ) -> "OutboxEvent":
        """
        Persiste un evento en el outbox.
        Debe llamarse dentro de una transaction.atomic() activa para garantizar
        que el evento y el aggregate se confirman o revierten juntos.
        """
        from runtime.models.outbox_event import OutboxEvent

        return OutboxEvent.objects.create(
            event_id=event_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
        )

    @staticmethod
    def process_pending(event_type: str | None = None, limit: int = 100) -> dict:
        """
        Lee eventos PENDING (o FAILED con intentos < MAX_ATTEMPTS), los marca
        PROCESSING, invoca al consumer y los marca PROCESSED o FAILED.

        Returns un dict con contadores: processed, failed, skipped.
        """
        from runtime.models.outbox_event import OutboxEvent

        qs = OutboxEvent.objects.filter(
            status__in=[OutboxEvent.PENDING, OutboxEvent.FAILED],
            attempts__lt=MAX_ATTEMPTS,
        ).order_by("created_at")

        if event_type:
            qs = qs.filter(event_type=event_type)

        qs = qs[:limit]

        stats = {"processed": 0, "failed": 0, "skipped": 0}

        for event in qs:
            consumer_path = _CONSUMER_REGISTRY.get(event.event_type)
            if not consumer_path:
                logger.warning("No consumer for event_type=%s", event.event_type)
                stats["skipped"] += 1
                continue

            # Marcar PROCESSING
            OutboxEvent.objects.filter(pk=event.pk).update(
                status=OutboxEvent.PROCESSING,
                attempts=event.attempts + 1,
            )
            event.refresh_from_db()

            try:
                module_path, class_name = consumer_path.rsplit(".", 1)
                module = importlib.import_module(module_path)
                consumer_cls = getattr(module, class_name)
                consumer = consumer_cls()
                consumer.handle(event)

                OutboxEvent.objects.filter(pk=event.pk).update(
                    status=OutboxEvent.PROCESSED,
                    processed_at=timezone.now(),
                    last_error="",
                )
                stats["processed"] += 1
                logger.info("Processed event %s (%s)", event.event_id, event.event_type)

            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {exc}"
                new_status = (
                    OutboxEvent.FAILED
                    if event.attempts >= MAX_ATTEMPTS
                    else OutboxEvent.PENDING
                )
                OutboxEvent.objects.filter(pk=event.pk).update(
                    status=new_status,
                    last_error=error_msg,
                )
                stats["failed"] += 1
                logger.error(
                    "Failed event %s (%s): %s",
                    event.event_id, event.event_type, error_msg,
                )

        return stats
