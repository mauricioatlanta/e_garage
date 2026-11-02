# ADR-003 — Stock Reservation

- **Estado:** Proposed
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `inventory.stock.v1`, `commerce.order.v1` (futuro)
- **Sustituye:** —
- **Sustituido por:** —
- **Depende de:** ADR-004 (la reserva debe especificar `location_id`, cuya estructura define ADR-004)

---

## 1. Dueño del dato

La **reserva de stock** pertenece a **ERP Core** (`erp.inventory`). Commerce Engine crea el pedido y solicita la reserva; ERP la acepta o rechaza. Ningún subsistema fuera de ERP puede decrementar, reservar ni liberar stock directamente.

---

## 2. Contexto y problema

Cuando un comprador confirma un checkout, hay un intervalo de tiempo entre la confirmación del pedido y la confirmación del pago. Durante ese intervalo, ¿el stock está comprometido para ese pedido o sigue disponible para otros compradores?

La respuesta depende del método de pago:
- **Pago online inmediato**: el pago puede confirmarse en segundos. Reservar por 15 minutos es razonable.
- **Transferencia bancaria**: el pago puede tomar 24–48 horas. Reservar durante ese período evita sobrevender, pero inmoviliza stock.
- **Pago contraentrega / retiro en tienda**: el pago ocurre al momento de la entrega.

Sin una política explícita, Commerce podría vender el mismo producto dos veces o, en el extremo opuesto, inmovilizar stock indefinidamente por pedidos que nunca se pagan.

---

## 3. Capa responsable

| Subsistema | Responsabilidad |
|---|---|
| `commerce.engine` | Crea el pedido; emite `order.placed`; no reserva stock directamente |
| `erp.inventory` | Intenta la reserva al recibir `order.placed`; confirma, rechaza o expira |
| `erp.tax-engine` | Define el medio de pago en el pedido, que determina el TTL de reserva |

---

## 4. Contratos utilizados

- `inventory.stock.v1` — el campo `reserved` por ubicación refleja las reservas activas.
- `commerce.order.v1` (futuro) — el evento `order.placed` dispara el proceso de reserva en ERP.

---

## 5. Opciones consideradas

### Opción A — Reservar al agregar al carrito

Cuando el comprador agrega un producto al carrito, ERP reserva inmediatamente una unidad.

**Ventaja:** el comprador nunca llega al checkout con un producto agotado.

**Desventaja:** la mayoría de los carritos se abandonan. Se generan miles de reservas falsas que inmoviliza stock real. ERP debe liberar reservas de carritos expirados como tarea permanente.

### Opción B — Reservar solo tras pago confirmado

ERP decrementa el stock únicamente cuando el pago está confirmado. No hay reserva intermedia.

**Ventaja:** máxima disponibilidad de stock. Sin reservas falsas.

**Desventaja:** si dos compradores pagan al mismo tiempo el último ítem, uno de los dos pagos quedará sin stock. ERP debe rechazar el segundo pago y gestionar un reembolso. Mala experiencia de compra.

### Opción C — Reserva controlada por ERP según política y medio de pago (elegida)

Commerce emite `order.placed`. ERP intenta reservar usando la `reservation_policy` correspondiente al medio de pago. ERP responde con `stock.reserved` o `stock.reservation_rejected`. Si la reserva expira sin pago confirmado, ERP la libera automáticamente.

**Ventaja:** equilibrio entre disponibilidad y consistencia. ERP mantiene la autoridad. Commerce no gestiona lógica de inventario.

**Desventaja:** Commerce puede confirmar un pedido que luego ERP rechaza (ventana de inconsistencia). Se necesita un flujo explícito de rechazo visible al comprador.

---

## 6. Decisión

**Opción C.** Reserva iniciada por `order.placed`, controlada por política de ERP según medio de pago.

Política de reserva publicada por ERP (parte del contrato de pedido, futuro):

```yaml
reservation_policy:
  online_immediate:
    trigger: checkout_confirmed
    ttl: "15m"

  bank_transfer:
    trigger: order_approved
    ttl: "48h"

  cash_on_pickup:
    trigger: order_accepted
    ttl: "24h"
```

Flujo de reserva:

```
Commerce confirma checkout
    ↓
order.placed  →  ERP
    │
    ├── reserva aceptada
    │      ↓
    │   stock.reserved  →  Commerce actualiza estado del pedido
    │
    └── reserva rechazada
           ↓
       stock.reservation_rejected  →  Commerce notifica al comprador
```

