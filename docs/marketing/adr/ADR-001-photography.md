# ADR-001 — Fotografías reales, nunca renders ni mockups

**Estado:** Aprobado
**Fecha:** 2026-08-05
**Autores:** Mauricio Alvarado

---

## Contexto

Al construir los activos visuales de las páginas de bienvenida, surgió la decisión de elegir entre:

1. **Renders / ilustraciones 3D** — control total del resultado, sin necesidad de sesión fotográfica
2. **Mockups con stock photos** — rápidos y económicos, pero genéricos
3. **Fotografías documentales reales** — alta inversión inicial, pero autenticidad total

El target de eGarage son dueños de talleres mecánicos, casas de repuestos y desarmadurías en Latinoamérica y USA. Son personas con mucha experiencia en su rubro que reconocen inmediatamente cuando algo se ve "irreal" o de publicidad corporativa.

---

## Decisión

**Fotografías documentales reales siempre. Sin excepciones.**

Esto incluye:
- Las 5 escenas de rubro globales (Sprint B1)
- Los heroes por país (Sprint B2)
- Todo el material para redes sociales y anuncios

---

## Razones

### 1. El cliente se reconoce o no se reconoce en la imagen
Una foto de un taller real con un técnico real y un auto común dice:
*"Este software es para negocios como el mío."*

Un render o stock photo dice:
*"Este software es para una empresa diferente a la mía."*

La identificación emocional ocurre en menos de 500ms. No hay texto que la supla.

### 2. La autenticidad construye confianza
El sector automotriz es desconfiado por naturaleza — los clientes llegan con miedo a ser estafados.
Un material visual que se ve real transmite que la empresa detrás también es real.

### 3. Los renders envejecen; las fotografías buenas, no
Un render bien hecho en 2026 parece desactualizado en 2028.
Una fotografía documental de 2026 sigue siendo válida en 2032.

### 4. Los renders invitan a comparar con la realidad
Si un render muestra un taller impecable y el cliente tiene un taller normal,
la comparación genera distancia. La fotografía real evita esa trampa.

---

## Consecuencias

- **Mayor inversión inicial:** las 5 escenas de Sprint B1 requieren producción fotográfica real o generación IA con brief preciso.
- **Brief de arte obligatorio:** cada imagen requiere el brief completo de `HERO_RUBRO_SCENES` en `welcome_config.py`.
- **No hay atajos:** si no existe la fotografía aprobada, se usa `placeholder.webp`. Nunca un render de emergencia.
- **Revisión antes de publicar:** toda imagen pasa el Do/Don't de `05_PHOTO_GUIDELINES.md`.

---

## Alternativa considerada y descartada

**Ilustraciones de estilo flat/isométrico** (como Notion, Linear):
Elegante para productos B2B de software. Incorrecto para eGarage porque el cliente
no trabaja con abstracciones — trabaja con autos, motores y herramientas reales.
Una ilustración crea distancia con su realidad cotidiana.
