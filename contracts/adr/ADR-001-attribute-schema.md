# ADR-001 — Attribute Schema

- **Estado:** Accepted with amendments
- **Fecha:** 2026-07-30
- **Revisado:** 2026-07-30
- **Decisores:** Mauricio Alvarado
- **Contratos afectados:** `catalog.product-knowledge.v1`
- **Sustituye:** —
- **Sustituido por:** —

---

## 1. Dueño del dato

**ERP Core** (`erp.catalog`) es el único propietario y escritor del esquema de atributos. Ningún Tenant, Template ni subsistema consumidor puede crear, modificar o eliminar definiciones de atributos directamente.

---

## 2. Contexto y problema

Commerce Engine necesita conocer qué atributos tienen los productos del catálogo para indexarlos, filtrarlos, ordenarlos y construir facetas de búsqueda. Sin un esquema formal, cada subsistema interpretaría los atributos de forma diferente, generando inconsistencias entre la búsqueda, el catálogo y el filtrado.

El problema tiene tres aristas:

- **Tipado**: ¿`vehicle.year` es un entero, un string o un rango?
- **Cardinalidad**: ¿un producto puede tener múltiples marcas o solo una?
- **Descubrimiento**: ¿cómo sabe Commerce Engine cuáles atributos existen sin consultar los modelos Django del ERP?

La solución debe ser independiente del modelo de datos interno de ERP y no debe requerir acceso a código del ERP para funcionar.

---

## 3. Capa responsable

| Subsistema | Responsabilidad |
|---|---|
| `erp.catalog` | Define, valida y publica las definiciones de atributos |
| `Capability Profile` | Declara qué atributos son relevantes para el vertical (sin crear tipos) |
| `commerce.engine` | Indexa atributos, ejecuta búsquedas, filtros y facetas |
| `analytics` | Puede usar atributos como dimensiones de análisis |

---

## 4. Contratos utilizados

- `catalog.product-knowledge.v1` — el esquema se transporta como campo `attribute_schema` dentro del payload de este contrato.

---

## 5. Opciones consideradas

### Opción A — Columnas dinámicas creadas por Tenant

El Tenant define sus propios atributos desde una UI de administración. ERP almacena valores en una tabla de clave-valor genérica.

**Ventaja:** máxima flexibilidad para el Tenant.

**Desventaja:** ningún subsistema puede validar los atributos. Commerce Engine no puede optimizar índices sin saber los tipos. Un Tenant puede crear atributos inconsistentes que rompan la búsqueda. No es versionable.

### Opción B — Código ejecutable dentro del Template

El Template Casa de Repuestos incluye un parser que interpreta el texto libre del usuario y extrae atributos estructurados.

**Ventaja:** máxima expresividad.

**Desventaja:** el Template ejecuta código, lo que viola el Principio de Autonomía. Un error en el código del Template puede romper todo el Commerce Engine. No se puede validar automáticamente.

### Opción C — Esquema declarativo y versionado publicado por ERP Core (elegida)

ERP Core publica un `attribute_schema` como parte del Product Knowledge Contract. El esquema define cada atributo con nombre canónico, tipo, cardinalidad y propiedades de indexación. El Capability Profile declara cuáles de esos atributos usa cada vertical. Commerce Engine indexa según el esquema recibido.

**Ventaja:** versionable, validable automáticamente, no ejecutable, reutilizable por múltiples verticals, sin acoplamiento al modelo Django del ERP.

**Desventaja:** agregar un atributo nuevo requiere un cambio en `erp.catalog`, no puede hacerlo el Tenant solo. Mayor overhead inicial para cada nuevo tipo de atributo.

---

## 6. Decisión

**Opción C.** Esquema declarativo, versionado y exportado por ERP Core como campo `attribute_schema` dentro del payload de `catalog.product-knowledge.v1`.

Modelo de definición de atributo:

```yaml
attribute_schema:
  version: "1.0.0"
  definitions:
    - key: vehicle.brand
      data_type: string
      cardinality: single
      nullable: true
      searchable: true
      filterable: true
      sortable: false
      facetable: true
      unit: null

    - key: vehicle.year_from
      data_type: integer
      cardinality: single
      nullable: true
      searchable: false
      filterable: true
      sortable: true
      facetable: false
      unit: year
```

Tipos iniciales permitidos: `string`, `integer`, `decimal`, `boolean`, `date`, `datetime`, `enum`, `reference`.

Cardinalidades permitidas: `single`, `multiple`.

---

## 7. Consecuencias positivas

- Commerce Engine puede construir índices optimizados por tipo de dato.
- El Capability Profile puede declarar facetas sin ejecutar código.
- El esquema es validable en CI antes de llegar a producción.
- Analytics puede usar los atributos como dimensiones sin conocer el modelo ERP.
- Un cambio de esquema tiene versión semver, por lo que los consumidores pueden adaptarse de forma controlada.

---

## 8. Consecuencias negativas y riesgos

- Agregar un nuevo tipo de atributo requiere un cambio en `erp.catalog` y una nueva publicación del contrato.
- Un Tenant no puede añadir atributos propios sin involucrar a la plataforma.
- Si `erp.catalog` no publica el esquema actualizado, Commerce Engine opera con el último conocido y puede rechazar productos que usen atributos nuevos.

