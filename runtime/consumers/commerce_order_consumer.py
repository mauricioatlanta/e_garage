"""
CommerceOrderConsumer — procesa commerce.order.submitted y crea Documento PTS BORRADOR.

Fronteras respetadas:
- Puede importar modelos ERP (Documento, LineaRepuesto, Cliente, DocumentSequence).
- No importa modelos Commerce directamente (recibe solo el payload contractual).
- No emite el Documento.
- No descuenta stock ni crea MovimientoInventario.
"""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from django.db import transaction

if TYPE_CHECKING:
    from runtime.models.outbox_event import OutboxEvent

logger = logging.getLogger(__name__)

EVENT_TYPE = "commerce.order.submitted"
CONSUMER_NAME = "commerce_order_consumer"


class CommerceOrderConsumer:
    """
    Consumer idempotente para commerce.order.submitted.

    Por cada evento:
    1. Verifica idempotencia via ProcessedEvent.
    2. Resuelve o crea un Cliente guest en la Empresa.
    3. Crea Documento tipo PTS en estado BORRADOR.
    4. Asigna numero via DocumentSequence.next() (select_for_update).
    5. Crea LineaRepuesto con datos congelados del snapshot.
    6. Registra ProcessedEvent con correlación event_id ↔ documento_id.
    """

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
        buyer = payload["buyer"]
        items = payload["items"]
        total = Decimal(str(payload["total"]))

        # ── 2. Cliente guest (find or create por email) ──────────────
        cliente = self._resolve_guest_cliente(empresa, buyer)

        # ── 3. Documento PTS BORRADOR ────────────────────────────────
        doc = self._create_documento(empresa, cliente, total)

        # ── 4. Número de secuencia ───────────────────────────────────
        self._assign_numero(doc, empresa)

        # ── 5. Líneas congeladas ─────────────────────────────────────
        self._create_lineas(doc, items)

        # ── 6. Registrar correlación ─────────────────────────────────
        ProcessedEvent.objects.create(
            event_id=event.event_id,
            consumer=CONSUMER_NAME,
            result_type="documento",
            result_id=str(doc.pk),
        )

        logger.info(
            "commerce.order.submitted processed: event=%s → documento=%s (%s)",
            event.event_id, doc.pk, doc.numero,
        )

    # ── Helpers privados ─────────────────────────────────────────────

    def _validate_payload(self, payload: dict) -> None:
        required = ["empresa_id", "buyer", "items", "total"]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"Payload inválido, faltan campos: {missing}")
        buyer = payload["buyer"]
        if not buyer.get("full_name"):
            raise ValueError("buyer.full_name es requerido")
        if not buyer.get("email"):
            raise ValueError("buyer.email es requerido")
        if not payload["items"]:
            raise ValueError("El evento no contiene líneas de producto")

    def _resolve_empresa(self, empresa_id: int):
        from taller.models.empresa import Empresa
        try:
            return Empresa.objects.get(pk=empresa_id)
        except Empresa.DoesNotExist:
            raise ValueError(f"Empresa pk={empresa_id} no existe")

    def _resolve_guest_cliente(self, empresa, buyer: dict):
        """
        Reglas explícitas de resolución de identidad (ADR-007):
        1. Buscar Cliente de la empresa con el mismo email.
        2. Si no existe, crear un Cliente guest mínimo.
        No mezcla tenants: filtra siempre por empresa.
        """
        from taller.models.clientes import Cliente

        email = buyer["email"].strip().lower()
        full_name = buyer["full_name"].strip()
        phone = buyer.get("phone", "").strip()

        cliente_qs = Cliente.objects.filter(empresa=empresa, email=email)
        if cliente_qs.exists():
            return cliente_qs.first()

        # Separar nombre / apellido de forma simple
        parts = full_name.split(" ", 1)
        nombre = parts[0]
        apellido = parts[1] if len(parts) > 1 else ""

        return Cliente.objects.create(
            empresa=empresa,
            nombre=nombre,
            apellido=apellido or None,
            email=email,
            telefono=phone[:15] if phone else None,
        )

    def _create_documento(self, empresa, cliente, total: Decimal):
        from django.utils import timezone
        from taller.models.documento import Documento

        return Documento.objects.create(
            empresa=empresa,
            cliente=cliente,
            tipo="PTS",
            estado="BORRADOR",
            fecha_emision=timezone.now().date(),
            moneda=self._currency_to_moneda(empresa),
            country=getattr(empresa, "pais", "CL"),
            total=total,
            neto_repuestos=total,
        )

    def _assign_numero(self, doc, empresa) -> None:
        from taller.models.sequence import DocumentSequence

        seq = DocumentSequence.next(empresa, "PTS")
        doc.numero = f"PTS-{seq:06d}"
        doc.save(update_fields=["numero"])

    def _create_lineas(self, doc, items: list) -> None:
        from taller.models.lineas_documento import LineaRepuesto, ORIGEN_EXTERNO

        for item in items:
            try:
                precio = Decimal(str(item["unit_price"]))
            except (InvalidOperation, KeyError):
                raise ValueError(f"unit_price inválido en ítem: {item}")

            cantidad = int(item.get("quantity", 1))
            if cantidad < 1:
                raise ValueError(f"quantity < 1 en ítem: {item}")

            item_id = item.get("commerce_order_item_id", 0)
            codigo = (item.get("sku") or f"COM-{item_id}")[:100]
            nombre = (item.get("name") or f"Producto {item_id}")[:255]

            linea = LineaRepuesto(
                documento=doc,
                codigo=codigo,
                nombre=nombre,
                cantidad=cantidad,
                precio_unitario=precio,
                origen_repuesto=ORIGEN_EXTERNO,
            )
            linea.save()

    def _currency_to_moneda(self, empresa) -> str:
        pais = getattr(empresa, "pais", "CL")
        return {
            "CL": "CLP", "US": "USD", "MX": "MXN",
            "AR": "ARS", "PE": "PEN", "BR": "BRL",
            "UY": "UYU", "VE": "VES",
        }.get(pais, "CLP")
