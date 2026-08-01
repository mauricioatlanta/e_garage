# ADR-004 — Commerce ↔ ERP solo via eventos (dominio de pagos)

**Estado:** ACEPTADO  
**Fecha:** 2026-07-31  
**Autor:** Mauricio Alvarado  
**Aplica a:** Todo código bajo `commerce/payments/`, `commerce/services/payment_service.py`, `runtime/consumers/commerce_paid_consumer.py`

---

## Contexto

El Commerce Engine y el ERP (taller/) son dominios independientes. Este principio ya está establecido para el catálogo (ADR-001: CommerceCatalogGateway). Debe aplicarse igualmente —y con más rigor— al dominio de pagos.

La tentación al implementar el pago es conectar directamente: cuando WebPay confirma, crear el Documento. Es la ruta más corta. También es la que destruye el desacople.

## Decisión

**Commerce y el ERP nunca se llaman directamente. Toda comunicación ocurre exclusivamente a través del Outbox y el Contract Runtime.**

El flujo autorizado es:

```
PaymentGateway (I/O externo)
  ↓
CommercePaymentService (Commerce)
  ↓ si pago confirmado
OutboxService.enqueue("commerce.order.paid")
  ↓
process_outbox (Runtime)
  ↓
CommercePaidConsumer
  ↓
Documento EMITIDO + MovimientoInventario OUT (ERP)
```

El flujo prohibido es:

```
PaymentGateway
  ↓
[cualquier import de taller.models]   ← VIOLACIÓN
  ↓
Documento                             ← PROHIBIDO
```

## Por qué importa

**Razón 1 — Testabilidad:**  
`CommercePaymentService` se puede testear completamente con un gateway mockeado y un `OutboxService` mockeado. Sin fixtures ERP. Sin base de datos de documentos. La suite de Commerce corre en aislamiento.

**Razón 2 — Resiliencia:**  
Si el ERP falla procesando `commerce.order.paid`, el pago ya fue confirmado y el evento está en el Outbox. El consumer reintenta. No hay ventana de inconsistencia entre "Transbank dijo sí" y "el Documento no se creó".

**Razón 3 — Extensibilidad:**  
En el futuro, `commerce.order.paid` puede tener múltiples consumers: uno crea el Documento, otro envía el email de confirmación, otro actualiza métricas. Ninguno requiere cambios en el `CommercePaymentService`.

**Razón 4 — Boundary explícita:**  
La boundary entre Commerce y ERP está en el Outbox. Cruzarla directamente (desde `payment_service.py`) es equivalente a hacer una llamada HTTP a otro microservicio sin pasar por la API. Funciona hoy; rompe la arquitectura mañana.

## Regla de código

En los archivos `commerce/payments/*.py` y `commerce/services/payment_service.py`, está **prohibido**:

```python
from taller.models import Documento
from taller.models import MovimientoInventario
from taller.models import LineaRepuesto
from taller.documentos import *
from taller.services import *
```

El único export permitido hacia el ERP es:

```python
from runtime.services.outbox_service import OutboxService
OutboxService.enqueue(event_type="commerce.order.paid", ...)
```

## Contrato del evento `commerce.order.paid`

```json
{
  "event_id": "uuid4",
  "occurred_at": "ISO-8601",
  "schema_version": "1.0.0",
  "empresa_id": 42,
  "commerce_order_id": 101,
  "order_number": "ORD-42-ABC12345",
  "payment_method": "webpay",
  "gateway_ref": "123456",
  "paid_at": "ISO-8601",
  "amount": 49990,
  "currency": "CLP",
  "buyer": {
    "full_name": "Juan Pérez",
    "email": "juan@example.com",
    "phone": "+56912345678"
  },
  "items": [
    {
      "commerce_order_item_id": 55,
      "sku": "CAT-001",
      "name": "Catalizador Toyota Yaris 2018",
      "quantity": 1,
      "unit_price": "49990",
      "line_total": "49990"
    }
  ],
  "total": "49990"
}
```

Este contrato es **estable**. El `CommercePaidConsumer` depende de él. Cualquier campo nuevo es aditivo (retrocompatible). Nunca eliminar ni renombrar campos existentes sin bump de `schema_version`.

## Responsabilidades por capa

| Capa | Responsabilidad | Prohibido |
|------|----------------|-----------|
| `PaymentGateway` | I/O con el proveedor (Transbank, etc.). Retorna `PaymentResult`. | Tocar modelos Django |
| `CommercePaymentService` | Orquesta intento → resultado → evento. Actualiza `CommerceOrder` y `PaymentAttempt`. | Importar modelos ERP |
| `OutboxService` | Persiste el evento en la misma transacción. | — |
| `CommercePaidConsumer` | Procesa `commerce.order.paid`. Crea Documento EMITIDO + stock OUT. | Importar modelos Commerce |
| `process_outbox` | Despacha eventos a consumers registrados. | Lógica de negocio |

## Idempotencia

`CommercePaidConsumer` debe ser idempotente vía `ProcessedEvent`, igual que `CommerceOrderConsumer`. Si el mismo evento llega dos veces (retry del Outbox), el Documento no se duplica y el stock no se descuenta dos veces.

Mecanismo sugerido para el stock: constraint único en `MovimientoInventario(commerce_order_item_id)`. Si ya existe, la operación es silenciosa (ya procesado).

## Relación con otras ADRs

- ADR-000: Este ADR es la aplicación de "plataforma, no desarrollo a medida" al dominio de pagos.
- ADR-001 (CommerceCatalogGateway): El mismo principio de aislamiento, aplicado al catálogo. Este ADR extiende ese principio al flujo de pago.
- ADR-007 (identidad guest): El `CommercePaidConsumer` usará el mismo patrón find-or-create que el `CommerceOrderConsumer`.
