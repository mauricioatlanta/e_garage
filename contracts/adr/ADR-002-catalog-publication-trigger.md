# ADR-002 — Catalog Publication Trigger

- **Estado:** Proposed
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `catalog.product-knowledge.v1`
- **Sustituye:** —
- **Sustituido por:** —
- **Depende de:** ADR-001 (el atributo `product_version` solo puede existir si el esquema de atributos está definido)

---

## 1. Dueño del dato

**ERP Core** (`erp.catalog`) es el único propietario del catálogo de productos. Solo `erp.catalog` decide cuándo un producto está listo para publicarse y cuándo debe retirarse.

---

## 2. Contexto y problema

Cuando ERP modifica un producto — precio, nombre, atributo, estado de publicación — Commerce Engine necesita enterarse para mantener el catálogo del storefront actualizado. El problema tiene tres dimensiones:

1. **Latencia**: ¿cuánto tiempo puede pasar entre un cambio en ERP y su reflejo en Commerce?
2. **Consistencia**: ¿qué ocurre si se pierde un evento? ¿Puede Commerce quedar permanentemente desincronizado?
3. **Idempotencia**: ¿puede Commerce procesar el mismo mensaje dos veces sin efectos secundarios?

El mecanismo de disparo afecta directamente las garantías declaradas en `catalog.product-knowledge.v1` (`consistency: eventual`, `completeness: full-snapshot`, `max_staleness: 5m`).

---

## 3. Capa responsable

| Subsistema | Responsabilidad |
|---|---|
| `erp.catalog` | Detecta cambios, persiste eventos en outbox, emite al canal |
| `commerce.engine` | Consume eventos, actualiza índice, idempotencia local |

---

## 4. Contratos utilizados

- `catalog.product-knowledge.v1` — este ADR define el mecanismo de disparo del contrato.

---

## 5. Opciones consideradas

### Opción A — Snapshot completo periódico

ERP genera un snapshot completo del catálogo cada N minutos y Commerce lo consume entero.

**Ventaja:** simple, sin lógica de eventos. La reconciliación es automática.

**Desventaja:** latencia alta (N minutos). Volumen de datos alto incluso para un cambio de un solo campo. Carga innecesaria en base de datos.

### Opción B — Solo eventos incrementales

Cuando ERP modifica un producto, dispara un evento directamente desde la señal Django (`post_save`). Commerce consume el evento y actualiza solo ese producto.

**Ventaja:** near-realtime. Volumen bajo.

**Desventaja:** si se pierde un evento (crash, reinicio, error de red), Commerce queda permanentemente desincronizado sin saberlo. No hay mecanismo de recuperación. Las señales Django no garantizan entrega exacta.

### Opción C — Modelo híbrido: Transactional Outbox + eventos incrementales + snapshot de reconciliación (elegida)

1. Cuando ERP modifica un producto, escribe el evento en una tabla `outbox` dentro de la misma transacción.
2. Un proceso separado lee el outbox y emite los eventos al canal.
3. Commerce consume eventos incrementales: actualización near-realtime.
4. Un proceso batch periódico emite un snapshot completo para reconciliación.
5. Un producto eliminado genera un tombstone explícito, no silencio.

**Ventaja:** near-realtime, recuperable, idempotente, trazable, independiente del transporte.

**Desventaja:** mayor complejidad de implementación. Requiere el patrón outbox y un worker de procesamiento.

---

## 6. Decisión

**Opción C.** Modelo híbrido con transactional outbox.

Payload del evento incremental:

```json
{
  "product_id": "erp-product-123",
  "product_version": 19,
  "operation": "upsert",
  "occurred_at": "2026-07-30T20:00:00Z"
}
```

Operaciones permitidas:

| Operación | Significado |
|---|---|
| `upsert` | El producto fue creado o modificado. Commerce debe re-leer el producto completo. |
| `unpublish` | El producto debe ocultarse del storefront pero conservarse en el índice. |
| `delete` | El producto fue eliminado. Commerce debe eliminarlo del índice. |

