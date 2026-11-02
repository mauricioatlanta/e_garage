"""
CommercePaidConsumer — procesa commerce.order.paid.

Qué hace:
  1. Encuentra el Documento PTS BORRADOR creado por CommerceOrderConsumer.
  2. Cambia estado → EMITIDO y marca el documento como pagado.
  3. El pre_save signal (signals_inventory.py) dispara InventoryService,
     que es el único camino autorizado para mover stock y crear
     MovimientoInventario (ADR-004).
  4. Registra ProcessedEvent para idempotencia.

Fronteras respetadas:
  - Importa modelos ERP para leer y cambiar estado (Documento, Empresa).
  - NO crea MovimientoInventario directamente. Commerce no mueve inventario.
  - NO modifica Repuesto.cantidad_stock directamente.
  - No emite nuevos OutboxEvents.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db import transaction

if TYPE_CHECKING:
    from runtime.models.outbox_event import OutboxEvent

logger = logging.getLogger(__name__)

EVENT_TYPE = "commerce.order.paid"
CONSUMER_NAME = "commerce_paid_consumer"


class CommercePaidConsumer:

    event_type = EVENT_TYPE

    @transaction.atomic
    def handle(self, event: "OutboxEvent") -> None:
        from runtime.models.processed_event import ProcessedEvent

        # ── 1. Idempotencia ──────────────────────────────────────────
        if ProcessedEvent.objects.filter(event_id=event.event_id).exists():
            logger.info("Event %s already processed — skipping.", event.event_id)
            return

        payload = event.payload
        self._validate_payload(payload)

        empresa = self._resolve_empresa(payload["empresa_id"])
        doc = self._resolve_documento(payload["commerce_order_id"], empresa)

        # ── 2. Emitir y marcar pagado ────────────────────────────────
        # doc.save() dispara pre_save → signals_inventory → InventoryService.
        # El ERP es el único responsable de mover stock. Este consumer no
        # toca MovimientoInventario ni Repuesto.cantidad_stock.
        self._emit_and_mark_paid(doc)

        # ── 3. Registrar correlación ─────────────────────────────────
        ProcessedEvent.objects.create(
            event_id=event.event_id,
            consumer=CONSUMER_NAME,
            result_type="documento",
            result_id=str(doc.pk),
        )

        logger.info(
            "commerce.order.paid processed: event=%s → documento=%s EMITIDO",
            event.event_id, doc.pk,
        )

    # ── Helpers privados ─────────────────────────────────────────────

    def _validate_payload(self, payload: dict) -> None:
        for field in ["empresa_id", "commerce_order_id"]:
            if field not in payload:
                raise ValueError(f"Payload inválido, falta campo: {field!r}")

    def _resolve_empresa(self, empresa_id: int):
        from taller.models.empresa import Empresa
        try:
            return Empresa.objects.get(pk=empresa_id)
        except Empresa.DoesNotExist:
            raise ValueError(f"Empresa pk={empresa_id} no existe")

    def _resolve_documento(self, commerce_order_id: int, empresa):
        """
        Localiza el Documento PTS BORRADOR creado por CommerceOrderConsumer
        para este pedido, usando la correlación outbox_event → ProcessedEvent.
        """
        from runtime.models.outbox_event import OutboxEvent
        from runtime.models.processed_event import ProcessedEvent
        from taller.models.documento import Documento

        submitted_event = OutboxEvent.objects.filter(
            aggregate_type="commerce_order",
            aggregate_id=str(commerce_order_id),
            event_type="commerce.order.submitted",
        ).first()

        if submitted_event is None:
            raise ValueError(
                f"No se encontró OutboxEvent commerce.order.submitted "
                f"para el pedido commerce_order_id={commerce_order_id}."
            )

        processed = ProcessedEvent.objects.filter(
            event_id=submitted_event.event_id,
            consumer="commerce_order_consumer",
        ).first()

        if processed is None:
            raise ValueError(
                f"El evento commerce.order.submitted (id={submitted_event.event_id}) "
                f"aún no fue procesado. El Documento PTS BORRADOR no existe todavía."
            )

        try:
            return Documento.objects.get(pk=int(processed.result_id), empresa=empresa)
        except Documento.DoesNotExist:
            raise ValueError(
                f"Documento pk={processed.result_id} no encontrado "
                f"para empresa {empresa.pk}."
            )

    def _emit_and_mark_paid(self, doc) -> None:
        if doc.estado == "EMITIDO":
            return  # idempotente: la señal no volverá a descontar stock
        if doc.estado != "BORRADOR":
            raise ValueError(
                f"Documento pk={doc.pk} en estado inesperado: {doc.estado!r}. "
                "Solo se puede emitir un documento en estado BORRADOR."
            )
        doc.estado = "EMITIDO"
        doc.estado_pago = "PAGADO"
        doc.pagado = True
        doc.save(update_fields=["estado", "estado_pago", "pagado"])
