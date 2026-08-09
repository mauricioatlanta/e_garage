# Checklist de publicación — eGarage Marketing

> Este documento se abre antes de publicar cualquier landing, imagen o campaña.
> Completar de arriba abajo. No publicar con ítems sin marcar.

---

## Landing / página web

### Marca y copy

- [ ] El H1 describe un beneficio, no el software ni una funcionalidad.
- [ ] El visitante entiende qué es eGarage sin bajar el scroll (test de 5 segundos).
- [ ] El copy fue validado contra `COPY_GUIDELINES.md` (vocabulario, tono, frases prohibidas).
- [ ] El CTA principal dice "Comenzar gratis" (o equivalente local aprobado).
- [ ] El subtext "30 días • Sin tarjeta • Configuración en minutos" está visible bajo el CTA.
- [ ] Ninguna sección usa terminología técnica: ERP, CRM, SaaS, módulo, workflow.

### Diseño

- [ ] Todos los tokens de color, tipografía, radios y sombras siguen `DESIGN_SYSTEM.md`.
- [ ] No hay más de un botón primario visible en el mismo viewport.
- [ ] El espaciado vertical entre secciones es ≥ 80px en desktop.
- [ ] No se usaron tipografías futuristas (Orbitron, Exo 2) en contexto de producto.
- [ ] Radios de borde: solo 16px, 24px o 32px.
- [ ] Sombras: solo `shadow-sm` o `shadow-lg`.

### Estructura

- [ ] La estructura de secciones sigue `LANDING_GUIDELINES.md` (Hero → Stats → Rubros → Features → …).
- [ ] Cada sección responde exactamente una pregunta (`CONVERSION_GUIDELINES.md` Principio 2).
- [ ] Ninguna sección termina "muerta" sin invitar a continuar (Principio 3).
- [ ] Los beneficios aparecen antes que las características (Principio 6).

### Imágenes

- [ ] Todas las imágenes fueron validadas contra `PHOTO_GUIDELINES.md`.
- [ ] Hay al menos una fotografía con personas reales interactuando.
- [ ] Ninguna imagen supera 400KB.
- [ ] Todas las imágenes tienen `loading="lazy"` excepto el hero (`loading="eager"`).
- [ ] Todas usan formato WebP con `<picture>` y `srcset`.
- [ ] No hay texto sobre imagen sin overlay de legibilidad.
- [ ] Ninguna imagen tiene logo de marca de auto visible y prominente.

### Localización (para páginas por país)

- [ ] Los terminology pills son correctos para el país (`welcome_config.py` → `terminology`).
- [ ] El `market_insight` corresponde al mercado real del país.
- [ ] El `social_proof.stats` usa datos del mercado local, no globales.
- [ ] La variante de idioma (ES/EN/PT) es coherente en toda la página.

### Performance

- [ ] LCP < 2.5s (medir con Lighthouse o WebPageTest).
- [ ] CLS < 0.1.
- [ ] Las fuentes tienen `font-display: swap`.
- [ ] No hay bloqueo de render por JS síncrono en `<head>`.

### Mobile

- [ ] El H1 es legible sin zoom en iPhone SE (375px).
- [ ] El CTA es alcanzable con el pulgar (zona inferior de pantalla, ≥ 48px de alto).
- [ ] El carrusel de escenas (mobile) hace scroll suave con scroll-snap.
- [ ] No hay elementos que se corten horizontalmente en 375px.

---

## Imagen / activo visual

- [ ] La imagen fue producida siguiendo `PHOTO_GUIDELINES.md` (Do / Don't).
- [ ] Hay al menos una persona visible e identificable.
- [ ] Hay interacción real (no persona mirando a cámara).
- [ ] Luz natural o cálida. Sin neón frío, sin estudio genérico.
- [ ] Vehículo cotidiano (si aplica). Sin autos de lujo.
- [ ] El master está guardado en `marketing/Assets/Master/` con el prefijo correcto.
- [ ] El pipeline fue ejecutado: `./marketing/scripts/export_assets.sh {escena}`.
- [ ] Los exports están en `marketing/Assets/Exports/` en todos los formatos.
- [ ] El archivo web-ready está en `static/img/welcome/scenes/{slug}.webp`.
- [ ] Se verificó en browser que la imagen aparece correctamente.

---

## Campaña / contenido social

- [ ] El copy fue generado o revisado contra `COPY_GUIDELINES.md`.
- [ ] El tono es cercano y profesional. Sin frases corporativas ni jerga técnica.
- [ ] El gancho de la primera línea no supera 2 líneas antes del corte.
- [ ] El CTA es una acción del usuario, no una descripción del producto.
- [ ] Los hashtags son relevantes al mercado y al rubro target.
- [ ] Las imágenes adjuntas pasaron el checklist de imagen de arriba.
- [ ] El contenido está en `contenido_generado/YYYY-MM-DD-slug/` para registro.

---

## Firma

> Al marcar este checklist, confirmo que el material cumple los estándares de la marca eGarage
> y puede publicarse sin revisión adicional.

Responsable: ___________________  Fecha: ___________________
