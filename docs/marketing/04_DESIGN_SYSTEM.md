# Design System — eGarage Marketing

> Todo componente tiene una sola respuesta correcta para cada propiedad.
> La consistencia es el resultado de no decidir dos veces lo mismo.

---

## Tokens base

### Colores

| Token | Valor | Rol |
|-------|-------|-----|
| `--color-bg` | `#FFFFFF` | Fondo principal |
| `--color-text` | `#111827` | Texto principal |
| `--color-text-muted` | `#6B7280` | Texto secundario, captions |
| `--color-text-subtle` | `#9CA3AF` | Labels, placeholders |
| `--color-brand` | `#00f0ff` | Color de marca (turquesa eGarage) |
| `--color-brand-dark` | `#0891b2` | Variante oscura para hover |
| `--color-success` | `#16a34a` | Confirmaciones, badges positivos |
| `--color-error` | `#dc2626` | Alertas, validaciones |
| `--color-border` | `#E5E7EB` | Bordes de cards y divisores |
| `--color-surface` | `#F9FAFB` | Fondos de sección alternos |

**Uso del color de marca:** aparece en un solo elemento por sección.
Nunca saturar la vista con turquesa. El blanco es el color dominante.

> Para las páginas de bienvenida en dark mode (`#0a0c10`), los tokens CSS son
> `--c1-rgb` y `--c2-rgb` inyectados por vista. Esos contextos tienen sus propias
> reglas — ver `taller/welcome_config.py` → campo `theme`.

### Tipografía

| Familia | Rol | Pesos |
|---------|-----|-------|
| Inter | Principal | 400, 500, 600, 700 |
| Plus Jakarta Sans | Alternativa | 400, 600, 700 |

**Nunca usar Orbitron, Exo 2 ni tipografías futuristas en landings de producto.**
Esas fuentes están reservadas para las páginas de bienvenida marketing (contexto dark-mode).

#### Escala tipográfica

| Elemento | Mobile | Desktop | Peso |
|----------|--------|---------|------|
| H1 hero | 36px | 56–72px | 700 |
| H2 sección | 28px | 36–40px | 700 |
| H3 subsección | 22px | 24px | 600 |
| Body largo | 16px | 18px | 400 |
| Body corto | 15px | 16px | 400 |
| Caption / label | 12px | 13px | 500 |
| CTA button | 16px | 17px | 600 |
| Eyebrow (sobre H2) | 11px | 12px | 600, uppercase, tracking 0.12em |

Nunca usar `font-size` menor a 12px en elementos visibles.

---

## Espaciado

El sistema es de 8px base. Todos los valores son múltiplos de 8.

| Token | Valor | Uso típico |
|-------|-------|------------|
| `space-2` | 8px | Gap mínimo entre elementos inline |
| `space-4` | 16px | Padding interno de badges y pills |
| `space-6` | 24px | Gap entre cards |
| `space-8` | 32px | Padding interno de cards |
| `space-10` | 40px | Gap de grid de features |
| `space-12` | 48px | Separación entre sección y su título |
| `space-20` | 80px | Padding vertical mínimo de sección |
| `space-24` | 96px | Padding vertical estándar de sección |
| `space-32` | 128px | Padding vertical del hero |

**El espacio blanco es parte del diseño.** Una sección con menos de 80px vertical
en desktop se siente abarrotada. No rellenar el espacio — usarlo.

---

## Layout

| Propiedad | Valor |
|-----------|-------|
| Container max-width | 1440px |
| Content max-width (texto) | 768px |
| Content max-width (grid + imagen) | 1152px |
| Grid | 12 columnas |
| Grid gap | 32px |
| Padding lateral mobile | 16px |
| Padding lateral tablet | 32px |
| Padding lateral desktop | 48px |

---

## Border radius

Solo tres valores. Sin excepciones.

| Token | Valor | Uso |
|-------|-------|-----|
| `radius-md` | 16px | Inputs, badges, pills |
| `radius-lg` | 24px | Cards, modales |
| `radius-xl` | 32px | Imágenes hero, CTA grandes |

---

## Sombras

Solo dos. Sin excepciones.

