# Marketing Architecture — eGarage

> Leer este documento primero. Explica qué existe, cómo se relaciona y en qué orden usarlo.

---

## Por qué existe esta carpeta

eGarage opera en 11 países. Genera landings, imágenes, campañas, emails y contenido social.
Sin un sistema documentado, cada pieza de marketing es una decisión individual.
Con este sistema, cada pieza es una consecuencia de reglas ya tomadas.

**Objetivo:** que cualquier persona —desarrollador, diseñador, redactor, IA— pueda producir
material de eGarage sin preguntar qué está bien y qué está mal.

---

## Índice de documentos

```
docs/marketing/
│
├── 00_MARKETING_ARCHITECTURE.md   ← este documento
├── 01_PRODUCT_NARRATIVE.md        ← el héroe, el guía, el enemigo, la transformación
├── 02_BRAND_GUIDE.md              ← misión, promesa, personalidad, visión
├── 03_COPY_GUIDELINES.md          ← vocabulario, tono por canal, frases aprobadas
├── 04_DESIGN_SYSTEM.md            ← tokens, componentes, espaciado, sombras, radios
├── 05_PHOTO_GUIDELINES.md         ← estilo fotográfico, Do/Don't por escena
├── 06_LANDING_GUIDELINES.md       ← estructura de página, hero copy, checklist
├── 07_CONVERSION_GUIDELINES.md    ← 8 principios de conversión
├── 08_ASSET_PIPELINE.md           ← flujo técnico Master→Exports→Web, comandos
├── 09_SUCCESS_METRICS.md          ← métricas de producto y de marca
├── 10_CHECKLIST.md                ← verificación completa antes de publicar
├── 11_AI_PLAYBOOK.md              ← instrucciones para IA por tipo de tarea
│
└── adr/
    ├── ADR-001-photography.md             ← por qué fotografías reales
    ├── ADR-002-benefits-over-features.md  ← por qué beneficios antes que funcionalidades
    ├── ADR-003-global-scenes-local-heroes.md ← por qué escenas globales y hero localizado
    └── ADR-004-dark-welcome.md            ← por qué dark mode en bienvenidas y light en producto
```

---

## Árbol de dependencias

```
01_PRODUCT_NARRATIVE        ← la historia que lo gobierna todo
        │
        ▼
02_BRAND_GUIDE              ← quiénes somos, qué prometemos, cómo hablamos
        │
        ├──▶ 03_COPY_GUIDELINES       ← vocabulario, tono, frases aprobadas
        │           │
        │           └──▶ 06_LANDING_GUIDELINES   ← estructura, hero copy, UX
        │
        ├──▶ 04_DESIGN_SYSTEM         ← tokens, componentes, espaciado
        │           │
        │           └──▶ 06_LANDING_GUIDELINES   (también depende de aquí)
        │
        ├──▶ 05_PHOTO_GUIDELINES      ← estilo fotográfico, Do/Don't
        │           │
        │           └──▶ 08_ASSET_PIPELINE       ← flujo técnico de producción
        │
        └──▶ 07_CONVERSION_GUIDELINES ← principios que gobiernan toda decisión de UX

09_SUCCESS_METRICS           ← mide si todo lo anterior está funcionando
10_CHECKLIST                 ← valida antes de publicar
11_AI_PLAYBOOK               ← traduce todo lo anterior en instrucciones para IA

adr/                         ← registra por qué se tomaron las decisiones clave
```

**Regla de lectura:**
Un nodo solo puede contradecir a sus hijos. Un hijo nunca contradice a su padre.
Si hay conflicto entre documentos, gana el más alto en la jerarquía.

---

## Qué leer según tu rol

| Rol | Documentos obligatorios | Referencia |
|-----|------------------------|------------|
| **Nuevo en el proyecto** | 00 → 01 → 02 | todos |
| **Redactor / copy** | 01 → 02 → 03 | 06, 11 |
| **Diseñador web** | 02 → 04 → 07 | 06, 11 |
| **Fotógrafo / IA de imágenes** | 02 → 05 → 11 | 08 |
| **Desarrollador de landing** | 04 → 06 → 07 | 10, 11 |
| **Al generar con IA** | 11 → el doc específico de la tarea | — |
| **Antes de publicar cualquier cosa** | 10 | — |

---

## Flujo completo: de la idea a la publicación

```
1. Narrativa
   └─ validar contra 01_PRODUCT_NARRATIVE (¿el dueño es el héroe?)
   └─ validar contra 02_BRAND_GUIDE (¿encaja con la personalidad?)

2. Copy
   └─ redactar según 03_COPY_GUIDELINES (vocabulario, tono)
   └─ aplicar estructura de 06_LANDING_GUIDELINES (H1/H2/CTA)

3. Diseño visual
   └─ aplicar tokens de 04_DESIGN_SYSTEM (colores, radios, sombras, spacing)
   └─ validar contra 07_CONVERSION_GUIDELINES (los 8 principios)

4. Imágenes
   └─ brief de arte según 05_PHOTO_GUIDELINES (Do/Don't por escena)
   └─ producción y exportación según 08_ASSET_PIPELINE

5. Implementación
   └─ código sigue 04_DESIGN_SYSTEM y 06_LANDING_GUIDELINES
   └─ si usas IA: leer 11_AI_PLAYBOOK antes de generar

6. Revisión final
   └─ pasar 10_CHECKLIST completo sin excepciones
   └─ medir contra 09_SUCCESS_METRICS al lanzar
```

---

## Principio de no duplicación

**Si un dato ya existe en el código, la documentación lo referencia — no lo repite.**

Ejemplos:
- El brief de arte de cada escena está en `taller/welcome_config.py → HERO_RUBRO_SCENES`. Los documentos apuntan allí.
- Los colores por país están en `WELCOME_CONFIG[(country, lang)]["theme"]`. Los documentos dicen dónde buscarlo.
- Las frases de localización están en `terminology`. Los documentos explican el patrón, no los valores.

Esto garantiza que hay una sola fuente de verdad. Si cambia el código, no hay documentos desactualizados.

---

## Regla operativa

> Ningún cambio en la landing, ninguna imagen nueva y ninguna campaña de marketing
> se aprueba sin cumplir estos documentos.

Esta regla convierte estos archivos de notas en el manual operativo de la marca.
Si un documento dice algo diferente a lo que se está haciendo, el documento tiene la razón.
Si el documento está equivocado, se actualiza el documento — no la excepción.

---

## Sobre los ADRs de marketing

Los ADRs (`adr/`) registran las decisiones importantes que tomamos y por qué.
No son opiniones. Son decisiones tomadas con argumentos verificables.

**Cuándo crear un nuevo ADR:**
- Al tomar una decisión que va contra la convención del mercado
- Al elegir una opción sobre otra cuando hay argumentos en ambos lados
- Cuando alguien en el futuro podría preguntarse "¿por qué hicimos esto así?"

**Cuándo NO crear un ADR:**
- Para convenciones obvias que todo el mundo comparte
- Para decisiones de implementación que el código ya documenta

---

## Versiones

| Versión | Fecha | Cambio principal |
|---------|-------|-----------------|
| 1.0 | 2026-08-05 | Estructura inicial basada en Brand Guide v1.0 |
| 1.1 | 2026-08-06 | Estructura numerada, Product Narrative, ADRs, Success Metrics, AI Playbook |
