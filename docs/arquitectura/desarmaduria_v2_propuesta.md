# Desarmaduria v2 — Propuesta de Arquitectura
**Fecha:** 2026-08-05  
**Estado:** Diseño técnico. Sin implementación aprobada.  
**Referencia:** `docs/auditorias/desarmaduria_templates_audit.md`

---

## 1. Problema

La auditoría de templates (2026-08-05) identificó tres categorías de problemas que impiden escalar el módulo:

### 1.1 Modelo de stock inconsistente

- `finalizar_venta_desde_inventario` decrementaba `PiezaDesarme.cantidad` sin actualizar `estado_pieza` a `VENDIDA` cuando llegaba a cero. **(Corregido en P0)**
- El storefront no filtraba por `cantidad__gt=0`, exponiendo piezas agotadas. **(Corregido en P0)**
- No existía bloqueo de filas (`select_for_update`) antes de decrementar stock. **(Corregido en P0)**

### 1.2 Dos flujos de venta paralelos e incompatibles

| Flujo | Modelo | Stock | Integración |
|-------|--------|-------|-------------|
| Venta rápida | `VentaDesarme` + `LineaVentaDesarme` | Correcto | Ninguna |
| Venta inventario | `Documento` + `LineaRepuesto` | Tenía bug | Contable completa |

Cada flujo tiene su propia lógica de descuento de stock, sus propios templates y no comparte datos.

### 1.3 Ausencia de etapas explícitas del ciclo de vida

Una pieza confirmada en `revisar_vehiculo` aparece inmediatamente en el kiosko con `estado_pieza=DISPONIBLE`. No existe una distinción entre:
- Pieza **confirmada** (existe en BD, no desmontada físicamente)
- Pieza **desmontada y almacenada** (tiene ubicación física)
- Pieza **publicada** (visible en kiosko y storefront)

El resultado práctico: el kiosko muestra piezas que no están físicamente listas para venta.

### 1.4 Dos vistas de inventario sin convergencia

`inventario_vehiculo.html` (994L) e `inventario_inteligente.html` (53L + partials) sirven el mismo propósito con lógicas y templates diferentes. La vista clásica tiene su propio formulario de venta en línea.

---

## 2. Decisión central

> **Al crear el vehículo, todas las piezas aplicables aparecen presumidas y seleccionadas por defecto, pero no se convierten en inventario definitivo ni se publican en el kiosko hasta que el operador lo decide de forma explícita.**

Esto implica:
1. `SugerenciaPiezaDesarme` es el registro pre-inventario. Persiste en `PENDIENTE` hasta que el operador actúa.
2. `PiezaDesarme` solo existe cuando el operador confirma. En ese momento tiene `publicada=False`.
3. La transición `publicada=False → publicada=True` es el acto explícito de "Publicar en kiosko".
4. El kiosko filtra por `publicada=True AND estado_pieza=DISPONIBLE AND cantidad__gt=0 AND activo=True`.

---

## 3. Nuevo flujo completo

