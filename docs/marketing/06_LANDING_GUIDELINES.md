# Landing Guidelines — eGarage

> El visitante nunca debe preguntarse: ¿Qué hace este software?
> Debe entenderlo en cinco segundos.

---

## Estructura de una landing de producto

Orden fijo. No reordenar sin razón de conversión documentada.

```
1.  Hero          → H1 + H2 + CTA + social proof inmediato
2.  Platform stats → 4 estadísticas globales de la plataforma
3.  Rubro scenes   → 4 fotografías (taller / repuestos / desarme / carwash)
4.  Rubro selector → Cards de registro por tipo de negocio
5.  Features       → 3-6 beneficios concretos (no funcionalidades)
6.  Market insight → Dato local del mercado + contexto
7.  Social proof   → Estadísticas del mercado local
8.  Story          → El día del negocio (timeline)
9.  Screenshots    → Capturas reales del producto
10. Pricing        → Planes y precios (si aplica)
11. FAQ            → 5-8 preguntas reales de clientes
12. CTA final      → Repetir hero simplificado
13. Footer         → Links + país + legal
```

---

## Hero

### Copy obligatorio

```
H1: La plataforma para hacer crecer tu negocio automotriz.
H2: Controla tu taller, casa de repuestos, desarmaduría o carwash desde cualquier lugar.
CTA: Comenzar gratis
Subtext: 30 días • Sin tarjeta • Configuración en minutos
```

### Reglas del hero

- H1 nunca supera 12 palabras.
- H2 complementa, no repite. Máximo 20 palabras.
- Un solo CTA primario. El CTA secundario (si existe) es un enlace de texto, nunca un botón igual.
- El subtext elimina la fricción más común: "¿me van a cobrar?", "¿es difícil?".
- No poner precio en el hero. No poner funcionalidades en el hero.

---

## Adaptación por país

El copy del hero se localiza por país pero mantiene la misma estructura.
La localización NO es traducción literal — es adaptación al contexto del mercado.

Fuente: `taller/welcome_config.py` → `get_config(country, lang)`:
- `hero_headline`: sobrescribe el global si el país tiene versión local
- `hero_subline`: ídem
- `terminology`: 3 términos locales mostrados como pills bajo el subtítulo

---

## Rubro cards

Máximo 3 cards en el selector principal.
El orden depende del `priority_rubro` configurado por país.
Cada card lleva a `/signup/?rubro={slug}` para pre-configurar el onboarding.

---

## Features

- Máximo 6 features por sección.
- Cada feature: ícono + título (beneficio) + descripción (1-2 líneas).
- El título es el beneficio, no la funcionalidad.
  - ✓ "Nunca pierdas el historial de un vehículo"
  - ✗ "Módulo de órdenes de trabajo"

---

## Screenshots

- Solo capturas reales del producto. No mockups.
- Marco: bordes redondeados, sombra sutil, sin marcos de teléfono/laptop complicados.
- Siempre mostrar datos representativos, no datos de prueba vacíos.
- Si hay datos sensibles, usar datos ficticios pero realistas.
- Tablet y celular siempre muestran eGarage. Nunca pantalla en blanco.

---

## CTAs en la página

| Posición | CTA | Estilo |
|----------|-----|--------|
| Hero | Comenzar gratis | Botón primario grande |
| Rubro selector | implícito en el card | Card clickeable |
| Mid-page | Comenzar gratis | Botón primario |
| FAQ | Ver precios / Comenzar gratis | Botón secundario |
| Footer | Comenzar gratis | Link de texto |

Nunca más de un botón primario visible en el viewport al mismo tiempo.

---

## Performance

- LCP objetivo: < 2.5s
- CLS: < 0.1
- Imágenes hero: formato WebP, max 300KB, `loading="eager"` solo en hero, `loading="lazy"` en el resto.
- Fuentes: `font-display: swap`, preload de las 2 fuentes principales.
- No cargar librerías de animación hasta que el hero sea visible (lazy init AOS).

---

## Checklist antes de publicar una landing

- [ ] El H1 describe un beneficio, no el software.
- [ ] El visitante entiende qué es eGarage sin bajar el scroll.
- [ ] Hay al menos una fotografía con personas reales.
- [ ] El CTA principal dice "Comenzar gratis" (o equivalente local aprobado).
- [ ] El subtext "30 días • Sin tarjeta • Configuración en minutos" está presente.
- [ ] Los términos locales (terminology pills) están correctos para el país.
- [ ] Ninguna imagen supera 400KB.
- [ ] No hay texto sobre imagen sin overlay de legibilidad.
- [ ] Mobile: el H1 es legible sin zoom y el CTA es alcanzable con el pulgar.
- [ ] El copy fue validado contra `COPY_GUIDELINES.md`.
- [ ] Las imágenes fueron validadas contra `PHOTO_GUIDELINES.md`.
