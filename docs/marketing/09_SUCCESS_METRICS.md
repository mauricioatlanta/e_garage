# Success Metrics — eGarage Marketing

> Estas no son métricas de vanidad. Son señales de que el producto y la narrativa funcionan juntos.
> Si una métrica está consistentemente por debajo del objetivo, el sistema tiene un error de diseño — no de marketing.

---

## Principio de lectura

Cada métrica tiene una pregunta de diagnóstico detrás.
Si el objetivo no se cumple, la pregunta identifica dónde está el problema.

---

## Embudo de adquisición

| Etapa | Métrica | Objetivo | Si no se cumple, preguntar |
|-------|---------|----------|---------------------------|
| Atracción | Visitas a landing | — | (tráfico, no conversión) |
| Atención | Scroll depth > 50% | > 60% | ¿El hero genera suficiente interés para seguir? |
| Comprensión | Hero entendido | < 5 segundos | ¿El H1 describe el beneficio sin necesitar el H2? |
| Intención | CTR del CTA hero | > 8% | ¿El copy del CTA y el diseño eliminan la fricción? |
| Conversión | Landing → Signup | > 20% | ¿La página responde las objeciones antes de pedir el registro? |
| Activación | Signup → Empresa creada | > 80% | ¿El onboarding es tan simple que completarlo es la ruta obvia? |
| Retención | Regreso en 7 días | > 50% | ¿El producto entrega valor en la primera sesión? |

---

## Métricas técnicas (por landing)

| Métrica | Objetivo | Herramienta |
|---------|----------|-------------|
| Lighthouse Performance | ≥ 95 | Lighthouse CLI / PageSpeed |
| LCP (Largest Contentful Paint) | < 2.5s | CrUX / PageSpeed |
| CLS (Cumulative Layout Shift) | < 0.1 | CrUX / PageSpeed |
| INP (Interaction to Next Paint) | < 200ms | CrUX |
| Peso total de página | < 1MB | WebPageTest |
| Peso de imagen hero | < 300KB | manual |
| Tiempo hasta interactivo | < 3.5s | Lighthouse |

---

## Métricas de contenido (por imagen)

| Criterio | Objetivo | Cómo medir |
|----------|----------|------------|
| Personas visibles en la imagen | 100% de imágenes de escena | visual review |
| Imagen con interacción humana | 100% de imágenes de escena | visual review |
| Imágenes que pasaron PHOTO_GUIDELINES | 100% antes de publicar | checklist |
| Peso de imagen WebP (scenes) | < 300KB | `ls -lh static/img/welcome/scenes/` |
| Formatos exportados por master | 6 (scene + 5 formatos) | `export_assets.sh --check` |

---

## Métricas de marca (revisión trimestral)

Estas métricas no son automáticas. Requieren revisión manual cada 90 días.

| Pregunta | Objetivo |
|----------|----------|
| ¿Todas las landings activas pasaron el checklist? | 100% |
| ¿Los ADRs de marketing están actualizados? | Sin ADRs > 6 meses sin revisión si el contexto cambió |
| ¿El Product Narrative sigue siendo la brújula real del copy producido? | Sí, sin excepciones documentadas |
| ¿Las imágenes publicadas cumplen los Do/Don't de PHOTO_GUIDELINES? | 100% |
| ¿El vocabulario prohibido aparece en alguna landing activa? | 0 instancias |

---

## Métricas de consistencia (por país)

Para cada página de bienvenida activa:

| Métrica | Objetivo |
|---------|----------|
| `terminology` pills correctos para el país | 3 pills, fuente: `welcome_config.py` |
| `market_insight` con dato verificado | dato real, no placeholder |
| `social_proof.stats` con números del mercado local | ≥ 2 stats, no global |
| Imagen hero específica del país (post Sprint B2) | `static/img/welcome/{cc}/hero.webp` existe |

---

## Cómo usar este documento

1. **Al lanzar una landing nueva:** correr Lighthouse antes de publicar. Registrar los valores.
2. **Semanalmente:** revisar CTR del CTA hero y Landing→Signup en el analytics.
3. **Al mes de lanzamiento:** revisar scroll depth y tiempo en página.
4. **Trimestralmente:** pasar la revisión de marca y consistencia por país.

Si una métrica está consistentemente bajo objetivo durante 30 días:
abrir el documento correspondiente (CONVERSION_GUIDELINES, COPY_GUIDELINES, DESIGN_SYSTEM)
e identificar cuál principio se está violando. **No optimizar a ciegas — diagnosticar primero.**

---

## Fuente de datos

| Dato | Fuente |
|------|--------|
| CTR, scroll depth, conversión | Google Analytics 4 / Plausible |
| LCP, CLS, INP | Google Search Console (CrUX) |
| Lighthouse | `npx lighthouse {url} --output json` |
| Peso de imágenes | `ls -lh static/img/welcome/` |
| Estado de activos | `./marketing/scripts/export_assets.sh --check` |
