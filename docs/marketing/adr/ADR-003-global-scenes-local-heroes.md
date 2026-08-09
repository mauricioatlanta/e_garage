# ADR-003 — Escenas de rubro globales, hero localizado por país

**Estado:** Aprobado
**Fecha:** 2026-08-05
**Autores:** Mauricio Alvarado

---

## Contexto

eGarage opera en 11 países con 4 tipos de rubro principales (taller, repuestos, desarmaduría, carwash).

Al diseñar la biblioteca visual, había tres opciones:

1. **Todo global:** mismas 5 imágenes para los 11 países
2. **Todo local:** 5 imágenes × 11 países = 55 imágenes para producir desde cero
3. **Híbrido:** escenas de rubro globales + hero localizado por país

---

## Decisión

**Híbrido: 5 master globales (Sprint B1) + 1 hero localizado por país (Sprint B2).**

### Sprint B1 — 5 masters globales
```
01_taller.webp       → Taller mecánico
02_repuestos.webp    → Casa de repuestos
03_desarme.webp      → Desarmaduría
04_carwash.webp      → Carwash
05_control_center.webp → Dashboard eGarage
```

Estas imágenes son neutras en contexto de país: personas latinoamericanas genéricas,
vehículos comunes en toda la región (sedán y pickup), sin elementos culturales específicos.

### Sprint B2 — 1 hero por país
```
static/img/welcome/{cc}/hero.webp
```

El hero de cada país compone el master global con elementos locales:
- Vehículo típico del país (`welcome_config.py` → `vehicles`)
- Terminología local superpuesta
- Paleta del país (`theme.primary`, `theme.accent`)

---

## Razones

### 1. Calidad > Cantidad
5 fotografías excelentes producidas con cuidado superan a 55 fotografías mediocres producidas a las carreras.
La confianza visual se construye con pocas imágenes perfectas, no con muchas imágenes "suficientes".

### 2. Los rubros son universales; el contexto cultural, no
Un técnico mostrando una tablet a un cliente frente a un auto elevado es reconocible en México, Chile y Brasil.
Pero el vehículo que ese cliente trajo al taller es diferente: en México es una Nissan Frontier,
en Chile es una Toyota Hilux, en Brasil es un Fiat Strada.
La escena es global. El detalle que genera identificación cultural es local.

### 3. El pipeline de exportación soporta exactamente este modelo
`export_assets.sh` procesa masters y genera todos los formatos automáticamente.
Cambiar un master regenera automáticamente todos sus derivados.
Sin este pipeline, mantener 55 imágenes sería inmanejable.

### 4. Separación de responsabilidades
- Sprint B1: producción fotográfica/IA → 5 imágenes. Hecho una vez, reutilizado para siempre.
- Sprint B2: composición digital → 11 variantes. Tarea repetible con un template.

---

## Implementación técnica

### Fallback automático
Si el hero del país no existe, `{% scene_image %}` usa `placeholder.webp`.
El sistema nunca lanza error 404 ni rompe el layout.

### Fuente de datos
`taller/welcome_config.py` → `WELCOME_CONFIG[(country, lang)]`:
- `vehicles`: lista de vehículos típicos del país (para composición del hero)
- `theme`: colores para el overlay
- `hero_image`: ruta del hero localizado

### Orden de producción Sprint B2
CL → US → MX → AR → CO → PE → EC → UY → VE → BR

Criterio: volumen de mercado + países con suscriptores activos primero.

---

## Consecuencias

- **Restricción de diseño:** los masters globales no pueden tener elementos culturales específicos (matrículas legibles, señales de tráfico nacionales, uniformes con banderas).
- **Revisión periódica:** si un master global necesita actualizarse, todos los heroes por país derivados de él también se regeneran.
- **Documentación en código:** `HERO_RUBRO_SCENES` en `welcome_config.py` es la fuente de verdad del brief de arte. La documentación lo referencia, no lo duplica.

---

## Alternativa descartada: todo local

**Razón del descarte:** la calidad fotográfica real requiere producción presencial o generación IA muy controlada.
Producir 55 imágenes de calidad consistente con recursos limitados es inviable.
La estrategia global/local permite lanzar con 5 imágenes de alta calidad y escalar localmente solo donde hay tracción de mercado suficiente para justificar la inversión.