Reglas del outbox:

1. El evento se persiste en la misma transacción que el cambio de producto. Si la transacción hace rollback, el evento también.
2. El worker de outbox procesa solo eventos confirmados (post-commit).
3. Commerce ignora cualquier evento con `product_version` menor o igual al último procesado para ese `product_id`.
4. La reconciliación batch ejecuta al menos una vez cada 24 horas.

---

## 7. Consecuencias positivas

- Un cambio de precio en ERP refleja en Commerce en menos de 5 minutos.
- El mismo evento procesado dos veces no genera duplicados (idempotencia por `product_version`).
- Un reinicio del worker no genera pérdida de eventos (outbox persiste hasta confirmación).
- Un tombstone explícito garantiza que los productos eliminados desaparezcan del storefront.
- La reconciliación batch corrige cualquier inconsistencia acumulada.

---

## 8. Consecuencias negativas y riesgos

- Requiere implementar el patrón transactional outbox, que no existe hoy en eGarage.
- El worker de outbox es un proceso adicional a operar y monitorear.
- Si Commerce procesa eventos fuera de orden (puede ocurrir en sistemas distribuidos), puede mostrar brevemente un estado antiguo hasta que el evento correcto llegue o la reconciliación lo corrija.

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `erp.catalog` | Implementar tabla outbox; modificar flujo de guardado de productos |
| `commerce.engine` | Implementar consumidor idempotente con control de `product_version` |
| Infraestructura | Worker de outbox; scheduler de reconciliación batch |

---

## 10. Principios protegidos o modificados

- **Principio de Autonomía**: ERP no llama directamente a Commerce. Publica eventos. Commerce decide cuándo consumirlos.
- **write_authority**: solo `erp.catalog` puede escribir en el catálogo. El outbox es una extensión de esa autoridad, no una excepción.

---

## 11. Qué ocurre si el componente desaparece

Si `erp.catalog` deja de emitir eventos:

- Commerce mantiene el último estado conocido. El storefront sigue funcionando.
- Commerce puede detectar la interrupción comparando el `batch_sequence` del último snapshot recibido con el tiempo transcurrido.
- Cuando `erp.catalog` se restablece, el outbox entrega los eventos pendientes. La reconciliación batch restaura la consistencia completa.

Si Commerce Engine deja de consumir eventos:

- El outbox acumula eventos no procesados. ERP sigue operando sin degradación.
- Cuando Commerce se restablece, procesa los eventos pendientes en orden. La idempotencia garantiza que no haya duplicados.

---

## 12. Criterios de aceptación arquitectónica

- [ ] Un cambio de precio en ERP aparece en Commerce en menos de 5 minutos (medido en staging).
- [ ] El mismo evento con la misma `product_version` procesado dos veces no genera un segundo update en el índice de Commerce.
- [ ] Un producto eliminado en ERP genera un tombstone visible en el log de Commerce antes de desaparecer del storefront.
- [ ] Una interrupción de 30 minutos en el worker de outbox no genera inconsistencias permanentes: la reconciliación batch las corrige.
- [ ] La reconciliación batch puede ejecutarse mientras el storefront está en producción sin downtime.

---

## 13. Plan de transición

**Fase 1 (inicial):** solo snapshot periódico cada 5 minutos. Sin outbox. Sin eventos incrementales. Acepta la latencia de hasta 5 minutos para cambios de producto.

**Fase 2:** implementar outbox transaccional y worker. Mantener el snapshot como reconciliación. Reducir latencia a menos de 1 minuto.

**Fase 3:** monitoreo del lag de outbox como métrica de salud del sistema. Alertas si el lag supera el `max_staleness` declarado en el contrato.

---

## 14. Evidencia y referencias

- Patrón Transactional Outbox: [microservices.io/patterns/data/transactional-outbox](https://microservices.io/patterns/data/transactional-outbox.html) — Chris Richardson.
- Idempotent consumer: [microservices.io/patterns/communication/idempotent-consumer](https://microservices.io/patterns/communication/idempotent-consumer.html).
- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
