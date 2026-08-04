# ADR-005 — Tax Calculation Authority

- **Estado:** Proposed
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `tax.policy.v1`
- **Sustituye:** —
- **Sustituido por:** —

---

## 1. Dueño del dato

La **Tax Policy** pertenece a **ERP Core** (`erp.tax-engine`). Es el único subsistema autorizado a definir y publicar políticas fiscales. El **cálculo fiscal autoritativo** (el que produce el documento legal) también pertenece a ERP. Commerce Engine calcula estimaciones comerciales usando la política publicada, pero nunca produce el documento fiscal.

---

## 2. Contexto y problema

El motor de impuestos de eGarage vive en `taller/impuestos/engine.py` (ERP Core). Implementa reglas por país: IVA 19% en Chile sobre partes, IGV 18% en Perú sobre todo, Sales Tax variable en USA por estado y ciudad.

Commerce Engine necesita mostrar precios con impuestos al comprador durante la navegación del catálogo, en el carrito y en el checkout — antes de que exista una transacción contable. El problema es:

1. **Duplicación**: si Commerce implementa su propio motor tributario, hay dos fuentes de lógica fiscal que pueden desincronizarse.
2. **Acoplamiento**: si Commerce llama a ERP en cada carga de página para calcular impuestos, crea una dependencia síncrona de alta frecuencia.
3. **Autoridad**: el documento fiscal (boleta, factura) debe ser producido por ERP, no por Commerce. ¿Cómo garantizar que Commerce no genere documentos tributarios?

---

## 3. Capa responsable

| Subsistema | Cálculo | Propósito |
|---|---|---|
| `erp.tax-engine` | Define y publica `TaxPolicy` | Fuente de verdad. Documento fiscal definitivo. |
| `commerce.engine` | Estima el impuesto para el comprador | Visualización comercial previa a la compra. |
| `erp` (al emitir documento) | Cálculo fiscal autoritativo | Documento legal: boleta, factura, nota de crédito. |

---

## 4. Contratos utilizados

- `tax.policy.v1` — exporta las políticas que Commerce usa para calcular estimaciones.

---

## 5. Opciones consideradas

### Opción A — Solo ERP calcula (Commerce llama a ERP en tiempo real)

Commerce llama a un endpoint de ERP para calcular el impuesto en cada producto, en el carrito y en el checkout.

**Ventaja:** un único punto de cálculo. Siempre actualizado.

**Desventaja:** acoplamiento síncrono fuerte. Si ERP tiene latencia o no está disponible, el storefront de Commerce se degrada. Alta frecuencia de llamadas (cada carga de catálogo). Viola el Principio de Autonomía.

### Opción B — Solo Commerce calcula (duplica la lógica)

Commerce implementa su propio motor tributario con las mismas reglas que ERP.

**Ventaja:** Commerce es completamente autónomo.

**Desventaja:** duplicación de lógica tributaria. Si cambia una regla fiscal, debe actualizarse en dos lugares. Riesgo de discrepancias que generan problemas legales.

### Opción C — Separación de responsabilidades: política en ERP, estimación en Commerce, documento en ERP (elegida)

ERP define y publica la `TaxPolicy` versionada. Commerce recibe la política y la usa para calcular estimaciones comerciales. Cuando se emite el documento fiscal, ERP realiza el cálculo autoritativo usando la misma política, y persiste el resultado en el pedido como `tax_snapshot`.

**Ventaja:** Commerce es autónomo para mostrar precios. ERP mantiene la autoridad fiscal. No hay duplicación de lógica (la política es la misma, el código de cálculo puede ser el mismo o equivalente). Las discrepancias son detectables y procesables.

---

## 6. Decisión

**Opción C.** Tres responsabilidades distintas con contratos claros entre ellas.

Flujo:

```
ERP Tax Domain
    │
    └── publica tax.policy.v1
              │
    ┌─────────┴──────────┐
    │                    │
Commerce Engine        ERP (al emitir documento)
    │                    │
Estimación          Cálculo autoritativo
comercial           + Documento legal
(carrito/checkout)  (boleta, factura)
```

`tax_snapshot` que debe conservar el pedido:

```json
{
  "tax_snapshot": {
    "policy_id": "tax-cl-iva-2026",
    "policy_version": "1.0.0",
    "calculated_at": "2026-07-30T20:00:00Z",
    "taxable_amount": "10000",
    "tax_amount": "1900",
    "total": "11900",
    "calculated_by": "commerce.engine"
  }
}
```

Cuando ERP emite el documento, reemplaza `calculated_by` con `erp.tax-engine` y registra cualquier discrepancia.

