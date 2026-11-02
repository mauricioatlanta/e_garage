# ADR-000 — Meta-Contract Evolution: Message Types, Interaction, and Transport

- **Estado:** Accepted
- **Fecha:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** todos — este ADR gobierna la estructura del Meta-Contrato del cual todos los contratos derivan
- **Sustituye:** —
- **Sustituido por:** —

> **Nota de proceso:** Este es el ADR fundacional del sistema de contratos.
> Ninguna modificación a `meta-contract.yaml` ni a `meta-contract.schema.json`
> puede realizarse sin que este ADR esté en estado `Accepted`.
> Los amendments marcados **[Blocking]** deben estar resueltos antes de esa transición.

---

## 1. Dueño del dato

El **Meta-Contrato** es propiedad de la plataforma eGarage como conjunto. No tiene un subsistema dueño porque es la capa de gobernanza que existe *por encima* de todos los subsistemas. Las modificaciones al Meta-Contrato requieren revisión arquitectónica explícita y un ADR en estado `Accepted` — este documento.

---

## 2. Contexto y problema

El Meta-Contrato actual (v1, creado el 2026-07-30) modela cada contrato como una unidad plana con un único schema, una única dirección y una única frecuencia:

```yaml
schema_ref: schemas/catalog.product-knowledge.v1.schema.json
direction: Pull
frequency: NearRealtime
```

ADR-002 (Catalog Publication Trigger) reveló que `catalog.product-knowledge.v1` en realidad transporta **tres mensajes con semánticas distintas**:

| Mensaje | Semántica | Frecuencia | Schema |
|---------|-----------|------------|--------|
| Producto modificado | Evento incremental | NearRealtime | Diferente |
| Snapshot completo | Estado completo | Batch (reconciliación) | Diferente |
| Tombstone | Señal de eliminación | NearRealtime | Diferente |

Un modelo plano no puede expresar esto sin ambigüedad. `direction: Pull` y `frequency: NearRealtime` describen *uno* de los tres mensajes, dejando los otros dos sin contrato formal.

Esto tiene consecuencias concretas:

1. Un consumidor no puede declarar que solo consume el snapshot periódico y no los eventos incrementales.
2. No hay versionado independiente por tipo de mensaje — si cambia el schema del tombstone, todos los consumidores reciben una nueva versión del contrato completo.
3. La separación entre *patrón de interacción* (evento, snapshot, request-response) y *mecanismo de transporte* (queue, HTTP, archivo) no existe, lo que acopla el "qué" con el "cómo".

---

## 3. Capa responsable

El Meta-Contrato es una herramienta de gobernanza de la plataforma. No pertenece a ERP Core ni a Commerce Engine. Es mantenido por quien tenga el rol de arquitecto de plataforma.

---

## 4. Contratos utilizados

Este ADR no consume ningún contrato externo. Es la autoridad que define la estructura de todos los contratos.

---

## 5. Opciones consideradas

### Opción A — Mantener el modelo plano, agregar campos opcionales

Agregar `message_types[]` como campo opcional al Meta-Contrato actual, manteniendo `direction` y `frequency` para compatibilidad.

**Ventaja:** migración sin breaking change para los contratos existentes.

**Desventaja:** el modelo plano y el modelo por message_types coexisten con semánticas solapadas. La ambigüedad que queremos eliminar se convierte en un campo más del mismo documento.

### Opción B — Migrar completamente a `message_types[]` con transición forzada

Reemplazar `direction`, `frequency` y `schema_ref` por un array `message_types[]` obligatorio. Los contratos existentes deben migrarse antes de poder ser marcados `stable`.

**Ventaja:** modelo limpio desde el primer contrato estable. Sin ambigüedad.

**Desventaja:** los cuatro contratos draft actuales deben actualizarse. Mayor trabajo de migración, pero todos están en `status: draft`, por lo que no hay consumidores de producción que romper.

### Opción C — Meta-Contrato versionado: v1 para contratos simples, v2 para contratos con múltiples mensajes

Dos versiones del Meta-Contrato coexisten. Los contratos simples usan v1. Los contratos con múltiples mensajes usan v2.

**Ventaja:** migración gradual.