```
CREAR VEHÍCULO
└── vehiculo_form.html
    ├── Datos del vehículo (marca, modelo, año, patente, VIN)
    ├── Inspector SVG de daños de carrocería → InspeccionIngreso + DanoInspeccion
    ├── Datos del vendedor y costo de adquisición
    └── POST → inicializar_sugerencias() → SugerenciaPiezaDesarme × N (PENDIENTE)
        └── REDIRECT → Centro de Operaciones

CENTRO DE OPERACIONES (nuevo hub)
└── centro_operaciones.html (nuevo template sobre ver_vehiculo.html)
    ├── Panel de estado del vehículo (etapa actual, KPIs)
    ├── Acciones disponibles según etapa:
    │   ├── [INGRESADO]    → Inspeccionar excepciones, Confirmar piezas
    │   ├── [CONFIRMADO]   → Desmontar, Almacenar
    │   ├── [EN_ALMACEN]   → Publicar, Agregar pieza suelta
    │   ├── [PUBLICADO]    → Ver kiosko, Reservar, Vender
    │   └── [VENDIENDO]    → Analizar, Cerrar vehículo
    └── Historial de acciones

INSPECCIONAR EXCEPCIONES
└── revisar_vehiculo.html (existente, sin cambios al HTML)
    ├── SugerenciaPiezaDesarme por zona con estado PENDIENTE/CONFIRMADA/DESCARTADA
    ├── Acciones: confirmar | descartar | reabrir | agregar
    ├── Al confirmar → PiezaDesarme creada con publicada=False
    └── Al finalizar → vehiculo.etapa → CONFIRMADO

DESMONTAR
└── scanner_vehiculo.html (rol: tracking de desmonte físico)
    ├── Marcar piezas como desmontadas (nuevo estado físico o campo)
    ├── Asignar ubicación física por pieza
    └── Al completar → vehiculo.etapa → EN_ALMACEN

ALMACENAR
└── Centro de Operaciones (panel de ubicaciones)
    ├── Vista de piezas sin ubicación física
    ├── Batch: asignar ubicación a múltiples piezas
    └── Al asignar todas → vehiculo permanece en etapa EN_ALMACEN

PUBLICAR
└── Centro de Operaciones → acción "Publicar piezas"
    ├── Selección de piezas a publicar (por zona o todas)
    ├── Revisión de precios antes de publicar
    ├── POST → pieza.publicada = True → visible en kiosko
    └── vehiculo.etapa → PUBLICADO

RESERVAR
└── Desde kiosko o panel interno
    ├── estado_pieza = RESERVADA
    ├── Datos del comprador potencial
    └── Tiempo límite de reserva (configurable)

VENDER
└── inventario_inteligente.html (canónico único)
    └── → confirmar_venta_desde_inventario.html
        └── → Documento + LineaRepuesto (flujo canónico único)
            ├── PiezaDesarme.cantidad -= cantidad vendida
            ├── Si cantidad == 0 → estado_pieza = VENDIDA
            └── REDIRECT → Documento imprimible

ANALIZAR RENTABILIDAD
└── reportes.html (existente) + nuevas métricas v2
    ├── Costo vs ingresos por vehículo
    ├── % de piezas vendidas / publicadas / descartadas
    ├── Días promedio hasta primera venta
    └── ROI por marca/modelo

CERRAR VEHÍCULO
└── Centro de Operaciones → acción "Cerrar vehículo"
    ├── Verifica que no haya piezas en estado RESERVADA
    ├── Piezas DISPONIBLE restantes → SCRAP o FALTANTE (decisión del operador)
    └── vehiculo.estado_desarme = CERRADO
```

---

## 3.1 Módulo "Así va tu negocio" (estadísticas de rentabilidad)

El flujo de operación genera datos que el operador necesita para tomar decisiones. Este módulo los convierte en información accionable en lenguaje de negocio, no en tablas de datos.

Dos niveles:
- **Panel por vehículo** — embebido en el Centro de Operaciones. Responde: ¿este auto está siendo rentable?
- **Dashboard empresa** — pantalla dedicada `estadisticas.html`. Responde: ¿cómo va mi negocio de desarmaduria?

Las seis preguntas que siempre responde:
1. ¿Cuánto entró? (costo de adquisición)
2. ¿Cuánto salió? (ingresos generados)
3. ¿Cuánto gané? (ganancia bruta)
4. ¿Cuánto queda por recuperar? (valor potencial restante publicado)
5. ¿Qué requiere atención? (alertas activas)
6. ¿Qué conviene hacer ahora? (acción sugerida por alerta)

Nombre visible: **"Así va tu negocio"**

Detalle completo: `docs/arquitectura/desarmaduria_v2_estadisticas_negocio.md`  
Experiencia de usuario: `docs/arquitectura/desarmaduria_v2_experiencia_humana.md`

---

## 4. Principios de diseño

### 4.1 Una sola fuente de verdad para stock
`PiezaDesarme.cantidad` es el único contador. El `estado_pieza` es derivado de `cantidad` y de las transiciones explícitas. El campo `activo` es el soft-delete operacional. El campo `publicada` (nuevo) es la compuerta del kiosko.

### 4.2 Una sola vía de venta canónica
`Documento + LineaRepuesto` con `origen_repuesto=ORIGEN_DESARME`. `VentaDesarme` se mantiene pero no recibe nuevas funcionalidades; su UI se convierte en wrapper sobre el flujo canónico.

