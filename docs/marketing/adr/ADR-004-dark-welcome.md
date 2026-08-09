# ADR-004 — Dark mode en páginas de bienvenida, light mode en el producto

**Estado:** Aprobado
**Fecha:** 2026-08-05
**Autores:** Mauricio Alvarado

---

## Contexto

eGarage tiene dos contextos visuales con propósitos distintos:

1. **Páginas de bienvenida** (`/mx/es/bienvenida/`, `/cl/es/bienvenida/`, etc.) — adquisición de nuevos clientes
2. **Producto** (dashboard, OTs, inventario, clientes) — uso diario por suscriptores

Al diseñar las páginas de bienvenida, surgió la pregunta: ¿deberían seguir el mismo sistema visual que el producto?

---

## Decisión

**Las páginas de bienvenida usan dark mode (`#0a0c10`). El producto usa light mode (`#FFFFFF`).**

Son sistemas visuales separados con propósitos distintos. No deben converger.

---

## Razones

### 1. Propósitos distintos requieren estados emocionales distintos

**Dark mode (bienvenida):**
Crea una atmósfera premium, tecnológica y aspiracional.
El visitante está evaluando, comparando, decidiendo.
El dark mode communica: *"esto es serio, esto es moderno, esto está hecho con cuidado"*.

**Light mode (producto):**
Crea claridad, legibilidad y confort para uso prolongado.
El suscriptor trabaja 4-8 horas con el sistema.
El light mode communica: *"esto es claro, esto es productivo, esto no cansa la vista"*.

### 2. La diferencia visual marca la transición de prospecto a cliente

Cuando el usuario registrado entra al producto por primera vez, el cambio de dark a light
es una señal clara de que "ya estoy adentro". El producto se siente distinto de la landing.
Eso es intencional: la landing vende la promesa, el producto la cumple.

### 3. El dark mode para marketing es una convención de productos premium

Stripe, Linear, Vercel, Planetscale — todos usan dark en sus landings y light en sus productos.
No seguimos la convención porque ellos lo hacen. La seguimos porque la razón detrás es correcta.

---

## Implementación técnica

### Tokens de color por contexto

**Dark (bienvenidas):**
```css
/* Inyectados desde welcome_config.py → theme */
--c1-rgb: R G B   /* color primario del país */
--c2-rgb: R G B   /* color de acento del país */
background: #0a0c10
```

**Light (producto):**
```css
/* Design System estándar */
--color-bg: #FFFFFF
--color-text: #111827
--color-brand: #00f0ff
```

### Tipografía por contexto

**Dark (bienvenidas):** Orbitron (futurista) para H1, Exo 2 para subtítulos — solo en este contexto.
**Light (producto):** Inter / Plus Jakarta Sans — nunca Orbitron en el producto.

Esta separación está documentada en `04_DESIGN_SYSTEM.md`:
> *"Nunca usar tipografías futuristas (Orbitron, Exo 2) en landings de producto.
> Esas fuentes están reservadas para las páginas de bienvenida marketing (contexto dark-mode)."*

### Personalización por país (solo en bienvenidas)

Cada país tiene su propia paleta en `WELCOME_CONFIG[(country, lang)]["theme"]`:
```python
"theme": {
    "primary": "#00f0ff",   # --c1-rgb
    "accent":  "#0891b2",   # --c2-rgb
    "badge":   "#38bdf8",   # badges y pills
}
```

El producto no tiene variación de color por país. Un solo sistema visual para todos.

---

## Consecuencias

- **Mantenimiento separado:** cambios en el Design System del producto no afectan las bienvenidas, y viceversa.
- **Brief de imágenes diferente:** las fotografías para las bienvenidas deben funcionar sobre fondo oscuro (overlay dark en las escenas). Las capturas del producto son sobre fondo blanco.
- **Restricción de componentes:** los glass-cards, el glow, las animaciones AOS del dark mode no deben filtrarse al producto.
- **Coherencia de marca:** aunque los colores son distintos, el turquesa de marca (`#00f0ff`) aparece en ambos contextos como el color de acción principal. Es el hilo visual que conecta adquisición y retención.

---

## Revisión futura

Esta decisión debería revisarse si:
- El producto migra a un modo oscuro opcional (en ese caso, usar los tokens del dark de bienvenida como punto de partida)
- El volumen de páginas de bienvenida justifica un sistema de componentes separado en código (actualmente comparten Tailwind)