**Desventaja:** dos modelos de contrato en el mismo Registry generan confusión de tooling y documentación. La pregunta "¿cuándo usas v1 vs v2?" no tiene una respuesta objetiva.

---

## 6. Decisión

**Opción B**, con la incorporación de los amendments A, B, C y D descritos en las secciones 6.1 a 6.4.

Dado que todos los contratos están en `status: draft` y ninguno tiene consumidores de producción, el costo de la migración es bajo y el beneficio de un modelo limpio desde el primer contrato estable es alto.

### 6.1 — Amendment A [Pre-Stable]: `message_types[].id` globalmente único

Los identificadores de message_type deben ser únicos a nivel de plataforma, no solo dentro de un contrato.

**Formato:** `{domain}.{entity}.{action}`

```yaml
# Correcto
message_types:
  - id: catalog.product.changed
  - id: catalog.product.snapshot
  - id: catalog.product.tombstone

# Incorrecto — ambiguo en cinco años cuando Stock también tenga un incremental-event
message_types:
  - id: incremental-event
  - id: full-snapshot
```

Un consumidor puede entonces declarar:

> "Consumo `catalog.product.changed` y `inventory.stock.updated`."

Sin mencionar el contrato padre. Esto reduce el acoplamiento al mínimo posible.

### 6.2 — Amendment B [Pre-Stable]: separar `interaction` de `transport`

El campo `direction` actual mezcla el patrón de interacción con el mecanismo de transporte. Se reemplaza por dos campos separados:

| Campo | Pregunta que responde | Valores |
|-------|----------------------|---------|
| `interaction` | ¿Qué patrón de intercambio usa este mensaje? | `event`, `request-response`, `snapshot`, `stream` |
| `transport` | ¿Por qué canal físico viaja? | `queue`, `http`, `file`, `grpc`, `webhook` |

Ejemplo:

```yaml
# Un snapshot puede viajar por queue o por HTTP — son decisiones independientes
- id: catalog.product.snapshot
  interaction: snapshot      # patrón semántico
  transport: queue           # mecanismo físico (puede cambiar sin cambiar la semántica)
```

Cambiar el `transport` de `queue` a `http` es un cambio de implementación.
Cambiar el `interaction` de `snapshot` a `event` es un breaking change que requiere nueva versión.

### 6.3 — Amendment C [Blocking]: definición explícita de qué es un contrato

El Meta-Contrato actual no define formalmente qué es un contrato. Esta omisión puede llevar a que alguien cree un contrato por cada mensaje individual.

**Definición canónica:**

> Un **contrato** es un conjunto nombrado y versionado de Message Types que comparten un dominio común y son gobernados por un único publicador.

Consecuencias de esta definición:

- Un contrato agrupa mensajes relacionados del mismo dominio. `catalog.product-knowledge.v1` agrupa todos los mensajes de conocimiento de producto del catálogo.
- Un mensaje no puede pertenecer a dos contratos simultáneamente.
- El versionado del contrato (`v1`, `v2`) representa la evolución del *conjunto*. El versionado de un `message_type` individual (`version: 1.0.0`) representa la evolución de ese mensaje específico.
- Si un dominio necesita un mensaje completamente diferente que no encaja en ningún contrato existente, se crea un contrato nuevo — no se agrega al contrato más cercano.

Esta definición debe aparecer en el campo `meta_description` del `meta-contract.yaml` y en el `README.md` del registry.

### 6.4 — Amendment D [Non-blocking]: compatibilidad declarada con AsyncAPI