| Token | CSS | Uso |
|-------|-----|-----|
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)` | Cards en reposo, inputs |
| `shadow-lg` | `0 10px 40px rgba(0,0,0,0.10), 0 4px 16px rgba(0,0,0,0.06)` | Cards en hover, modales |

Nunca usar `box-shadow` y `border` al mismo tiempo en el mismo elemento.
En hover: pasar de `shadow-sm` a `shadow-lg` con `transition: box-shadow 200ms ease-out`.

---

## Componentes

### Hero
```
padding-top:    128px
padding-bottom: 96px
max-width:      1152px
H1:             font-size 56px / weight 700 / color #111827
H2:             font-size 22px / weight 400 / color #6B7280 / margin-top 16px
CTA gap:        16px
subtext:        font-size 14px / color #9CA3AF / margin-top 12px
```
Un solo CTA primario. Si hay CTA secundario, es un `<a>` con `text-decoration: underline`, nunca un botón.

### Card
```
border-radius:  24px
padding:        32px
background:     #FFFFFF
border:         1px solid #E5E7EB
shadow:         shadow-sm
hover-shadow:   shadow-lg
transition:     200ms ease-out (shadow + transform)
hover-transform: translateY(-2px)
```

### CTA Button (primario)
```
height:         56px
padding:        0 32px
border-radius:  16px
font-size:      17px
font-weight:    600
background:     #00f0ff  (o color de marca del país)
color:          #111827
hover-bg:       #0891b2
transition:     150ms ease-out
```

### CTA Button (secundario)
```
height:         48px
padding:        0 24px
border-radius:  16px
font-size:      15px
font-weight:    500
background:     transparent
border:         1.5px solid #E5E7EB
color:          #374151
hover-border:   #9CA3AF
```

### Feature card
```
icon-size:      40px
icon-color:     --color-brand
title:          font-size 18px / weight 600 / color #111827
body:           font-size 15px / weight 400 / color #6B7280 / line-height 1.6
gap interno:    16px
max por fila:   3 (desktop) / 1 (mobile)
```

### Badge / pill
```
height:         28px
padding:        0 12px
border-radius:  16px
font-size:      12px
font-weight:    600
text-transform: uppercase
letter-spacing: 0.06em
```

### Statistic
```
valor:          font-size 48px / weight 700 / color #111827 / font-family Inter
label:          font-size 14px / weight 500 / color #6B7280 / margin-top 4px
max por fila:   4 (desktop) / 2 (mobile)
```

### Screenshot
```
border-radius:  24px
shadow:         shadow-lg
border:         1px solid #E5E7EB
overflow:       hidden
max-width:      880px
margin:         0 auto
```
Solo capturas reales del producto. No mockups fabricados.

### FAQ (accordion)
```
border-top:     1px solid #E5E7EB (primer ítem)
item border-bottom: 1px solid #E5E7EB
pregunta:       font-size 17px / weight 600 / color #111827 / padding 20px 0
respuesta:      font-size 15px / weight 400 / color #6B7280 / padding-bottom 20px
máximo:         8 preguntas
```

### Timeline
```
line-color:     #E5E7EB
dot-size:       12px
dot-color:      --color-brand
step-gap:       32px
label:          font-size 15px / weight 500 / color #374151
```

### Footer
```
background:     #F9FAFB
border-top:     1px solid #E5E7EB
padding:        48px 0
font-size:      14px / color #6B7280
Sin elementos decorativos. Solo links, país y legal.
```

---

## Animaciones

Solo estas cuatro. Sin excepciones.

| Animación | Propósito | Duración | Easing |
|-----------|-----------|----------|--------|
| `fade` | Entrada al viewport | 400ms | ease-out |
| `slide` | Transición lateral (carrusel) | 300ms | ease-in-out |
| `hover` | Botones y cards | 150–200ms | ease-out |
| `counter` | Estadísticas numéricas | 1200ms | ease-out |

- Nunca animar más de un elemento al mismo tiempo en la misma área visual.
- Las animaciones no bloquean la lectura. El contenido es visible inmediatamente, la animación es un refuerzo.
- No cargar librerías de animación hasta que el hero sea interactivo (lazy init).

---

## Íconos

| Parámetro | Valor |
|-----------|-------|
| Sistema | Heroicons o Lucide (consistencia en todo el producto) |
| Tamaño inline | 20px |
| Tamaño UI | 24px |
| Tamaño feature card | 40px |
| Color | Heredado del texto o `--color-brand`. Sin colores propios por ícono. |
| Stroke width | 1.5px |

---

## Performance

| Métrica | Objetivo |
|---------|----------|
| LCP | < 2.5s |
| CLS | < 0.1 |
| FID / INP | < 200ms |
| Imagen hero | WebP, < 300KB, `loading="eager"` |
| Demás imágenes | WebP, `loading="lazy"`, `decoding="async"` |
| Fuentes | `font-display: swap`, preload de las 2 principales |