Regla de discrepancia: si la diferencia entre la estimación de Commerce y el cálculo de ERP supera el 1% (o cualquier umbral legal aplicable), ERP **no debe modificar silenciosamente** el total cobrado. Debe emitir una `tax.discrepancy` como evento procesable.

---

## 7. Consecuencias positivas

- Commerce puede mostrar precios con impuestos sin llamar a ERP en cada carga de página.
- El documento fiscal sigue siendo producido y validado por ERP. Ningún riesgo legal se traslada a Commerce.
- Si la política fiscal cambia (nueva tasa de IVA, nueva categoría), ERP publica una nueva versión de la política. Commerce la recibe en el próximo batch y actualiza sus estimaciones.
- El `tax_snapshot` en el pedido permite auditar exactamente qué política se aplicó en cada venta.

---

## 8. Consecuencias negativas y riesgos

- Puede existir una discrepancia entre la estimación de Commerce y el cálculo de ERP si la política cambió entre el momento del checkout y la emisión del documento. Este es un riesgo inherente a cualquier sistema con cálculo anticipado.
- Commerce debe implementar el motor de cálculo usando la política exportada. Si la política exportada tiene un error, ambos cálculos (estimación y autoritativo) pueden estar mal — aunque ERP los detectará al comparar.
- El campo `max_staleness: 24h` en el contrato significa que una política nueva puede tardar hasta 24 horas en llegar a Commerce. En países con cambios fiscales frecuentes, este TTL puede necesitar reducirse.

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `erp.tax-engine` | Publicar `TaxPolicy` versionada via `tax.policy.v1`; detectar discrepancias al emitir documentos |
| `commerce.engine` | Calcular estimaciones usando la política recibida; almacenar `tax_snapshot` en el pedido |
| `taller/impuestos/engine.py` | Fuente del cálculo autoritativo de ERP; no debe duplicarse en Commerce |
| Módulo de pedidos | El pedido debe conservar `tax_snapshot` como campo inmutable |

---

## 10. Principios protegidos o modificados

- **Principio de Autonomía**: Commerce calcula estimaciones de forma autónoma sin llamar a ERP en tiempo real.
- **write_authority**: solo `erp.tax-engine` define y publica políticas fiscales. Commerce no puede crear ni modificar políticas.
- **Separabilidad**: si Commerce desaparece, el motor fiscal de ERP sigue operando sin cambios. Los documentos se emiten correctamente desde ERP.

---

## 11. Qué ocurre si el componente desaparece

Si `erp.tax-engine` deja de publicar `TaxPolicy`:

- Commerce usa la última política conocida (cacheada). Las estimaciones pueden quedar desactualizadas si cambia la ley fiscal.
- ERP sigue emitiendo documentos correctamente usando su motor interno (no depende del contrato publicado para el cálculo autoritativo).

Si `commerce.engine` no puede calcular impuestos (falta la política):

- El checkout debe bloquearse hasta recibir una política válida. No se deben mostrar precios sin impuesto en países donde es obligatorio.

---

## 12. Criterios de aceptación arquitectónica

- [ ] Chile: IVA 19% aplicado únicamente a partes. Los servicios no llevan impuesto. Verificado en Commerce y en ERP.
- [ ] Perú: IGV 18% aplicado a partes y servicios. Verificado en Commerce y en ERP.
- [ ] El `tax_snapshot` del pedido conserva `policy_id`, `policy_version` y `calculated_at`.
- [ ] Una discrepancia entre estimación de Commerce y cálculo de ERP mayor al 1% genera un evento `tax.discrepancy` visible en los logs de ERP.
- [ ] Un cambio de política publicado por ERP llega a Commerce en menos de 24 horas (dentro del `max_staleness` declarado).
- [ ] Commerce bloquea el checkout si no tiene una política de impuestos vigente para el país del tenant.

---

## 13. Plan de transición

**Fase 1 (inicial):** solo Chile (IVA 19% fijo sobre partes). La política se define como constante en `commerce.engine` usando el valor exportado. Sin complejidad multi-país.

**Fase 2:** `tax.policy.v1` implementado como contrato real. Commerce recibe la política via batch. Cubre CL y PE.

**Fase 3:** USA (Sales Tax por estado/ciudad). MX (IVA 16%). AR (IVA 21%). Política completamente dinámica.

---

## 14. Evidencia y referencias

- `taller/impuestos/engine.py` — motor tributario actual en eGarage ERP.
- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- Stripe Tax como referencia de separación entre estimación y cálculo autoritativo en plataformas de pagos.
