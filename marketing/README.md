# Marketing eGarage

Repositorio central de contenido y activos visuales de la marca.

---

## Estructura

```
marketing/
├── BrandBook/            ← Paleta, tipografía, voz de marca, guías de uso
├── Assets/
│   ├── Master/           ← Archivos fuente de alta resolución (.psd / .ai / .fig)
│   ├── Exports/          ← Derivados por formato y tamaño (nunca editar directo)
│   │   ├── Hero/         ← 2560 × 1440 px  (páginas de bienvenida web)
│   │   ├── OG/           ← 1200 × 630 px   (Open Graph / Twitter Card)
│   │   ├── Social/       ← 1080 × 1350 px  (post feed Instagram / Facebook)
│   │   ├── Story/        ← 1080 × 1920 px  (Historias / Reels verticales)
│   │   └── Thumbnail/    ← 1280 × 720 px   (YouTube / presentaciones)
│   └── Mockups/          ← Composites finales (hero por país, ads ensamblados)
├── Welcome/              ← Hero localizados por país (un subdirectorio por mercado)
│   ├── Chile/
│   ├── Mexico/
│   ├── USA/
│   ├── Argentina/
│   ├── Uruguay/
│   ├── Brazil/
│   ├── Peru/
│   ├── Venezuela/
│   ├── Colombia/
│   └── Ecuador/
├── Social/               ← Publicaciones listas para publicar (texto + imagen)
│   ├── Instagram/
│   ├── Facebook/
│   ├── LinkedIn/
│   └── TikTok/
├── Ads/                  ← Creatividades de anuncios pagados
│   ├── Meta/
│   └── Google/
├── Video/
│   ├── Reels/
│   └── YouTube/
├── Presentations/        ← Decks comerciales y pitch
└── contenido_generado/   ← Generado por `manage.py generar_contenido_marketing`
```

---

## Resoluciones oficiales

| Formato       | Resolución    | Uso principal                           |
|---------------|---------------|-----------------------------------------|
| Hero          | 2560 × 1440   | Páginas de bienvenida (hero fullwidth)  |
| Open Graph    | 1200 × 630    | Vista previa en links (OG / Twitter)   |
| Social        | 1080 × 1350   | Post feed Instagram y Facebook          |
| Story         | 1080 × 1920   | Historias, Reels, TikTok               |
| Thumbnail     | 1280 × 720    | YouTube, presentaciones comerciales     |

> **Regla:** todos los formatos salen del mismo master. Nunca se diseña desde cero para cada tamaño.

---

## Sprint B1 — Biblioteca Oficial (5 masters)

Los cinco activos maestros de la plataforma. Compartidos por todas las páginas de país.

| Archivo master              | Escena                  | Descripción                                           |
|-----------------------------|-------------------------|-------------------------------------------------------|
| `01_taller.psd`             | Taller mecánico         | Técnico + cliente frente a vehículo elevado, tablet   |
| `02_repuestos.psd`          | Casa de repuestos       | Empleado escaneando QR en estantería impecable        |
| `03_desarme.psd`            | Desarmaduría            | Operario etiquetando motor con QR, tablet en mano    |
| `04_carwash.psd`            | Carwash premium         | Empleado entrega llaves a cliente, auto brillante     |
| `05_control_center.psd`     | Dashboard eGarage       | Mockup de marketing: KPIs, OTs, agenda, inventario   |

Exportar como:
```
Assets/Exports/Hero/01_taller_2560x1440.webp
Assets/Exports/OG/01_taller_1200x630.webp
Assets/Exports/Social/01_taller_1080x1350.webp
...
```

Web-ready (optimizados para las páginas de bienvenida) se colocan en:
```
static/img/welcome/scenes/taller.webp
static/img/welcome/scenes/repuestos.webp
static/img/welcome/scenes/desarme.webp
static/img/welcome/scenes/carwash.webp
static/img/welcome/scenes/dashboard.webp
```

---

## Sprint B2 — Heroes por país

Un hero por mercado, generado componiendo los masters con el vehículo y texto locales.

```
static/img/welcome/{country}/hero.webp   ← web-ready
marketing/Welcome/{Country}/hero.psd     ← fuente editable
```

Orden de producción: CL → US → MX → AR → CO → PE → EC → UY → VE → BR

---

## Contenido social (generado por CLI)

```bash
python manage.py generar_contenido_marketing \
    --feature "Nombre de la funcionalidad" \
    --descripcion "Descripción breve de qué hace y por qué importa" \
    --idioma es \
    --pais CL
```

| Opción          | Default                   | Descripción                        |
|-----------------|---------------------------|------------------------------------|
| `--feature`     | *requerido*               | Nombre de la funcionalidad         |
| `--descripcion` | *requerido*               | Descripción corta                  |
| `--publico`     | Talleres en Latinoamérica | Público objetivo                   |
| `--idioma`      | `es`                      | Código de idioma                   |
| `--pais`        | `CL`                      | País (CL, MX, AR, US, PE...)       |
| `--force`       | false                     | Sobreescribir si ya existe         |
| `--dry-run`     | false                     | Previsualizar sin crear archivos   |

Salida en `contenido_generado/YYYY-MM-DD-slug/`:
`facebook.md`, `instagram.md`, `tiktok.md`, `reel_guion.md`, `historias.md`, `hashtags.md`, `paquete.json`

---

## Principios

- **Una fuente de verdad** — cada imagen existe una sola vez (en `Master/`); los exports son derivados.
- **Nunca diseñar desde cero** — si se cambia un color de marca, se actualiza el master y se regeneran los exports.
- **Git como registro** — los masters PSD/AI no se versionar aquí (son binarios grandes); los exports webp sí.
- **Separación contenido/activo** — `contenido_generado/` = texto. `Assets/` = visual. No mezclar.