### 4.3 El Centro de Operaciones como hub único
`ver_vehiculo.html` se expande (o se reemplaza) en un hub que refleja la etapa actual del vehículo y expone solo las acciones pertinentes a esa etapa. Elimina la confusión de tener múltiples puntos de entrada (scanner, inventario, revisar) sin contexto de etapa.

### 4.4 Transiciones explícitas, no implícitas
Ninguna transición de estado debe ocurrir como efecto secundario de otra operación sin intención del operador. La publicación en el kiosko es un acto deliberado.

### 4.5 Retro-compatibilidad en modelos
`activo=False` equivale a `publicada=False` para el kiosko actual. El nuevo campo `publicada` permite separar "pieza inactivada" (soft-delete) de "pieza no publicada aún" (en proceso).

---

## 5. Impacto por capa (diseño, sin implementar)

### 5.1 Modelos
- `PiezaDesarme`: añadir `publicada` (BooleanField, default=False), `etapa_fisica` (CharField choices).
- `VehiculoDesarme`: añadir `etapa` (CharField, choices de las etapas del flujo) o reutilizar `estado_desarme` con nuevos valores.
- `SugerenciaPiezaDesarme`: sin cambios de esquema. Solo cambios en cuándo se inicializa y cómo se muestra.

### 5.2 Views
- Nueva view: `centro_operaciones` (reemplaza `ver_vehiculo` como punto de entrada).
- Nueva view: `dashboard_estadisticas` en `views_stats.py` — dashboard "Así va tu negocio".
- Nueva función: `kpis_vehiculo(vehiculo)` en `views_stats.py` — KPIs por vehículo para el Centro de Operaciones.
- `revisar_vehiculo`: sin cambios de lógica. Nuevo botón "Finalizar revisión" para transición de etapa.
- `scanner_vehiculo`: nuevo rol como tracker de desmonte físico (no solo precio/estado).
- `finalizar_venta_desde_inventario`: ya corregido en P0.
- Deprecar: `iniciar_venta_rapida`, `confirmar_venta_rapida` (mantener pero sin nuevas features).

### 5.3 Templates
- `centro_operaciones.html` (nuevo): panel de etapa, acciones contextuales, KPIs rápidos por vehículo.
- `dashboard_asi_va_tu_negocio.html` (nuevo): dashboard de estadísticas empresa — "Así va tu negocio".
- `partials/_kpis_vehiculo.html` (nuevo): partial de KPIs por vehículo, incluido desde `centro_operaciones.html`.
- `inventario_inteligente.html`: canónico único para selección y venta.
- `inventario_vehiculo.html`: deprecar progresivamente (no eliminar en esta fase).
- `ventas/confirmar.html`: congelar en mantenimiento.
- `dashboard_financiero.html`: eliminar (huérfano, sin URL).
- `partials/_inventario_sale_panel.html`: eliminar (huérfano, sin include).

### 5.4 Storefront
- Añadir `publicada=True` al filtro base. **(Pendiente — no breaking si publicada tiene default True en migración para registros existentes)**
- `cantidad__gt=0` ya añadido en P0.

---

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Registros existentes con `publicada` null tras migración | Alta | Medio | Data migration: todos los `PiezaDesarme` activos con `estado_pieza=DISPONIBLE` → `publicada=True` |
| Operadores confundidos con nueva etapa "Publicar" | Media | Alto | El kiosko muestra en tiempo real. Flujo de onboarding en Centro de Operaciones |
| `VentaDesarme` con datos históricos no migrados | Baja | Bajo | VentaDesarme se mantiene; no hay migración de datos necesaria |
| `inventario_vehiculo.html` con usuarios activos | Media | Bajo | Deprecar con redirect hacia inventario_inteligente, no eliminar |
| select_for_update silencioso en SQLite (dev) | Alta | Bajo | Ya documentado. Tests en PostgreSQL (clon prod) validan el comportamiento real |

---

## 7. Lo que NO cambia

- `SugerenciaPiezaDesarme` como etapa pre-inventario: correcto y se mantiene.
- `revisar_vehiculo.html`: lógica correcta, solo cambios menores de UX.
- `catalogo_operativo.py` y `catalogo_piezas.py`: fuente estática del catálogo, intactos.
- Multi-tenant con `TenantScoped`: patrón correcto, sin cambios.
- `_generar_numero_documento` con `select_for_update`: ya correcto.
- Tests existentes: todos pasan, no se tocan.
