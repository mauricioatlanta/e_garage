# ADR-008 — Stock Domain vs Reservation Domain Boundary

- **Estado:** Proposed
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `inventory.stock.v1`, `inventory.reservation.v1` (nuevo)
- **Sustituye:** —
- **Sustituido por:** —
- **Depende de:** ADR-003 (reserva iniciada por `order.placed`), ADR-004 (multi-warehouse, `location_id`)

---

## 1. Dueño del dato

**`inventory.stock.v1`** — dueño: `erp.inventory`. Publica el estado observable del inventario físico, incluyendo el agregado `available` que ya descuenta reservas activas y bloqueos operacionales. Es la única fuente de verdad sobre cuántas unidades puede vender Commerce en un instante dado.

**`inventory.reservation.v1`** — dueño: `erp.inventory`. Publica el ciclo de vida de las reservas individuales. Es la fuente de verdad sobre qué reservas existen, cuándo expiran y cómo terminan (confirmadas, rechazadas, expiradas, liberadas).

Ningún consumidor externo a `erp.inventory` escribe en ninguno de los dos dominios.

---

## 2. Contexto y problema

ADR-003 decidió que la reserva de stock se inicia con `order.placed` y que ERP responde con `stock.reserved` o `stock.reservation_rejected`. ADR-004 introdujo la dimensión `location_id` y el agregado `{available, sellable}` por ubicación.

Quedó sin respuesta la pregunta de diseño más importante: **¿estos eventos pertenecen al mismo contrato que el estado físico del stock, o a un contrato separado?**

Si los eventos de reserva y el estado de stock se mezclan en un solo contrato:
- Un consumidor de inventario (analytics, reporting) recibe ruido de reservas que no le importan.
- Un consumidor de reservas (Commerce, notificaciones) recibe snapshots de inventario completos que no necesita.
- La semántica de las garantías se vuelve ambigua: ¿`ordered: true` aplica al stock o a la reserva?
- La frecuencia es incompatible: el stock físico cambia con recepciones (lenta), la reserva cambia con cada checkout (near-realtime, alta frecuencia).

La segunda pregunta es qué representa exactamente `aggregate.available` — si Commerce necesita cruzar al contrato de reservas para calcular disponibilidad, el dominio del stock está incompleto.

---

## 3. Capa responsable

| Subsistema | Responsabilidad |
|---|---|
| `erp.inventory` | Calcula y publica `aggregate.available`; gestiona el ciclo de vida de reservas |
| `commerce.engine` | Consume `aggregate.available` para mostrar disponibilidad; consume eventos de reserva para actualizar estado del pedido |
| `analytics` | Consume snapshots de stock para reporting; no necesita eventos de reserva |

---

## 4. Contratos utilizados

- `inventory.stock.v1` — estado observable del inventario (físico + agregados)
- `inventory.reservation.v1` (nuevo) — ciclo de vida de reservas individuales
- `commerce.order.v1` (futuro) — dispara el proceso de reserva con `order.placed`

---

## 5. Opciones consideradas

### Opción A — Un contrato único para stock y reservas

Un solo contrato `inventory.stock.v1` publica tanto el estado físico como los eventos de reserva.

**Ventaja:** un solo punto de suscripción; fácil de entender al inicio.

**Desventaja:** frecuencias incompatibles; acoplamiento de consumidores que no comparten intereses; la semántica de garantías (ordered, max_staleness) no puede satisfacer a ambos dominios simultáneamente; crecer el contrato con reservas obliga a versionar algo que debería ser estable.

### Opción B — Dos contratos separados: stock y reservas (elegida)

`inventory.stock.v1` publica únicamente el estado observable del inventario. `inventory.reservation.v1` publica el ciclo de vida de cada reserva.

**Ventaja:** cada contrato tiene garantías coherentes con su semántica; los consumidores suscriben exactamente lo que necesitan; el dominio del stock puede evolucionar a Stable independientemente del dominio de reservas; el dominio de reservas puede crecer (nuevos estados, auditoría) sin impactar el stock.

**Desventaja:** dos contratos para entender la disponibilidad completa; `erp.inventory` debe publicar en dos canales.

### Opción C — Contrato de stock con `aggregate.available` pre-calculado, sin eventos de reserva

`inventory.stock.v1` publica el estado físico más el agregado `available` (que ya descuenta reservas). Los eventos de reserva no son publicados como contrato — solo son internos de ERP.

**Desventaja:** Commerce pierde visibilidad sobre el ciclo de vida de sus reservas; no puede saber si una reserva fue rechazada o expiró sin un canal de comunicación.

---

## 6. Decisión

**Opción B.** Dos contratos con fronteras de dominio claras.

### Dominio Stock: `inventory.stock.v1`

Publica el **estado observable del inventario** — lo que es verdad en el sistema físico en un momento dado.

`aggregate.available` se define como:

```
aggregate.available = stock_físico - reservas_activas - bloqueos_operacionales + ajustes_válidos
```

Esta es una invariante del contrato: `erp.inventory` garantiza que el valor publicado ya incorpora el efecto de todas las reservas activas. **Commerce nunca necesita leer `inventory.reservation.v1` para calcular disponibilidad.** Si Commerce tiene un `aggregate.available = 5`, puede intentar vender hasta 5 unidades.

Tipos de mensaje:
- `inventory.stock.updated` — cambio incremental en el estado de una ubicación/producto
- `inventory.stock.snapshot` — snapshot completo para reconciliación

### Dominio Reservas: `inventory.reservation.v1`

Publica el **ciclo de vida de las reservas individuales** — lo que ocurrió con cada reserva específica.