---

## 9. Impacto en módulos

| Módulo | Impacto |
|---|---|
| `erp.catalog` | Debe generar y mantener el `attribute_schema` versionado |
| `commerce.engine` | Debe indexar atributos según el esquema recibido; rechazar atributos desconocidos |
| `analytics` | Puede usar los atributos como dimensiones |
| `Capability Profile` | Declara cuáles atributos usa cada vertical (subset del esquema) |

---

## 10. Principios protegidos o modificados

- **Principio de Autonomía**: Commerce Engine no accede a los modelos Django de ERP. Solo consume el contrato.
- **Capability Profile no ejecuta código**: el Template declara, no transforma.
- **write_authority**: solo `erp.catalog` puede definir y publicar el esquema.

---

## 11. Qué ocurre si el componente desaparece

Si `erp.catalog` deja de publicar el `attribute_schema`:

- Commerce Engine sigue funcionando con el último esquema conocido.
- Los productos existentes continúan siendo buscables y filtrables.
- Los productos nuevos que usen atributos no declarados en el esquema cacheado serán rechazados por Commerce Engine hasta que se restablezca la publicación.
- Analytics puede seguir usando las dimensiones del esquema anterior.

---

## 12. Criterios de aceptación arquitectónica

- [ ] `attribute_schema` tiene versión semver independiente del esquema del contrato padre.
- [ ] Todo producto publicado tiene atributos que respetan el esquema (`data_type` y `cardinality` correctos).
- [ ] Commerce Engine rechaza (con log de error, no con excepción fatal) productos con atributos desconocidos.
- [ ] Un atributo marcado `facetable: true` aparece como faceta en la búsqueda del storefront.
- [ ] Un atributo marcado `sortable: true` puede usarse como criterio de ordenamiento.
- [ ] Agregar un atributo opcional al esquema no requiere migración ni reindexación completa.

---

## 13. Plan de transición

**Fase 1 (inicial):** el esquema se define manualmente como configuración en `erp.catalog`. Atributos iniciales para Casa de Repuestos: `vehicle.brand`, `vehicle.model`, `vehicle.year_from`, `vehicle.year_to`, `part.category`, `part.side`.

**Fase 2:** interfaz de administración para agregar atributos sin deploys. Validación automática del esquema en CI.

**Fase 3:** extensión a otros verticals (Desarmaduría, Taller), con sus propios subsets del esquema.

---

## 14. Evidencia y referencias

- Conversación de arquitectura eGarage Commerce v1.0, julio 2026.
- Patrón Entity-Attribute-Value y sus alternativas: [Martin Fowler — Schema-less databases](https://martinfowler.com/articles/schemaless/).
- Elasticsearch mapping types como referencia para tipado de atributos de búsqueda.

---

## 15. Historial de revisión

### 2026-07-30 — Revisión arquitectónica inicial

**Resultado:** Accepted with amendments

**Decisión aceptada:** Opción C (esquema declarativo y versionado, propiedad exclusiva de `erp.catalog`). La argumentación de las secciones 5 y 6 es correcta. Los principios protegidos (Autonomía, write_authority) son consistentes con la arquitectura eGarage.

**Amendments incorporados en esta revisión:**

- **Amendment 1 (aplicado):** El enum de tipos en `catalog.product-knowledge.v1.schema.json` fue actualizado al conjunto canónico de 8 tipos (`string`, `integer`, `decimal`, `boolean`, `date`, `datetime`, `enum`, `reference`). La propiedad `data_type` reemplaza a `type` para el tipo semántico del atributo. `type` queda reservado para palabras estructurales de JSON Schema.

- **Amendment 2 (aplicado):** La representación de `attribute_schema` fue reescrita: de `additionalProperties` a una estructura `version` + `definitions[]`. Se incorporaron los campos `cardinality`, `nullable`, `searchable`, `filterable`, `sortable`, `facetable` y `unit` como parte del contrato formal. El campo `version` con patrón SemVer permite a los consumidores detectar cambios de esquema sin bumps del contrato padre.

**Amendments pendientes — bloquean el paso a Stable:**

- **Amendment 3 (abierto):** El tipo `reference` está declarado en el enum de `data_type` pero su semántica de resolución no está definida. Debe especificarse: entidad referenciada, formato del valor, comportamiento ante eliminación de la entidad, y si Commerce Engine resuelve el display name o solo indexa el identificador. Alternativa: excluir `reference` de v1 y reservarlo para un ADR posterior.

- **Amendment 4 (abierto):** La estrategia i18n del campo `label` no está decidida. El tipo actual (`string | null`) es temporal. Opciones: translation key, mapa por locale `{locale: string}`, o bare string para tenants monoidioma. Debe resolverse antes de Stable dado que eGarage ya tiene locale files para `es`, `en` y `pt_BR`.

**Estado del contrato:** `catalog.product-knowledge.v1` permanece en `draft`. No puede avanzar a `Stable` hasta que Amendments 3 y 4 sean cerrados y los criterios de aceptación del §12 sean verificables automáticamente.

**Próximo ADR revisable:** ADR-002 (Publication Trigger) puede abrirse en paralelo.
