# Asset Pipeline — eGarage

> Una fuente de verdad. Un comando. Cero decisiones manuales sobre formatos.

---

## Principio

Cada imagen existe **una sola vez**: el archivo master en `marketing/Assets/Master/`.
Todo lo demás —formatos web, redes, OG, thumbnails— se genera automáticamente desde ese master.
Nunca se diseña por tamaño. Nunca se exporta manualmente.

---

## Estructura de directorios

```
marketing/
└── Assets/
    ├── Master/           ← fuente: PNG/JPG/TIFF de alta resolución (no en git LFS por ahora)
    ├── Scenes/           ← crop 16:9 a máxima calidad (generado por el pipeline)
    └── Exports/
        ├── Hero/         ← 2560 × 1440 webp  (páginas de bienvenida)
        ├── OG/           ← 1200 × 630 webp   (Open Graph / Twitter Card)
        ├── Social/       ← 1080 × 1350 webp  (feed Instagram / Facebook)
        ├── Story/        ← 1080 × 1920 webp  (Historias, Reels, TikTok)
        └── Thumbnail/    ← 1280 × 720 webp   (YouTube, presentaciones)

static/img/welcome/
├── scenes/               ← web-ready (1920×1080, q85) — consumido por hero.html
│   ├── placeholder.webp
│   ├── taller.webp
│   ├── repuestos.webp
│   ├── desarme.webp
│   ├── carwash.webp
│   └── control_center.webp
└── {country}/            ← heroes por país (Sprint B2)
    └── hero.webp
```

---

## Convención de nombres

### Masters (Sprint B1 — escenas globales)

| Archivo master | Escena | Slug web |
|----------------|--------|----------|
| `01_taller.png` | Taller mecánico | `taller` |
| `02_repuestos.png` | Casa de repuestos | `repuestos` |
| `03_desarme.png` | Desarmaduría | `desarme` |
| `04_carwash.png` | Carwash premium | `carwash` |
| `05_control_center.png` | Control Center / Dashboard | `control_center` |

### Heroes por país (Sprint B2)

```
marketing/Welcome/{Country}/hero.png   →   static/img/welcome/{cc}/hero.webp
```

Países: Chile, Mexico, USA, Argentina, Colombia, Peru, Ecuador, Uruguay, Venezuela, Brazil

---

## Resoluciones y calidad

| Formato | Resolución | Calidad WebP | Archivo destino |
|---------|------------|--------------|-----------------|
| Scene master (16:9) | 2560 × 1440 | 92 | `Assets/Scenes/{prefix}.webp` |
| Hero | 2560 × 1440 | 88 | `Assets/Exports/Hero/{prefix}_2560x1440.webp` |
| Open Graph | 1200 × 630 | 88 | `Assets/Exports/OG/{prefix}_1200x630.webp` |
| Social feed | 1080 × 1350 | 88 | `Assets/Exports/Social/{prefix}_1080x1350.webp` |
| Story | 1080 × 1920 | 88 | `Assets/Exports/Story/{prefix}_1080x1920.webp` |
| Thumbnail | 1280 × 720 | 88 | `Assets/Exports/Thumbnail/{prefix}_1280x720.webp` |
| Web-ready | 1920 × 1080 | 85 | `static/img/welcome/scenes/{slug}.webp` |

El recorte es siempre center-crop (ImageOps.fit). El aspecto se preserva llenando el frame.

---

## Comandos

```bash
# Ver qué masters existen y qué falta
./marketing/scripts/export_assets.sh --check

# Exportar todos los masters disponibles
./marketing/scripts/export_assets.sh

# Exportar solo una escena
./marketing/scripts/export_assets.sh taller
./marketing/scripts/export_assets.sh repuestos desarme

# Preview sin escribir archivos
./marketing/scripts/export_assets.sh --dry-run
./marketing/scripts/export_assets.sh --dry-run taller
```

---

## Flujo completo por imagen

### Cuando termines una imagen en ChatGPT / Midjourney / fotógrafo:

```
1. Descargar en alta resolución (PNG preferido, mínimo 2560px de ancho)

2. Guardar en:
   marketing/Assets/Master/01_taller.png   (usar el prefijo correcto)

3. Ejecutar:
   ./marketing/scripts/export_assets.sh taller

4. Verificar resultado:
   ./marketing/scripts/export_assets.sh --check

5. Comprobar en browser:
   python manage.py runserver
   → /mx/es/bienvenida/  (la página debe mostrar la imagen nueva)

6. Commit:
   git add static/img/welcome/scenes/taller.webp marketing/Assets/Exports/
   git commit -m "feat(brand): add taller scene (Sprint B1)"
```

> El master PNG **no se commitea** por su tamaño. Solo se guardan los exports WebP.
> Si el proyecto crece, considerar Git LFS para `marketing/Assets/Master/`.

---

## Fallback automático

Si un archivo WebP no existe en `static/img/welcome/scenes/`, el sistema usa
`placeholder.webp` automáticamente vía el template tag `{% scene_image %}`.

El placeholder es un WebP de 46 bytes (16×9 px en negro `#0a0c10`).
Nunca lanza un error 404 ni rompe el layout.

---

## Integración con el template

```django
{# hero.html #}
{% load welcome_tags %}
{% scene_image scene.image as scene_src %}
<picture>
  <source srcset="{{ scene_src }}" type="image/webp">
  <img src="{{ scene_src }}" alt="{{ scene.label }}"
       loading="lazy" decoding="async">
</picture>
```

`scene.image` viene de `HERO_RUBRO_SCENES` en `taller/welcome_config.py`.
El template tag resuelve la ruta a `staticfiles` y aplica el fallback.

---

## Git — qué se commitea y qué no

| Archivos | Git |
|----------|-----|
| `marketing/Assets/Master/*.png` | ❌ No (archivos pesados, fuera de git) |
| `marketing/Assets/Scenes/*.webp` | ✅ Sí |
| `marketing/Assets/Exports/**/*.webp` | ✅ Sí |
| `static/img/welcome/scenes/*.webp` | ✅ Sí |
| `static/img/welcome/*/hero.webp` | ✅ Sí |
| `marketing/scripts/` | ✅ Sí |
| `docs/marketing/` | ✅ Sí |

Agregar al `.gitignore`:
```
marketing/Assets/Master/
```
