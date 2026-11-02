# ADR-004 — Multi-warehouse Strategy

- **Estado:** Proposed
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `inventory.stock.v1`
- **Sustituye:** —
- **Sustituido por:** —
- **Precede a:** ADR-003 (la estrategia de reserva depende de si el stock está distribuido por ubicación)

---

## 1. Dueño del dato

**ERP Core** (`erp.inventory`) es el único propietario del stock. Solo `erp.inventory` puede crear, modificar o eliminar registros de inventario. Commerce Engine nunca escribe stock directamente.

---

## 2. Contexto y problema

En su estado inicial, una empresa en eGarage tiene una sola bodega. Sin embargo, el esquema del contrato `inventory.stock.v1` debe ser diseñado para soportar múltiples ubicaciones desde el primer día, porque:

1. Añadir `location_id` en v2 es un **breaking change** que requeriría migrar todos los consumidores.
2. Una empresa puede crecer de una a varias bodegas sin cambiar de plataforma.
3. El proceso de fulfillment (envío, retiro en tienda, despacho desde bodega) depende de saber en qué ubicación está el stock.

La pregunta es: ¿cómo diseñar el contrato para que sea simple para empresas con una sola bodega y correcto para empresas con múltiples ubicaciones, sin que sean versiones distintas del contrato?

---

## 3. Capa responsable

| Subsistema | Responsabilidad |
|---|---|
| `erp.inventory` | Mantiene stock por ubicación; publica actualizaciones y agregado comercial |
| `commerce.engine` | Consume stock disponible; decide si el producto es vendible; no suma stock entre ubicaciones sin instrucción explícita |
| Fulfillment (futuro) | Selecciona la ubicación de despacho según la lógica del pedido |

---

## 4. Contratos utilizados

- `inventory.stock.v1` — este ADR define la estructura del campo `locations` y el `aggregate`.

---

## 5. Opciones consideradas

### Opción A — Una sola cantidad global sin location_id

El contrato publica un único campo `quantity_available` por producto.

**Ventaja:** esquema simple. Sin complejidad de ubicaciones.

**Desventaja:** agregar `location_id` en el futuro es un breaking change. No soporta retiro en tienda vs despacho a domicilio desde distintas bodegas. Bloquea el crecimiento.

### Opción B — Solo stock por ubicación, sin agregado

El contrato publica un array de ubicaciones. Cada producto tiene `n` registros, uno por `location_id`. No hay campo de agregado.

**Ventaja:** máxima precisión.

**Desventaja:** Commerce Engine debe sumar el stock por ubicación para decidir si un producto es vendible. Esa suma tiene reglas de negocio (no toda bodega puede despachar a todo cliente). Commerce no debe contener esa lógica.

### Opción C — Stock por ubicación + agregado comercial publicado por ERP (elegida)

El contrato publica:
- Un array de `locations` con stock físico, reservado y disponible por ubicación.
- Un campo `aggregate` con el total comercialmente vendible, calculado por ERP.

Commerce usa `aggregate.available` para decidir si el producto es vendible. El fulfillment usa `locations` para decidir desde dónde despachar.

**Ventaja:** Commerce no necesita conocer la lógica de suma de ubicaciones. Una empresa con una sola bodega usa `location_id: "warehouse-main"` sin cambios de comportamiento. El contrato no cambia cuando se agrega una segunda bodega.

---

## 6. Decisión

**Opción C.** `location_id` es obligatorio desde v1. Una empresa con una sola bodega usa una ubicación predeterminada. ERP publica también un `aggregate` comercial.

Modelo del payload:

```json
{
  "product_id": "erp-product-123",
  "stock_version": 27,
  "locations": [
    {
      "location_id": "warehouse-main",
      "physical": 10,
      "reserved": 2,
      "available": 8,
      "fulfillment": {
        "pickup": true,
        "delivery": true
      }
    }
  ],
  "aggregate": {
    "available": 8,
    "sellable": true
  }
}
```

Reglas:

