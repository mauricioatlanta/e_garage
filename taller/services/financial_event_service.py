from decimal import Decimal

from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.vehiculo_financial import VehicleFinancialEvent


class FinancialEventService:
    """Servicio para crear y sincronizar eventos financieros a partir de ventas de desarme."""

    @classmethod
    def _event_description(cls, linea: LineaRepuesto) -> str:
        return f"Venta de pieza {linea.codigo} - {linea.nombre} x{linea.cantidad}"

    @classmethod
    def _event_amount(cls, linea: LineaRepuesto) -> Decimal:
        return Decimal(linea.precio_unitario or 0) * Decimal(linea.cantidad or 0)

    @classmethod
    def _compute_event_hash(cls, linea: LineaRepuesto) -> str:
        """
        Fingerprint inmutable del evento financiero.

        IMPORTANTE:
        - Debe cambiar si cambia cualquier aspecto económico relevante.
        - Debe ser deterministicamente reproducible.
        - Se usa para idempotencia append-only.
        """

        pieza_id = getattr(linea, "pieza_desarme_id", "NO_PIEZA")

        payload = [
            "FIN_EVENT_V1",
            str(linea.id),
            str(linea.documento_id),
            str(pieza_id),
            str(linea.cantidad or 0),
            str(linea.precio_unitario or 0),
            str(linea.descuento or 0),
            str(linea.subtotal or 0),
        ]

        return "|".join(payload)

    @classmethod
    def sync_event_from_linea_repuesto(cls, linea: LineaRepuesto):
        """Crea o actualiza un evento financiero para una línea de repuesto de desarme."""
        if linea.origen_repuesto != ORIGEN_DESARME:
            return None

        documento = getattr(linea, "documento", None)
        if not documento or documento.estado != "EMITIDO":
            return None

        pieza = getattr(linea, "pieza_desarme", None)
        if not pieza:
            return None
        vehiculo_obj = getattr(pieza, "vehiculo", None)
        if not vehiculo_obj:
            return None

        monto = cls._event_amount(linea)
        descripcion = cls._event_description(linea)
        event_hash = cls._compute_event_hash(linea)
        event_type = VehicleFinancialEvent.EVENT_TYPE_VENTA

        existing = VehicleFinancialEvent.objects.filter(
            event_hash=event_hash
        ).first()

        if existing:
            return existing

        last_version = (
            VehicleFinancialEvent.objects.filter(
                linea_repuesto=linea,
                event_type=event_type,
            )
            .order_by("-event_version")
            .values_list("event_version", flat=True)
            .first()
            or 0
        )

        event = VehicleFinancialEvent.objects.create(
            vehiculo=vehiculo_obj,
            empresa=documento.empresa,
            tipo=event_type,
            monto=monto,
            descripcion=descripcion,
            documento=documento,
            pieza_desarme=pieza,
            linea_repuesto=linea,
            event_hash=event_hash,
            event_version=last_version + 1,
            event_type=event_type,
        )

        return event

    @classmethod
    def create_purchase_event(cls, vehiculo, empresa, monto, descripcion):
        """Registra un evento de compra de vehículo o costo asociado."""
        return VehicleFinancialEvent.objects.create(
            vehiculo=vehiculo,
            empresa=empresa,
            tipo=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            event_type=VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            monto=Decimal(monto or 0),
            descripcion=descripcion,
        )

    @classmethod
    def create_cost_event(cls, vehiculo, empresa, monto, descripcion):
        """Registra un evento de costo operativo o de desarme."""
        return VehicleFinancialEvent.objects.create(
            vehiculo=vehiculo,
            empresa=empresa,
            tipo=VehicleFinancialEvent.EVENT_TYPE_COSTO,
            event_type=VehicleFinancialEvent.EVENT_TYPE_COSTO,
            monto=Decimal(monto or 0),
            descripcion=descripcion,
        )

    @classmethod
    def remove_event_for_linea_repuesto(cls, linea: LineaRepuesto):
        """Elimina el evento financiero asociado a una línea de desarme si existe."""
        if linea.origen_repuesto != ORIGEN_DESARME:
            return 0
        deleted, _ = VehicleFinancialEvent.objects.filter(
            linea_repuesto_id=linea.id,
            event_type=VehicleFinancialEvent.EVENT_TYPE_VENTA,
        ).delete()
        return deleted

    @classmethod
    def sync_events_for_documento(cls, documento):
        """Sincroniza los eventos financieros para todas las líneas de desarme de un documento."""
        if documento.estado != "EMITIDO":
            return []
        events = []
        for linea in documento.lineas_repuesto.filter(origen_repuesto=ORIGEN_DESARME).select_related(
            "pieza_desarme", "documento"
        ):
            event = cls.sync_event_from_linea_repuesto(linea)
            if event:
                events.append(event)
        return events