Tipos de mensaje:
- `inventory.reservation.created` — ERP aceptó la solicitud y creó la reserva
- `inventory.reservation.confirmed` — la reserva fue convertida en despacho (pago confirmado)
- `inventory.reservation.rejected` — ERP rechazó la solicitud de reserva
- `inventory.reservation.expired` — la reserva expiró por TTL sin pago confirmado
- `inventory.reservation.released` — la reserva fue liberada manualmente (pedido cancelado)

### Regla invariante

> **Commerce nunca cruza contratos para calcular disponibilidad.** La única fuente de disponibilidad para mostrar al comprador es `aggregate.available` de `inventory.stock.v1`. Los eventos de `inventory.reservation.v1` actualizan el estado del pedido en Commerce, no la disponibilidad del catálogo.

---

## 7. Consecuencias positivas

- `inventory.stock.v1` puede evolucionar a Stable cuando ADR-001 y ADR-002 estén resueltos, sin esperar a que el dominio de reservas madure.
- Analytics puede consumir solo `inventory.stock.v1` sin recibir ruido de reservas.
- Commerce puede consumir solo `inventory.reservation.v1` para actualizar estado de pedidos, sin recibir snapshots de inventario completos.
- `aggregate.available` es un número accionable sin cómputo adicional en el consumidor.
- La semántica de `ordered: true` aplica de forma coherente dentro de cada dominio.

---

## 8. Consecuencias negativas y riesgos

- `erp.inventory` debe mantener dos canales de publicación.
- Existe un instante de inconsistencia entre la creación de una reserva y la actualización de `aggregate.available`. Commerce puede ver `available = 3` mientras ERP procesa una reserva sobre esa unidad. La ventana es acotada por `max_staleness`.
- Si `aggregate.available` no se actualiza dentro del `max_staleness`, Commerce puede sobre-vender. ERP debe publicar `inventory.stock.updated` cada vez que una reserva modifica el agregado.

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `erp.inventory` | Publicar en dos contratos; `aggregate.available` debe actualizarse atomicamente con cada cambio de reserva |
| `commerce.engine` | Suscribirse a `inventory.stock.v1` para disponibilidad; suscribirse a `inventory.reservation.v1` para estado de pedidos |
| `analytics` | Puede ignorar `inventory.reservation.v1` completamente |
| `inventory.stock.v1` | Eliminar eventos de reserva del contrato; agregar `aggregate.available` como campo de primer nivel |
| `inventory.reservation.v1` | Nuevo contrato; 5 tipos de mensaje con ciclo de vida completo |

---

## 10. Principios protegidos o modificados

- **Principio de Autonomía**: `erp.inventory` no llama a Commerce para informar un rechazo. Publica eventos que Commerce consume. Respetado por ambos contratos.
- **write_authority único**: solo `erp.inventory` escribe en ambos contratos.
- **Minimización de coupling**: Commerce no necesita conocer la estructura interna de reservas para mostrar disponibilidad. Solo necesita `aggregate.available`.

---

## 11. Qué ocurre si el componente desaparece

Si `erp.inventory` deja de publicar `inventory.stock.updated`:
- Commerce muestra el último `aggregate.available` conocido hasta que el `max_staleness` expire.
- Una vez expirado, Commerce debe deshabilitar el botón de compra o mostrar disponibilidad como desconocida.
- No debe asumir disponibilidad infinita ni disponibilidad cero.

Si `erp.inventory` deja de publicar en `inventory.reservation.v1`:
- Commerce no puede confirmar nuevos pedidos al comprador (no recibe `inventory.reservation.created`).
- Los pedidos en estado `pending_reservation` deben tener un TTL propio en Commerce.
- ERP debe procesar los eventos `order.placed` pendientes cuando se restablezca.

---

## 12. Criterios de aceptación arquitectónica

- [ ] `inventory.stock.v1` no contiene ningún evento de ciclo de vida de reserva.
- [ ] `inventory.reservation.v1` no contiene estado de stock físico.
- [ ] `aggregate.available` en `inventory.stock.updated` refleja el stock vendible después de restar reservas activas y bloqueos.
- [ ] Commerce determina disponibilidad únicamente leyendo `aggregate.available` — sin leer `inventory.reservation.v1`.
- [ ] Un cambio de reserva (created/rejected/expired) dispara un `inventory.stock.updated` correspondiente que actualiza `aggregate.available`.
- [ ] Los consumidores de analytics pueden suscribirse solo a `inventory.stock.v1` sin recibir eventos de `inventory.reservation.v1`.

---

## 13. Plan de transición

**Paso 1:** Migrar `inventory.stock.v1.yaml` a formato v2. Eliminar campos de reserva. Agregar `aggregate.available` como campo de primer nivel en el schema del snapshot.

**Paso 2:** Crear `inventory.reservation.v1.yaml` con los 5 tipos de mensaje del ciclo de vida de reservas.

**Paso 3:** Crear los schemas de payload para `inventory.stock.updated`, `inventory.stock.snapshot`, y los 5 eventos de `inventory.reservation.v1`.

**Paso 4 (futuro, implementación):** `erp.inventory` emite `inventory.stock.updated` en cada transacción que modifica `aggregate.available` (recepción, ajuste, cambio de reserva).

---

## 14. Evidencia y referencias

- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- Decisión explícita del usuario: "`aggregate.available` DEBE representar exactamente lo que Commerce puede vender en ese instante. Es decir: `aggregate.available` = stock físico - reservas activas - bloqueos operacionales + ajustes válidos."
- Decisión explícita del usuario: "`inventory.stock.v1` habla del estado observable del inventario. `inventory.reservation.v1` habla del ciclo de vida de las reservas. Son dominios diferentes."
- Vernon, Vaughn. *Implementing Domain-Driven Design*. Cap. 10: Aggregates.
- Richardson, Chris. *Microservices Patterns*. Cap. 4: Managing transactions with Sagas.
