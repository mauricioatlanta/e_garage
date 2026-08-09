# ADR-002 — Beneficios antes que características

**Estado:** Aprobado
**Fecha:** 2026-08-05
**Autores:** Mauricio Alvarado

---

## Contexto

Al redactar el copy de las landings y el material de marketing, había dos opciones claras:

1. **Describir características** — "Módulo de órdenes de trabajo, inventario, CRM, reportes"
2. **Describir beneficios** — "Nunca pierdas el historial de un vehículo", "Encuentra cualquier repuesto en segundos"

La mayoría de los competidores en el espacio de software automotriz usa características.
Es la convención del mercado. Y es exactamente por eso que decidimos no seguirla.

---

## Decisión

**Siempre comunicar el beneficio primero. La característica, si aparece, es secundaria y está subordinada al beneficio.**

En la práctica:
- El H1 siempre describe un resultado, no una funcionalidad
- Las feature cards tienen título de beneficio, descripción de funcionalidad
- El vocabulario de características (módulo, inventario, CRM, ERP) está prohibido en copy de cara al cliente
- Los ADRs, documentación técnica y código pueden usar terminología técnica

---

## Razones

### 1. Los clientes no compran software. Compran resultados.
El dueño de un taller no necesita "un módulo de gestión de clientes".
Necesita que los clientes vuelvan. Eso es lo que compra.

### 2. Las características crean comparación. Los beneficios crean conexión.
Si digo "tenemos inventario", el cliente compara nuestra funcionalidad con la del competidor.
Si digo "encuentra cualquier repuesto en segundos", el cliente imagina su problema resuelto.
La imaginación de la solución genera deseo. La comparación de características genera análisis.

### 3. Diferenciación en un mercado saturado de funcionalidades
Todos los ERP automotrices listan las mismas características.
Ninguno habla de lo que el dueño del negocio gana en su vida.
Ese espacio está vacío y es nuestro.

### 4. Alineado con el Product Narrative
El Product Narrative (`01_PRODUCT_NARRATIVE.md`) define que el héroe es el dueño del negocio.
Si comunicamos características, estamos hablando del software (el guía).
Si comunicamos beneficios, estamos hablando del dueño (el héroe).
Características-first viola el marco narrativo central.

---

## Tabla de traducción permanente

| Característica (prohibida en copy) | Beneficio (lo que decimos) |
|------------------------------------|---------------------------|
| ERP automotriz | La plataforma para hacer crecer tu negocio |
| Módulo de OT | Nunca pierdas el historial de un vehículo |
| Gestión de inventario | Encuentra cualquier repuesto en segundos |
| CRM de clientes | Conoce cada cliente como si fuera el primero |
| Reportes en tiempo real | Sabe exactamente cómo va tu negocio hoy |
| Multi-sucursal | Controla todas tus sucursales desde un lugar |

Esta tabla vive también en `03_COPY_GUIDELINES.md` y en el contexto de cada sesión de IA.

---

## Consecuencias

- **Copy más difícil de escribir:** hablar de beneficios requiere entender profundamente al cliente. No se puede generar automáticamente sin ese contexto.
- **Requiere disciplina en revisiones:** cualquier pieza de copy debe ser auditada contra la tabla de traducción.
- **Riesgo de ser vago:** un beneficio mal escrito es una promesa vacía. "Crecer con confianza" es vago. "Encuentra cualquier repuesto en segundos" es concreto. El beneficio siempre debe ser específico y verificable.

---

## Excepción documentada

En documentación técnica, onboarding avanzado y comunicación con suscriptores que ya conocen el producto,
el uso de terminología técnica (OT, inventario, módulos) es correcto y esperado.
Esta regla aplica exclusivamente al material de adquisición (landings, ads, social, email de prospecto).
