# Photo Guidelines — eGarage

> Una fotografía de eGarage debe parecer un reportaje, no una publicidad.
> El cliente debe verse reflejado. No aspiracional. Real.

---

## Principios fotográficos

1. **Personas trabajando** — siempre hay al menos una persona visible e identificable.
2. **Interacción humana** — nunca una persona sola mirando a cámara. Siempre hay acción.
3. **Negocios reales** — el ambiente debe existir en la vida real de un cliente de eGarage.
4. **La tecnología es la herramienta, no el protagonista** — eGarage aparece en la pantalla, no en el centro del encuadre.

---

## Estilo

| Parámetro | Regla |
|-----------|-------|
| Luz | Natural o cálida. Nunca estudio frío ni neón. |
| Lente | 35mm o 50mm. Sin grandes angulares (evitar distorsión). |
| Profundidad de campo | Foco en las personas. Fondo levemente desenfocado. |
| Paleta | Cálida-neutra. Saturación moderada. Nada sobreexpuesto. |
| Mood | Profesional y cercano. No glamoroso, no publicitario. |

---

## Do / Don't por escena

### Hero — Taller mecánico

| ✅ DO | ❌ DON'T |
|-------|---------|
| Cliente conversando con técnico frente al auto | Persona mirando a cámara con sonrisa forzada |
| Tablet mostrando eGarage, ambos mirando la pantalla | Pantalla en blanco o con interfaz genérica |
| Vehículo elevado en elevador hidráulico real | Ferrari, Lamborghini, auto deportivo de lujo |
| Luz natural o cálida entrando por ventana del taller | Estudio fotográfico frío, neón azul artificial |
| Herramientas ordenadas y reales al fondo | Taller de concesionaria de lujo irreal |
| Ropa de trabajo (overol, camiseta de trabajo) | Traje, corbata, ropa de oficina |

### Hero — Casa de repuestos

| ✅ DO | ❌ DON'T |
|-------|---------|
| Empleado escaneando código QR con scanner real | Persona parada sin hacer nada |
| Estantería ordenada, cajas etiquetadas claramente | Depósito caótico o vacío |
| Tablet o celular en mano activa | Pantalla en blanco |
| Postura activa, picking, movimiento | Pose estática mirando a cámara |
| Piezas reales (filtros, frenos, repuestos comunes) | Piezas de avión, maquinaria industrial irreal |

### Hero — Desarmaduría

| ✅ DO | ❌ DON'T |
|-------|---------|
| Operario etiquetando motor con código QR visible | Patio desordenado con autos apilados |
| Tablet en una mano, pieza en la otra | Escena de depósito sin organización |
| Ambiente organizado — centro de logística, no chatarra | Suciedad excesiva, ambiente de abandono |
| Motor o pieza importante como protagonista | Solo carrocería o autos completos sin contexto |
| Código QR legible en la imagen | Etiqueta borrosa o sin información |

### Hero — Carwash

| ✅ DO | ❌ DON'T |
|-------|---------|
| Empleado entregando llaves a cliente satisfecho | Solo agua y jabón sin personas |
| Auto brillante en primer plano | Auto sucio o mal terminado |
| Espuma o microfibra visible como detalle de calidad | Lavadero de barrio de bajo costo |
| Negocio premium pero accesible | Instalación de lujo irreal tipo spa automotriz |
| Cliente con expresión de satisfacción | Nadie en la escena |

### Dashboard / Control Center

| ✅ DO | ❌ DON'T |
|-------|---------|
| KPIs grandes y legibles (Ventas, OTs, Agenda) | Captura de pantalla del ERP sin contexto |
| Datos representativos y realistas | Datos vacíos o "Lorem ipsum" |
| Diseño limpio, mucho espacio blanco | Interface saturada de información |
| Dueño revisando el dashboard en tablet | Pantalla gigante en sala de servidores |
| Gráficos simples y claros | Gráficos complejos de Business Intelligence |

---

## Reglas absolutas

### ✅ Siempre
- Al menos una persona visible e identificable
- Interacción real (técnico ↔ cliente, empleado ↔ herramienta)
- Luz natural o cálida
- Negocios de tamaño real (1-5 empleados visibles)
- Herramientas y vehículos reales y comunes
- Tablet o celular mostrando eGarage (nunca pantalla en blanco)
- Ropa de trabajo apropiada