1. `location_id` es obligatorio. Una empresa sin bodegas configuradas usa `"warehouse-main"` como valor predeterminado.
2. Commerce usa `aggregate.available` para mostrar disponibilidad en el storefront.
3. Commerce no debe sumar `available` entre ubicaciones por su propia cuenta.
4. La selección de `location_id` para el fulfillment pertenece al proceso de pedido, no al contrato de stock.
5. Stock disponible (`aggregate.sellable: true`) no implica que cualquier canal pueda venderlo. La disponibilidad puede variar por canal y método de entrega.

---

## 7. Consecuencias positivas

- Agregar una segunda bodega no requiere cambio de versión del contrato.
- Commerce Engine tiene una respuesta directa para "¿es este producto vendible?" sin lógica de negocio propia.
- El proceso de fulfillment tiene la información necesaria para elegir la bodega de despacho.
- Una empresa simple opera exactamente igual que hoy, sin código adicional.

---

## 8. Consecuencias negativas y riesgos

- ERP debe mantener el campo `aggregate` actualizado y sincronizado con las ubicaciones. Si ERP publica `aggregate.available: 5` pero `locations[*].available` suma 8, hay inconsistencia interna que ERP debe detectar y corregir.
- El campo `fulfillment` por ubicación puede volverse complejo cuando se agreguen reglas de canal (pickup solo en ciertos horarios, despacho con restricciones geográficas).

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `erp.inventory` | Estructurar stock por ubicación; calcular y publicar `aggregate` |
| `commerce.engine` | Consumir `aggregate.available` para disponibilidad; no sumar `locations` |
| Fulfillment (futuro) | Consumir `locations` para selección de bodega de despacho |
| ADR-003 | La reserva debe especificar `location_id` para ser procesada por ERP |

---

## 10. Principios protegidos o modificados

- **Principio de Autonomía**: Commerce Engine no necesita conocer la lógica de suma de ubicaciones. ERP publica el resultado.
- **write_authority**: solo `erp.inventory` puede escribir stock. La existencia del campo `aggregate` no habilita a nadie más a escribirlo.
- **Separabilidad**: el módulo de fulfillment puede evolucionar de forma independiente porque el contrato ya expone `locations`.

---

## 11. Qué ocurre si el componente desaparece

Si `erp.inventory` deja de publicar actualizaciones de stock:

- Commerce opera con el último stock conocido por ubicación y el último `aggregate`.
- El storefront puede seguir vendiendo hasta agotar `aggregate.available` según el estado cacheado.
- Cuando `erp.inventory` se restablece, debe publicar una actualización completa para cada producto afectado.

---

## 12. Criterios de aceptación arquitectónica

- [ ] MonteAzul con una sola bodega opera con `location_id: "warehouse-main"` sin diferencia de comportamiento respecto a una empresa con múltiples bodegas.
- [ ] `aggregate.available` es siempre menor o igual a la suma de `locations[*].available`.
- [ ] Commerce usa exclusivamente `aggregate.available` para mostrar disponibilidad en el storefront.
- [ ] Agregar una segunda bodega no requiere un cambio de versión del contrato `inventory.stock.v1`.
- [ ] El campo `fulfillment` por ubicación permite distinguir entre pickup y delivery de forma independiente.

---

## 13. Plan de transición

**Fase 1 (inicial):** todas las empresas tienen una única ubicación `"warehouse-main"`. El campo `fulfillment` tiene `pickup: false, delivery: true` por defecto. El `aggregate` es igual a `locations[0].available`.

**Fase 2:** interfaz de administración para configurar múltiples bodegas. ERP calcula el `aggregate` con reglas de negocio por canal.

**Fase 3:** fulfillment inteligente — selección automática de bodega de despacho según distancia, stock y método de entrega.

---

## 14. Evidencia y referencias

- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- Patrón "Available to Promise" (ATP) en sistemas de gestión de inventario.
- Shopify Locations API como referencia de diseño de contratos multi-warehouse en e-commerce SaaS.
