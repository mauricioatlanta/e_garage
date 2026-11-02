from decimal import Decimal

from django.db import IntegrityError

from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.vehiculo_financial import VehicleFinancialEvent


class FinancialEventService:
    """Servicio para crear y sincronizar eventos financieros a partir de ventas de desarme."""

    @classmethod
    def _normalize_number(cls, value):
        return format(Decimal(value or 0), "f")

    @classmethod
    def _normalize_text(cls, value):
        if value is None:
            return ""
        return str(value).strip()

    @classmethod
    def _event_description(cls, linea: LineaRepuesto) -> str:
        return f"Venta de pieza {getattr(linea, 'codigo', '')} - {getattr(linea, 'nombre', '')} x{getattr(linea, 'cantidad', '')}"

    @classmethod
    def _event_amount(cls, linea: LineaRepuesto) -> Decimal:
        return Decimal(getattr(linea, 'precio_unitario', 0) or 0) * Decimal(getattr(linea, 'cantidad', 0) or 0)

    @classmethod
    def _compute_sale_hash(cls, linea: LineaRepuesto) -> str:
        pieza_id = getattr(linea, "pieza_desarme_id", "NO_PIEZA")
        payload = [
            "FIN_EVENT_V1",
            VehicleFinancialEvent.EVENT_TYPE_VENTA,
            str(linea.id),
            str(linea.documento_id),
            str(pieza_id),
            cls._normalize_number(linea.cantidad),
            cls._normalize_number(linea.precio_unitario),
            cls._normalize_number(linea.descuento),
            cls._normalize_number(linea.subtotal),
        ]
        return "|".join(payload)

    @classmethod
    def _compute_purchase_hash(cls, vehiculo, empresa, monto, descripcion) -> str:
        payload = [
            "FIN_EVENT_V1",
            VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            str(getattr(vehiculo, "id", "NO_VEHICULO")),
            str(getattr(empresa, "id", "NO_EMPRESA")),
            cls._normalize_number(monto),
            cls._normalize_text(descripcion),
        ]
        return "|".join(payload)

    @classmethod
    def _compute_cost_hash(cls, vehiculo, empresa, monto, descripcion) -> str:
        payload = [
            "FIN_EVENT_V1",
            VehicleFinancialEvent.EVENT_TYPE_COSTO,
            str(getattr(vehiculo, "id", "NO_VEHICULO")),
            str(getattr(empresa, "id", "NO_EMPRESA")),
            cls._normalize_number(monto),
            cls._normalize_text(descripcion),
        ]
        return "|".join(payload)

    @classmethod
    def _next_event_version(cls, vehiculo, event_type):
        return (
            VehicleFinancialEvent.objects.filter(
                vehiculo_desarme=vehiculo,
                event_type=event_type,
            )
            .order_by("-event_version")
            .values_list("event_version", flat=True)
            .first()
            or 0
        ) + 1

    @classmethod
    def _create_event(
        cls,
        vehiculo,
        empresa,
        event_type,
        monto,
        descripcion,
        event_hash,
        documento=None,
        pieza_desarme=None,
        linea_repuesto=None,
    ):
        existing = VehicleFinancialEvent.objects.filter(event_hash=event_hash).first()
        if existing:
            return existing

        event = VehicleFinancialEvent(
            vehiculo_desarme=vehiculo,
            empresa=empresa,
            tipo=event_type,
            event_type=event_type,
            monto=Decimal(monto or 0),
            descripcion=descripcion,
            documento=documento,
            pieza_desarme=pieza_desarme,
            linea_repuesto=linea_repuesto,
            event_hash=event_hash,
            event_version=cls._next_event_version(vehiculo, event_type),
        )
        try:
            event.save()
            return event
        except IntegrityError:
            return VehicleFinancialEvent.objects.filter(event_hash=event_hash).first()

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
        vehiculo_obj = getattr(pieza, "vehiculo_desarme", None)
        if not vehiculo_obj:
            return None

        descripcion = cls._event_description(linea)
        event_hash = cls._compute_sale_hash(linea)
        event_type = VehicleFinancialEvent.EVENT_TYPE_VENTA

        return cls._create_event(
            vehiculo_obj,
            documento.empresa,
            event_type,
            cls._event_amount(linea),
            descripcion,
            event_hash,
            documento=documento,
            pieza_desarme=pieza,
            linea_repuesto=linea,
        )

    @classmethod
    def create_purchase_event(cls, vehiculo, empresa, monto, descripcion):
        """Registra un evento de compra de vehículo o costo asociado."""
        event_hash = cls._compute_purchase_hash(vehiculo, empresa, monto, descripcion)
        return cls._create_event(
            vehiculo,
            empresa,
            VehicleFinancialEvent.EVENT_TYPE_COMPRA,
            monto,
            descripcion,
            event_hash,
        )

    @classmethod
    def create_cost_event(cls, vehiculo, empresa, monto, descripcion):
        """Registra un evento de costo operativo o de desarme."""
        event_hash = cls._compute_cost_hash(vehiculo, empresa, monto, descripcion)
        return cls._create_event(
            vehiculo,
            empresa,
            VehicleFinancialEvent.EVENT_TYPE_COSTO,
            monto,
            descripcion,
            event_hash,
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
