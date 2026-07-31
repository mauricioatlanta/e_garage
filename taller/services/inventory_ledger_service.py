import hashlib
import json
from decimal import Decimal

from django.core.exceptions import ValidationError


class InventoryLedgerService:
    HASH_VERSION = "INV_LEDGER_V1"

    @classmethod
    def build_idempotency_key(
        cls,
        *,
        empresa_id,
        tipo,
        origen_stock,
        repuesto_id,
        pieza_desarme_id,
        documento_id,
        linea_repuesto_id,
        cantidad_delta,
        operation_version=1,
        operation_id=None,
    ):
        """SHA-256 determinístico para idempotencia del ledger de inventario.

        operation_id: UUID de operación (solo para TipoMovimiento.EDICION).
        Si es None no se incluye en el payload, preservando compatibilidad con
        claves EMISION/ANULACION ya existentes en la DB.
        """
        payload = {
            "v": cls.HASH_VERSION,
            "empresa_id": empresa_id,
            "tipo": tipo,
            "origen_stock": origen_stock,
            "repuesto_id": repuesto_id,
            "pieza_desarme_id": pieza_desarme_id,
            "documento_id": documento_id,
            "linea_repuesto_id": linea_repuesto_id,
            "cantidad_delta": (
                str(cantidad_delta) if isinstance(cantidad_delta, Decimal) else int(cantidad_delta)
            ),
            "operation_version": operation_version,
        }
        if operation_id is not None:
            payload["operation_id"] = str(operation_id)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def record_stock_movement(
        cls,
        *,
        empresa,
        tipo,
        repuesto,
        documento,
        linea_repuesto,
        cantidad_delta,
        saldo_resultante,
        costo_unitario=None,
        created_by=None,
        metadata=None,
    ):
        """
        Registra un movimiento STOCK_BODEGA en el ledger de inventario.

        Idempotente: si ya existe un registro con la misma clave y los campos
        críticos coinciden, lo devuelve sin crear duplicado.

        Returns:
            tuple[MovimientoInventario, bool]: (instancia, creado)

        Raises:
            ValidationError: si existe un registro con la misma clave pero
                campos críticos distintos (conflicto de idempotencia).
        """
        from taller.models.movimiento_inventario import MovimientoInventario

        idempotency_key = cls.build_idempotency_key(
            empresa_id=empresa.pk,
            tipo=tipo,
            origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
            repuesto_id=repuesto.pk,
            pieza_desarme_id=None,
            documento_id=documento.pk,
            linea_repuesto_id=linea_repuesto.pk,
            cantidad_delta=cantidad_delta,
        )

        existing = MovimientoInventario.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            if (
                existing.empresa_id != empresa.pk
                or existing.tipo != tipo
                or existing.repuesto_id != repuesto.pk
                or existing.cantidad_delta != cantidad_delta
            ):
                raise ValidationError(
                    f"Conflicto de idempotencia para key={idempotency_key}: "
                    "campos críticos difieren del registro existente."
                )
            return existing, False

        movimiento = MovimientoInventario.objects.create(
            empresa=empresa,
            tipo=tipo,
            origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
            repuesto=repuesto,
            documento=documento,
            linea_repuesto=linea_repuesto,
            cantidad_delta=cantidad_delta,
            saldo_resultante=saldo_resultante,
            costo_unitario=costo_unitario,
            idempotency_key=idempotency_key,
            created_by=created_by,
            metadata=metadata or {},
        )
        return movimiento, True