### ❌ Nunca
- Ferraris, Lamborghinis, autos de lujo o colección
- Talleres de concesionaria o de lujo extremo
- Robots, hologramas, interfaces de ciencia ficción
- Efectos tecnológicos excesivos (rayos, partículas, glow extremo)
- Personas posando mirando a cámara con sonrisa forzada
- Logos de marcas de autos visibles y prominentes
- Herramientas flotando o en composición irreal
- Estudio fotográfico frío o luz neón azul artificial

---

## Interacciones aprobadas

| Escena | Descripción |
|--------|-------------|
| Técnico + cliente | Técnico muestra tablet al cliente frente al vehículo. Ambos miran la pantalla. |
| Empleado + scanner | Empleado escanea código QR en estantería. Postura activa. |
| Operario + pieza | Operario etiqueta pieza con código QR. Tablet en la otra mano. |
| Entrega + cliente | Empleado entrega llaves a cliente satisfecho. Auto limpio en primer plano. |
| Dueño + pantalla | Dueño del negocio revisa dashboard en escritorio o tablet. Expresión de control. |

---

## Biblioteca visual — estructura y estado

### Escenas globales (Sprint B1)
Compartidas por todos los países. Producir una sola vez.

| Código | Escena | Archivo web | Estado |
|--------|--------|-------------|--------|
| `01_taller` | Taller mecánico | `scenes/taller.webp` | placeholder |
| `02_repuestos` | Casa de repuestos | `scenes/repuestos.webp` | placeholder |
| `03_desarme` | Desarmaduría | `scenes/desarme.webp` | placeholder |
| `04_carwash` | Carwash premium | `scenes/carwash.webp` | placeholder |
| `05_control_center` | Dashboard eGarage | `scenes/control_center.webp` | placeholder |

> Master PSD/PNG → `marketing/Assets/Master/`
> Exportar con: `./marketing/scripts/export_assets.sh`

### Heroes por país (Sprint B2)
Un hero por mercado, compuesto desde los masters globales.

| País | Archivo web | Archivo master |
|------|-------------|----------------|
| Chile | `welcome/cl/hero.webp` | `marketing/Welcome/Chile/hero.psd` |
| México | `welcome/mx/hero.webp` | `marketing/Welcome/Mexico/hero.psd` |
| USA | `welcome/us/hero.webp` | `marketing/Welcome/USA/hero.psd` |
| Argentina | `welcome/ar/hero.webp` | `marketing/Welcome/Argentina/hero.psd` |
| Colombia | `welcome/co/hero.webp` | `marketing/Welcome/Colombia/hero.psd` |
| Perú | `welcome/pe/hero.webp` | `marketing/Welcome/Peru/hero.psd` |
| Ecuador | `welcome/ec/hero.webp` | `marketing/Welcome/Ecuador/hero.psd` |
| Uruguay | `welcome/uy/hero.webp` | `marketing/Welcome/Uruguay/hero.psd` |
| Venezuela | `welcome/ve/hero.webp` | `marketing/Welcome/Venezuela/hero.psd` |
| Brasil | `welcome/br/hero.webp` | `marketing/Welcome/Brazil/hero.psd` |

Orden de producción: CL → US → MX → AR → CO → PE → EC → UY → VE → BR

---

## Resoluciones oficiales

| Formato | Resolución | Uso |
|---------|------------|-----|
| Hero | 2560 × 1440 | Páginas de bienvenida (fullwidth) |
| Open Graph | 1200 × 630 | Preview en links (OG / Twitter Card) |
| Social | 1080 × 1350 | Post feed Instagram / Facebook |
| Story | 1080 × 1920 | Historias, Reels, TikTok |
| Thumbnail | 1280 × 720 | YouTube, presentaciones |

Todos los formatos salen del mismo master. Nunca se diseña por tamaño.

---

## Art direction por escena

Ver `taller/welcome_config.py` → `HERO_RUBRO_SCENES` y `DASHBOARD_SCENE`.
Cada escena contiene: `camera`, `lighting`, `mood`, `people_roles`, `people_action`, `vehicle`, `composition`.
Estos campos son el brief oficial para cualquier herramienta de generación de imágenes o fotógrafo humano.
