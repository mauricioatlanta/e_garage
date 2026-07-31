import hashlib
import json
from decimal import Decimal


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
    ):
        """SHA-256 determinístico para idempotencia del ledger de inventario."""
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
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