El modelo de message_types con `interaction`, `transport`, y `guarantees` está diseñado para poder exportarse a [AsyncAPI 3.x](https://www.asyncapi.com/) sin pérdida de información.

Esto no obliga a usar AsyncAPI. Significa que si en el futuro se decide generar documentación automática, SDKs internos, o validación de contratos en CI usando herramientas AsyncAPI, el modelo del Meta-Contrato lo soporta directamente.

Mapeo de campos eGarage → AsyncAPI:

| Campo eGarage | Equivalente AsyncAPI |
|---|---|
| `message_types[].id` | `channels.{id}.messages` |
| `message_types[].interaction` | `channels.{id}.bindings` |
| `message_types[].transport` | `servers.{name}.protocol` |
| `message_types[].schema_ref` | `components.messages.{id}.payload` |
| `message_types[].guarantees` | `components.messages.{id}.traits` |

---

## 7. Estructura del Meta-Contrato v2

El Meta-Contrato evolucionado tiene esta estructura para cada contrato:

```yaml
# Campos de identidad — sin cambio
id: catalog.product-knowledge.v1
display_name: Product Knowledge Contract
category: Truth

# Campos de ownership — sin cambio
owner: erp.catalog
publisher: erp.catalog
write_authority: erp.catalog

# consumers ahora declara por subsistema qué message_types consume (§8)
consumers:
  - subsystem: commerce.engine
    message_types:
      - catalog.product.changed
      - catalog.product.tombstone
  - subsystem: analytics
    message_types:
      - catalog.product.snapshot

# Reemplaza: direction, frequency, schema_ref
message_types:
  - id: catalog.product.changed          # Amendment A: globalmente único
    description: Incremental update when a product is created or modified.
    schema_ref: schemas/catalog.product.changed.schema.json
    version: "1.0.0"
    interaction: event                   # Amendment B: patrón semántico
    transport: queue                     # Amendment B: mecanismo físico
    guarantees:
      idempotent: true
      ordered: false
      consistency: eventual
      completeness: delta
      max_staleness: "5m"

  - id: catalog.product.snapshot
    description: Full catalog snapshot for reconciliation.
    schema_ref: schemas/catalog.product.snapshot.schema.json
    version: "1.0.0"
    interaction: snapshot
    transport: queue
    guarantees:
      idempotent: true
      ordered: false
      consistency: eventual
      completeness: full-snapshot
      max_staleness: "24h"

  - id: catalog.product.tombstone
    description: Signals that a product has been deleted and must be removed from Commerce.
    schema_ref: schemas/catalog.product.tombstone.schema.json
    version: "1.0.0"
    interaction: event
    transport: queue
    guarantees:
      idempotent: true
      ordered: false
      consistency: eventual
      completeness: delta
      max_staleness: "5m"

# Versioning — sin cambio
# Nota: "1.0.0" es la versión semántica del contrato de datos, no del meta-modelo.
# Migrar el formato de archivo a meta-contract v2 no es un breaking change en los datos.
version: "1.0.0"
status: draft
breaking_change_policy: semver-major
min_consumer_version: "1.0.0"
pending_decisions: []
```

---

## 8. Principio derivado: declaración explícita de consumo

Este principio emerge del Amendment A y merece ser elevado como regla arquitectónica:

> **Los consumidores declaran exactamente qué `message_type` consumen, no qué contrato consumen.**

En la práctica:

```yaml
# En el contrato catalog.product-knowledge.v1:
consumers:
  - subsystem: commerce.engine
    message_types:
      - catalog.product.changed
      - catalog.product.tombstone
    # commerce.engine NO consume catalog.product.snapshot — ese es para Analytics

  - subsystem: analytics
    message_types:
      - catalog.product.snapshot
```

Esto tiene consecuencias directas:

- Un cambio en el schema de `catalog.product.snapshot` no requiere que `commerce.engine` adapte nada.
- El Registry puede generar automáticamente una matriz de dependencias exacta.
- Un consumidor puede migrar a una nueva versión de un message_type de forma independiente de otros consumidores del mismo contrato.

---

## 9. Consecuencias positivas

- Cada message_type tiene su propio schema, su propia versión y sus propias garantías. Los cambios son quirúrgicos.
- Los consumidores están acoplados a mensajes específicos, no a contratos completos.
- La separación `interaction` / `transport` permite cambiar el mecanismo de entrega (de queue a HTTP) sin que sea un breaking change semántico.
- El modelo es exportable a AsyncAPI para generación automática de documentación y SDKs.
- La definición formal de "contrato" (Amendment C) previene la proliferación de contratos de un solo mensaje.

---

## 10. Consecuencias negativas y riesgos

- Los cuatro contratos draft actuales deben migrarse antes de poder ser marcados `stable`. Esto es trabajo adicional, pero está justificado porque todos están en draft.
- El Meta-Contrato v2 tiene más campos que el v1. La curva de aprendizaje para agregar un nuevo contrato es mayor.
- El `meta-contract.schema.json` debe actualizarse para validar la nueva estructura. Hasta que eso ocurra, los contratos migrados no pueden validarse automáticamente.

---

## 11. Impacto en módulos

| Artefacto | Impacto |
|---|---|
| `contracts/meta-contract.yaml` | Migrar a estructura v2 con `message_types[]` |
| `contracts/schemas/meta-contract.schema.json` | Actualizar para validar la nueva estructura |
| `contracts/registry/*.yaml` (4 contratos) | Migrar de campos planos a `message_types[]` |
| `contracts/schemas/*.schema.json` (4 payloads) | Separar en schemas por message_type donde corresponda |
| `contracts/README.md` | Actualizar la definición de contrato (Amendment C) |
| `contracts/adr/README.md` | Registrar ADR-000 en el índice |

---

## 12. Criterios de aceptación arquitectónica

> Los criterios marcados **[Blocking]** deben cumplirse antes de que cualquier contrato
> pueda pasar de `draft` a `stable`. Los demás son requeridos antes del primer deploy de producción.

- [ ] **[Blocking]** Amendment C: la definición canónica de "contrato" aparece en `meta-contract.yaml` y en `contracts/README.md`.
- [ ] Amendment A: todos los `message_types[].id` en el Registry usan el formato `{domain}.{entity}.{action}`. Ningún id es relativo al contrato padre.
- [ ] Amendment B: no existe ningún campo `direction` ni `frequency` en el nivel raíz de ningún contrato del Registry.
- [ ] El campo `consumers` en cada contrato usa la estructura objeto con `subsystem` y `message_types[]`. Ningún contrato tiene consumers como lista plana de strings.
- [ ] Al menos `catalog.product-knowledge.v1.yaml` migrado a la estructura v2 antes de migrar los restantes (piloto de validación).
- [ ] El `meta-contract.schema.json` actualizado rechaza contratos con la estructura v1 (`direction`, `frequency`, `schema_ref` en nivel raíz).
- [ ] Amendment D: `contracts/README.md` incluye la tabla de mapeo eGarage → AsyncAPI.

---

## 13. Plan de transición

**Paso 1 — Este ADR en `Accepted`.** ✓ Completado.

**Paso 2 — Actualizar `meta-contract.yaml`.**
Reescribir la plantilla con la estructura v2. `message_types[]` reemplaza `direction`, `frequency` y `schema_ref`.

**Paso 3 — Actualizar `meta-contract.schema.json`.**
Fase conservadora: mantener `direction`, `frequency`, `schema_ref` como campos opcionales con `description: "DEPRECATED"`. El validador emite advertencia si están presentes, no error. Esto protege los contratos existentes durante la migración.
Una vez migrados todos los contratos del Registry: eliminar los campos deprecated del schema.

**Paso 4 — Migrar `catalog.product-knowledge.v1.yaml` como piloto.**
Es el contrato más complejo (tres message_types). Si CI pasa aquí, los restantes son directos.

**Paso 5 — Migrar los tres contratos restantes.**
`inventory.stock.v1`, `tax.policy.v1`, `identity.profile.v1`.

**Paso 6 — Separar schemas de payload por message_type donde corresponda.**
`catalog.product-knowledge.v1.schema.json` se divide. Contratos con un solo message_type pueden conservar un único schema.

**Paso 7 — Eliminar campos deprecated del schema.**
Una vez que ningún YAML del Registry los use. Emitir error (no advertencia) a partir de este punto.

**Paso 8 — Actualizar `contracts/README.md`.**
Incorporar la definición canónica de contrato (Amendment C) y la tabla de mapeo AsyncAPI (Amendment D).

---

## 14. Evidencia y referencias

- ADR-002 (Catalog Publication Trigger) — reveló la limitación del modelo plano al definir el outbox con tres tipos de mensaje distintos.
- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- AsyncAPI Specification 3.x — [asyncapi.com/docs/reference/specification/v3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0).
- CloudEvents Specification — modelo de message_types con identificadores globalmente únicos.
- Enterprise Integration Patterns (Hohpe & Woolf) — separación entre Message Channel (transport) y Message (interaction).
