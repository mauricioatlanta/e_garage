# AI Playbook — eGarage

> Este documento es para Claude, Windsurf, Midjourney, ChatGPT, Copilot y cualquier herramienta de IA
> que genere contenido para eGarage. También aplica a cualquier persona nueva que trabaje con IA en el proyecto.
>
> Antes de generar cualquier cosa, leer las guías correspondientes a la tarea.

---

## Por qué existe este documento

La IA puede generar contenido muy rápido. El riesgo es que genere contenido que no representa a la marca.
Este playbook convierte las decisiones de marca en instrucciones que cualquier IA puede seguir.

**Principio:** La IA no decide el tono, el estilo ni los valores. Solo aplica los que están en estos documentos.

---

## Mapa de tareas → documentos

### Generar una imagen (fotografía de escena, hero, social)

**Leer antes de empezar:**
1. [`05_PHOTO_GUIDELINES.md`](05_PHOTO_GUIDELINES.md) — Do/Don't por escena, estilo, luz, personas
2. [`02_BRAND_GUIDE.md`](02_BRAND_GUIDE.md) — personalidad, lo que somos y lo que nunca somos

**Fuente oficial del brief de arte:**
`taller/welcome_config.py` → `HERO_RUBRO_SCENES` (campos: `camera`, `lighting`, `mood`, `people_action`, `vehicle`, `composition`)

**Checklist mínimo antes de aprobar la imagen:**
- [ ] Hay al menos una persona visible e identificable
- [ ] Hay interacción real (no pose mirando a cámara)
- [ ] Luz natural o cálida
- [ ] Vehículo cotidiano (si aplica) — sin autos de lujo
- [ ] Sin efectos tecnológicos: sin rayos, hologramas, neón frío

---

### Escribir copy (landing, email, social, ads)

**Leer antes de empezar:**
1. [`01_PRODUCT_NARRATIVE.md`](01_PRODUCT_NARRATIVE.md) — el héroe, el guía, la transformación, el enemigo
2. [`03_COPY_GUIDELINES.md`](03_COPY_GUIDELINES.md) — vocabulario nunca/siempre, tono por canal, frases aprobadas

**Reglas que nunca se rompen:**
- El dueño del negocio es el héroe. eGarage es el guía. Nunca al revés.
- Beneficios antes que características. Siempre.
- Vocabulario prohibido: ERP, CRM, módulo, robusto, potente, solución integral, end-to-end.
- El CTA es una acción del usuario: "Comenzar gratis", no "Ver nuestro sistema".

---

### Escribir o modificar una landing page

**Leer antes de empezar:**
1. [`04_DESIGN_SYSTEM.md`](04_DESIGN_SYSTEM.md) — tokens, componentes, espaciado exacto
2. [`06_LANDING_GUIDELINES.md`](06_LANDING_GUIDELINES.md) — estructura de secciones, copy H1/H2/CTA
3. [`07_CONVERSION_GUIDELINES.md`](07_CONVERSION_GUIDELINES.md) — los 8 principios que gobiernan cada decisión

**Checklist mínimo antes de generar código:**
- [ ] El H1 describe un beneficio (no el software)
- [ ] La estructura de secciones sigue el orden de `06_LANDING_GUIDELINES.md`
- [ ] Solo radios de borde: 16px, 24px, 32px
- [ ] Solo sombras: `shadow-sm` o `shadow-lg`
- [ ] CTA height: 56px, font-weight: 600
- [ ] Un solo CTA primario visible por viewport

---

### Escribir un post de redes sociales

**Leer antes de empezar:**
1. [`03_COPY_GUIDELINES.md`](03_COPY_GUIDELINES.md) → sección "Tono por canal → Redes sociales"
2. [`01_PRODUCT_NARRATIVE.md`](01_PRODUCT_NARRATIVE.md) → "El héroe" y "Lo que nunca decimos"

**O usar el comando oficial:**
```bash
python manage.py generar_contenido_marketing \
    --feature "nombre" \
    --descripcion "descripción" \
    --pais CL
```

---

### Generar assets visuales (exportar imágenes)

**Comando oficial:**
```bash
./marketing/scripts/export_assets.sh taller
./marketing/scripts/export_assets.sh --check
```

**Ver el flujo completo en:** [`08_ASSET_PIPELINE.md`](08_ASSET_PIPELINE.md)

---

### Diseñar un componente nuevo

**Antes de crear cualquier componente:**
1. Verificar que no existe ya en [`04_DESIGN_SYSTEM.md`](04_DESIGN_SYSTEM.md)
2. Si no existe, seguir los tokens base (colores, radios, sombras, tipografía) — nunca inventar nuevos valores
3. Si el nuevo componente debería estar en el Design System, agregarlo ahí antes de usarlo

---

### Crear una nueva página por país

**Archivos que definen la página:**
- `taller/welcome_config.py` → `WELCOME_CONFIG[(country, lang)]` — todos los datos de la página
- `taller/views_extra/bienvenida.py` → la view que inyecta el config
- `templates/components/welcome/_base.html` → el layout base
- `templates/components/welcome/hero.html` → el hero con escenas

**No duplicar datos que ya existen en el código.** Si hay un dato en `welcome_config.py`, usarlo desde allí.
No copiarlo en la documentación.

---

## Prompt base para generación de imágenes

Cuando generes el prompt para una imagen de eGarage, este es el template:

```
Fotografía documental de [ESCENA].
[PEOPLE_ACTION — copiar de HERO_RUBRO_SCENES.people_action]
Lente [CAMERA]mm. Luz [LIGHTING], cálida y natural.
Ambiente: [ENVIRONMENT] real, de tamaño normal, sin lujos.
Vehículo: [VEHICLE] — cotidiano, sedán o pickup popular, sin autos de lujo.
Composición: peso visual a la [COMPOSITION].
Post-procesado: saturación moderada, contraste natural, sin efectos digitales.
Sin: robots, hologramas, efectos de neón, personas mirando a cámara,
     logos gigantes, autos deportivos, talleres de concesionaria.
Estilo: editorial, documental, no publicitario.
```

Los valores de `[CAMERA]`, `[LIGHTING]`, `[PEOPLE_ACTION]`, `[VEHICLE]`, `[COMPOSITION]`
vienen de `taller/welcome_config.py` → `HERO_RUBRO_SCENES[n]`.

---

## Validación antes de entregar

Independientemente de la tarea, antes de presentar un resultado:

1. **¿El dueño del negocio es el héroe?** Si el copy o la imagen pone a eGarage en el centro, rehacer.
2. **¿Pasaría el test de 5 segundos?** ¿Alguien que no conoce eGarage entendería qué hace en 5 segundos?
3. **¿Hay vocabulario prohibido?** Buscar: ERP, CRM, módulo, robusto, potente, solución, end-to-end.
4. **¿Las imágenes tienen personas reales en acción?** No poses, no ilustraciones, no renders vacíos.
5. **¿El resultado pasaría el [`10_CHECKLIST.md`](10_CHECKLIST.md)?** Ese es el estándar de publicación.