Autoridades por etapa:

| Acción | Responsable |
|---|---|
| Crear el pedido | Commerce Engine |
| Intentar la reserva | ERP (`erp.inventory`) |
| Aceptar o rechazar la reserva | ERP (`erp.inventory`) |
| Expirar y liberar la reserva | ERP (`erp.inventory`) |
| Notificar al comprador del rechazo | Commerce Engine (al recibir `stock.reservation_rejected`) |

Regla invariante: **Commerce nunca debe considerar un pedido confirmado hasta recibir `stock.reserved` de ERP.**

---

## 7. Consecuencias positivas

- El stock se reserva en el momento más tarde posible (checkout, no carrito) para minimizar inmovilización.
- La política de TTL es responsabilidad de ERP, no de Commerce. Si cambia el plazo de pago por transferencia, solo cambia la política en ERP.
- ERP puede rechazar una reserva sin que Commerce tenga que gestionar la lógica de stock.
- Las reservas tienen TTL explícito: nunca quedan huérfanas indefinidamente.

---

## 8. Consecuencias negativas y riesgos

- Existe una ventana de inconsistencia entre `order.placed` y `stock.reserved`. Durante ese período, un segundo comprador podría intentar comprar el mismo artículo.
- Si ERP rechaza la reserva después de que Commerce confirmó el pago, el flujo de reembolso puede ser complejo.
- El campo `reserved` en el contrato de stock (`inventory.stock.v1`) debe actualizarse en near-realtime para que `aggregate.available` sea preciso.

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `erp.inventory` | Implementar motor de reservas con TTL por política; emitir `stock.reserved` y `stock.reservation_rejected` |
| `commerce.engine` | Consumir `stock.reserved` para confirmar pedido; consumir `stock.reservation_rejected` para notificar y cancelar |
| `inventory.stock.v1` | El campo `reserved` por ubicación debe incluir las reservas activas |
| Notificaciones | Notificar al comprador cuando una reserva es rechazada o expira |

---

## 10. Principios protegidos o modificados

- **write_authority de `erp.inventory`**: solo ERP modifica el campo `reserved`. Commerce no escribe inventario directamente.
- **Principio de Autonomía**: ERP no llama a Commerce para rechazar una reserva. Publica un evento `stock.reservation_rejected` que Commerce consume.

---

## 11. Qué ocurre si el componente desaparece

Si `erp.inventory` no responde tras `order.placed`:

- Commerce mantiene el pedido en estado `pending_reservation` sin confirmarlo al comprador.
- El TTL de la sesión de checkout protege al comprador de esperar indefinidamente.
- Cuando `erp.inventory` se restablece, procesa los eventos `order.placed` pendientes y emite las respuestas correspondientes.

Si `commerce.engine` no recibe `stock.reserved` dentro de un umbral de tiempo:

- Commerce debe cancelar el pedido automáticamente y notificar al comprador.
- ERP libera la reserva si la emitió antes del fallo de comunicación.

---

## 12. Criterios de aceptación arquitectónica

- [ ] Un pedido con `online_immediate` que no recibe pago en 15 minutos tiene su reserva liberada automáticamente por ERP.
- [ ] Commerce no confirma ningún pedido al comprador sin haber recibido `stock.reserved`.
- [ ] Un `stock.reservation_rejected` genera una notificación visible al comprador antes de cualquier intento de cobro.
- [ ] El campo `aggregate.available` en `inventory.stock.v1` refleja el stock real menos las reservas activas.
- [ ] Dos compradores simultáneos del último ítem: solo uno recibe `stock.reserved`, el otro recibe `stock.reservation_rejected`.

---

## 13. Plan de transición

**Fase 1 (inicial):** solo `online_immediate`. TTL de 15 minutos. La reserva se implementa como decremento optimista en ERP al recibir el pago confirmado (sin reserva intermedia). Acepta la pequeña ventana de inconsistencia en el inicio.

**Fase 2:** reserva intermedia real con TTL. Implementar los eventos `stock.reserved` y `stock.reservation_rejected`.

**Fase 3:** políticas `bank_transfer` y `cash_on_pickup`. Motor de TTL parametrizable por ERP.

---

## 14. Evidencia y referencias

- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- Patrón Saga (compensating transactions) para flujos de pedido distribuidos: Chris Richardson, *Microservices Patterns*, Cap. 4.
- Stripe y MercadoPago: ambos confirman el pago antes de que el merchant reciba el evento de cobro — no garantizan disponibilidad de stock.
