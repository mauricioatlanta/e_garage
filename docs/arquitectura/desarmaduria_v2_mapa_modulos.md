# Desarmaduria v2 — Mapa de Módulos
**Fecha:** 2026-08-05  
**Estado:** Diseño técnico. Sin implementación aprobada.  
**Referencia:** `docs/arquitectura/desarmaduria_v2_propuesta.md`

---

## 1. Visión general

```
┌─────────────────────────────────────────────────────────────┐
│                    PANEL OPERATIVO                          │
│  (autenticado, tenant-scoped, namespace: cl_es→desarme)     │
│                                                             │
│  Crear Vehículo → Centro de Operaciones → [Etapas]         │
│                         │                                   │
│              ┌──────────┴──────────┐                        │
│              │  Revisar / Confirmar│                        │
│              │  Desmontar          │                        │
│              │  Publicar           │                        │
│              │  Vender             │                        │
│              └─────────────────────┘                        │
└────────────────────────────┬────────────────────────────────┘
                             │ publicada=True
┌────────────────────────────▼────────────────────────────────┐
│                    STOREFRONT PÚBLICO                        │
│  kiosko_centralizado (multi-empresa)                        │
│  tienda_empresa (single-empresa)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Módulos por etapa del flujo

### 2.1 CREAR VEHÍCULO

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/taller/desarme/vehiculo_form.html` (887 L) |
| **View** | `taller/desarme/views.py::crear_vehiculo` (~L 577) |
| **URL** | `<pais>/es/desarme/vehiculos/crear/` |
| **URL name** | `desarme:crear_vehiculo` |
| **Modelos escritos** | `VehiculoDesarme`, `SugerenciaPiezaDesarme` × N (PENDIENTE) |
| **Modelos leídos** | `CatalogoRepuestoEmpresa`, `catalogo_operativo.py` |
| **Hooks post-save** | `inicializar_sugerencias(vehiculo)` en `views.py` |
| **Redirect destino** | `centro_operaciones` (v2) / `revisar_vehiculo` (v1 actual) |

**Responsabilidades del módulo:**
- Capturar datos básicos del vehículo (marca, modelo, año, patente, VIN, costo adquisición)
- Inspector SVG de daños de carrocería → `InspeccionIngreso` + `DanoInspeccion`
- Datos del vendedor
- Inicializar las `SugerenciaPiezaDesarme` presumidas en PENDIENTE

**No es responsabilidad de este módulo:**
- Decidir cuántas piezas se confirmarán
- Asignar precios definitivos
- Publicar en kiosko

---

### 2.2 CENTRO DE OPERACIONES (nuevo en v2)

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/taller/desarme/centro_operaciones.html` (nuevo) |
| **View** | `taller/desarme/views.py::centro_operaciones` (nueva) |
| **URL** | `<pais>/es/desarme/vehiculos/<pk>/centro/` |
| **URL name** | `desarme:centro_operaciones` |
| **Modelos leídos** | `VehiculoDesarme`, `PiezaDesarme`, `SugerenciaPiezaDesarme` |

**Responsabilidades del módulo:**
- Mostrar etapa actual del vehículo (`VehiculoDesarme.etapa`)
- Mostrar KPIs rápidos: piezas confirmadas, publicadas, vendidas, ingresos
- Exponer solo las acciones pertinentes a la etapa actual:
  - INGRESADO → botón "Inspeccionar/Confirmar piezas"
  - CONFIRMADO → botón "Iniciar desmonte"
  - EN_ALMACEN → botón "Publicar piezas"
  - PUBLICADO → botón "Ver en kiosko", "Registrar venta"
  - VENDIENDO → botón "Analizar rentabilidad", "Cerrar vehículo"
- Historial de acciones del vehículo

**No es responsabilidad de este módulo:**
- Procesar la lógica de cada acción (delegado a la view/template de esa etapa)

---

### 2.3 INSPECCIONAR EXCEPCIONES / CONFIRMAR PIEZAS

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/taller/desarme/revisar_vehiculo.html` (existente) |
| **View** | `taller/desarme/views.py::revisar_vehiculo` (~L 1637) |
| **URL** | `<pais>/es/desarme/vehiculos/<pk>/revisar/` |
| **URL name** | `desarme:revisar_vehiculo` |
| **Modelos escritos** | `SugerenciaPiezaDesarme` (estado), `PiezaDesarme` (crear) |
| **AJAX endpoints** | `confirmar`, `descartar`, `reabrir`, `agregar` |

**Responsabilidades del módulo:**
- Mostrar `SugerenciaPiezaDesarme` por zona con estado visual
- Permitir: confirmar → crea `PiezaDesarme` con `publicada=False`
- Permitir: descartar → marca sugerencia como DESCARTADA
- Permitir: reabrir → vuelve sugerencia a PENDIENTE
- Permitir: agregar pieza sin sugerencia previa
- Botón "Finalizar revisión" → `vehiculo.etapa = CONFIRMADO`

**Invariante:** Al salir de esta pantalla, ninguna `PiezaDesarme` tiene `publicada=True`.

---

### 2.4 DESMONTAR (tracker físico)

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/taller/desarme/scanner_vehiculo.html` (existente, rol cambia) |
| **View** | `taller/desarme/views.py::scanner_vehiculo` |
| **URL** | `<pais>/es/desarme/vehiculos/<pk>/scanner/` |
| **URL name** | `desarme:scanner_vehiculo` |
| **Modelos escritos** | `PiezaDesarme.etapa_fisica`, `PiezaDesarme.ubicacion_fisica` |

**Responsabilidades del módulo:**
- Marcar piezas como físicamente desmontadas (`etapa_fisica=DESMONTADA`)
- Asignar ubicación física (estantería, caja, zona)
- Al completar todas → `vehiculo.etapa = EN_ALMACEN`

**Cambio de rol respecto a v1:** En v1 `scanner_vehiculo.html` era un punto de entrada de precios/estado. En v2 es exclusivamente tracker de estado físico y ubicación.

---

### 2.5 PUBLICAR

| Elemento | Valor |
|----------|-------|
| **Template** | `centro_operaciones.html` (panel de publicación, sección dentro del hub) |
| **View** | `taller/desarme/views.py::publicar_piezas` (nueva, o acción en centro_operaciones) |
| **URL** | `<pais>/es/desarme/vehiculos/<pk>/publicar/` |
| **URL name** | `desarme:publicar_piezas` |
| **Modelos escritos** | `PiezaDesarme.publicada = True` |

**Responsabilidades del módulo:**
- Mostrar lista de piezas con `publicada=False` del vehículo
- Permitir selección individual o batch
- Revisión de precio antes de publicar
- POST → `pieza.publicada = True` → pieza aparece en kiosko
- → `vehiculo.etapa = PUBLICADO`

---

### 2.6 RESERVAR

| Elemento | Valor |
|----------|-------|
| **Template** | kiosko o panel interno (TBD en P3) |
| **View** | nueva view en `views_inventario.py` o `views.py` |
| **URL** | `<pais>/es/desarme/piezas/<pk>/reservar/` |
| **Modelos escritos** | `PiezaDesarme.estado_pieza = RESERVADA`, `ReservaDesarme` (nuevo modelo, P4) |

**Responsabilidades del módulo:**
- Cambiar `estado_pieza` de `DISPONIBLE` a `RESERVADA`
- Registrar datos del comprador potencial
- Establecer tiempo límite de reserva (configurable)
- Permitir liberar reserva (→ DISPONIBLE) o confirmar venta (→ flujo canónico)

---

### 2.7 VENDER (flujo canónico)

| Elemento | Valor |
|----------|-------|
| **Template selector** | `templates/taller/desarme/inventario_inteligente.html` (canónico único) |
| **Template confirmar** | `templates/taller/desarme/confirmar_venta_desde_inventario.html` |
| **View crear sesión** | `taller/desarme/views_inventario.py::crear_venta_desde_inventario` |
| **View finalizar** | `taller/desarme/views_inventario.py::finalizar_venta_desde_inventario` |
| **URLs** | `<pk>/inventario/` → `<pk>/confirmar-venta-desde-inventario/` → `<pk>/finalizar-venta-desde-inventario/` |
| **Modelos escritos** | `Documento`, `LineaRepuesto` (con `origen_repuesto=ORIGEN_DESARME`) |
| **Modelos actualizados** | `PiezaDesarme.cantidad`, `PiezaDesarme.estado_pieza` |

**Responsabilidades del módulo:**
- Selección de piezas a vender (qty, precio negociado)
- Confirmación con datos del cliente o cliente rápido
- `select_for_update()` + `transaction.atomic()` antes de decrementar stock
- `estado_pieza = VENDIDA` cuando `cantidad == 0`
- Redirect a documento imprimible

**Flujo canónico único:** Solo `Documento + LineaRepuesto`. `VentaDesarme` no recibe nuevas funcionalidades.

---

### 2.8 ANALIZAR RENTABILIDAD

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/taller/desarme/reportes.html` (existente + nuevas métricas) |
| **View** | existente + nuevas métricas v2 |
| **URL** | `<pais>/es/desarme/vehiculos/<pk>/reportes/` |
| **Modelos leídos** | `VehiculoDesarme`, `PiezaDesarme`, `Documento`, `LineaRepuesto` |

**Métricas v2 pendientes:**
- Costo adquisición vs ingresos totales (ROI por vehículo)
- % piezas vendidas / publicadas / descartadas
- Días promedio hasta primera venta
- ROI por marca/modelo (agregado empresa)

---

### 2.9 CERRAR VEHÍCULO

| Elemento | Valor |
|----------|-------|
| **Template** | acción en `centro_operaciones.html` |
| **View** | nueva acción `cerrar_vehiculo` en `views.py` |
| **URL** | `<pais>/es/desarme/vehiculos/<pk>/cerrar/` |
| **Modelos escritos** | `PiezaDesarme.estado_pieza` (SCRAP/FALTANTE), `VehiculoDesarme.estado_desarme = CERRADO` |

**Responsabilidades del módulo:**
- Verificar que no haya piezas en RESERVADA (no se puede cerrar)
- Para piezas DISPONIBLE restantes → operador decide: SCRAP o FALTANTE
- `VehiculoDesarme.estado_desarme = CERRADO`
- Archivar vehículo (sin eliminar datos)

---

### 2.10 STOREFRONT PÚBLICO

#### kiosko_centralizado (multi-empresa)

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/public/kiosko.html` |
| **View** | `taller/views_extra/storefront.py::kiosko_centralizado` |
| **URL** | `/kiosko/` |
| **Filtro base** | `empresa__kiosko_autorizado=True, activo=True, estado_pieza=DISPONIBLE, cantidad__gt=0` |
| **Filtro v2 adicional** | `publicada=True` |

#### tienda_empresa (single-empresa)

| Elemento | Valor |
|----------|-------|
| **Template** | `templates/public/tienda.html` |
| **View** | `taller/views_extra/storefront.py::tienda_empresa` (a.k.a. `_tienda_storefront_render`) |
| **URL** | `/<slug>/tienda/` |
| **Filtro base** | `empresa=empresa, activo=True, estado_pieza=DISPONIBLE, cantidad__gt=0` |
| **Filtro v2 adicional** | `publicada=True` |

---

### 2.11 "ASÍ VA TU NEGOCIO" — Estadísticas y Rentabilidad

| Elemento | Valor |
|----------|-------|
| **Template dashboard** | `templates/taller/desarme/dashboard_asi_va_tu_negocio.html` (nuevo) |
| **Template partial** | `templates/taller/desarme/partials/_kpis_vehiculo.html` (nuevo) |
| **View** | `taller/desarme/views_stats.py::dashboard_estadisticas` (nuevo archivo) |
| **Helpers** | `kpis_vehiculo(vehiculo)`, `kpis_empresa(empresa, periodo)` en `views_stats.py` |
| **URL dashboard** | `<pais>/es/desarme/estadisticas/` |
| **URL name** | `desarme:estadisticas` |
| **Modelos leídos** | `VehiculoDesarme`, `PiezaDesarme`, `Documento`, `LineaRepuesto`, `VentaDesarme`, `LineaVentaDesarme` |

**Las seis preguntas que responde:**
1. ¿Cuánto entró? — `VehiculoDesarme.costo_adquisicion`
2. ¿Cuánto salió? — `SUM(LineaRepuesto.subtotal)` + `SUM(LineaVentaDesarme.cantidad × precio)`
3. ¿Cuánto gané? — ingresos − costo (ganancia bruta)
4. ¿Cuánto queda por recuperar? — `SUM(PiezaDesarme.precio_venta_sugerido × cantidad)` donde `estado_pieza IN (DISPONIBLE, RESERVADA) AND activo=True` (incluye no publicadas, para reflejar valor total disponible)
5. ¿Qué requiere atención? — alertas activas: piezas sin precio, autos estancados, reservas vencidas
6. ¿Qué conviene hacer? — acción directa por alerta

**Nombre visible:** "Así va tu negocio"

**Dos niveles de agregación:**
- Panel por vehículo → embebido en `centro_operaciones.html` via `_kpis_vehiculo.html`
- Dashboard empresa → `dashboard_asi_va_tu_negocio.html` (pantalla propia)

**Detalle completo de fórmulas, fuentes de datos y criterios de aceptación:**  
`docs/arquitectura/desarmaduria_v2_estadisticas_negocio.md`

**Detalle de experiencia humana y lenguaje:**  
`docs/arquitectura/desarmaduria_v2_experiencia_humana.md`

---

## 3. Mapa de templates — estado actual vs v2

| Template | Líneas | Estado actual | Estado v2 |
|----------|--------|---------------|-----------|
| `vehiculo_form.html` | 887 | Activo | Sin cambios |
| `revisar_vehiculo.html` | ~400 | Activo | Botón "Finalizar revisión" + transición etapa |
| `scanner_vehiculo.html` | ~200 | Activo | Rol cambia: tracker físico |
| `inventario_inteligente.html` | 53 + partials | Activo | Canónico único |
| `inventario_vehiculo.html` | 994 | Activo | Deprecar → redirect |
| `confirmar_venta_desde_inventario.html` | ~150 | Activo | Sin cambios |
| `kiosko.html` | ~300 | Activo | Añadir filtro `publicada=True` |
| `tienda.html` | ~300 | Activo | Añadir filtro `publicada=True` |
| `reportes.html` | ~200 | Activo | Nuevas métricas v2 |
| `centro_operaciones.html` | — | **No existe** | **Crear (nuevo hub)** |
| `dashboard_asi_va_tu_negocio.html` | — | **No existe** | **Crear (estadísticas empresa)** |
| `partials/_kpis_vehiculo.html` | — | **No existe** | **Crear (KPIs por vehículo)** |
| `dashboard_financiero.html` | ~100 | **Huérfano** | **Eliminar** |
| `partials/_inventario_sale_panel.html` | ~50 | **Huérfano** | **Eliminar** |

---

## 4. Mapa de URLs y views

### Namespace: `desarme` (bajo `cl_es` → `chile` → `taller`)

```
GET  vehiculos/crear/                              crear_vehiculo
POST vehiculos/crear/                              crear_vehiculo

GET  vehiculos/<pk>/centro/                        centro_operaciones          [NUEVO v2]
GET  vehiculos/<pk>/revisar/                       revisar_vehiculo
POST vehiculos/<pk>/revisar/                       revisar_vehiculo (AJAX)

GET  vehiculos/<pk>/scanner/                       scanner_vehiculo
POST vehiculos/<pk>/scanner/                       scanner_vehiculo

POST vehiculos/<pk>/publicar/                      publicar_piezas             [NUEVO v2]
POST vehiculos/<pk>/cerrar/                        cerrar_vehiculo             [NUEVO v2]

GET  vehiculos/<pk>/inventario/                    crear_venta_desde_inventario
POST vehiculos/<pk>/inventario/                    crear_venta_desde_inventario
GET  vehiculos/<pk>/confirmar-venta-desde-inventario/   confirmar_venta_desde_inventario
POST vehiculos/<pk>/finalizar-venta-desde-inventario/   finalizar_venta_desde_inventario

GET  vehiculos/<pk>/reportes/                      reportes_vehiculo

GET  estadisticas/                                 dashboard_estadisticas      [NUEVO v2 — "Así va tu negocio"]

GET  /kiosko/                                      kiosko_centralizado
GET  /<slug>/tienda/                               tienda_empresa
```

---

## 5. Mapa de modelos — relaciones clave

```
EmpresaDesarme (Empresa)
    │
    ├── VehiculoDesarme
    │       │  etapa: INGRESADO|CONFIRMADO|EN_ALMACEN|PUBLICADO|VENDIENDO|CERRADO  [nuevo]
    │       │  estado_desarme: (existente)
    │       │
    │       ├── SugerenciaPiezaDesarme   [pre-inventario]
    │       │       estado: PENDIENTE|CONFIRMADA|DESCARTADA
    │       │
    │       └── PiezaDesarme            [inventario real]
    │               cantidad: int
    │               estado_pieza: DISPONIBLE|RESERVADA|VENDIDA|DANADA|SCRAP|FALTANTE
    │               activo: bool         (soft-delete)
    │               publicada: bool      [nuevo v2] (compuerta kiosko)
    │               etapa_fisica: str    [nuevo v2] CONFIRMADA|DESMONTADA|ALMACENADA
    │               ubicacion_fisica: str
    │
    └── Documento (origen_repuesto=ORIGEN_DESARME)
            └── LineaRepuesto
                    └── FK → PiezaDesarme
```

---

## 6. Flujo de datos — sesión de venta

```
inventario_inteligente.html
    │  POST items[]
    ▼
crear_venta_desde_inventario (view)
    │  session["venta_desde_inventario"] = {vehiculo_id, items}
    ▼
confirmar_venta_desde_inventario.html
    │  POST (datos cliente / cliente_rápido)
    ▼
finalizar_venta_desde_inventario (view)
    │  PiezaDesarme.select_for_update()  ← lock de filas
    │  validar stock
    │  crear Documento + LineaRepuesto × N
    │  PiezaDesarme.cantidad -= cant
    │  if cantidad == 0 → estado_pieza = VENDIDA
    ▼
Documento imprimible (redirect)
```

---

## 7. Dependencias entre módulos

```
crear_vehiculo
    └── inicializa → SugerenciaPiezaDesarme

revisar_vehiculo
    ├── lee ← SugerenciaPiezaDesarme
    └── crea → PiezaDesarme (publicada=False)

scanner_vehiculo / publicar
    └── actualiza → PiezaDesarme (etapa_fisica, publicada)

storefront (kiosko / tienda)
    └── lee ← PiezaDesarme WHERE publicada=True AND activo=True AND estado=DISPONIBLE AND cantidad>0

finalizar_venta_desde_inventario
    ├── lee ← PiezaDesarme (select_for_update)
    ├── crea → Documento, LineaRepuesto
    └── actualiza → PiezaDesarme (cantidad, estado_pieza)

cerrar_vehiculo
    └── actualiza → PiezaDesarme (estado), VehiculoDesarme (estado_desarme)

dashboard_estadisticas / _kpis_vehiculo
    ├── lee ← VehiculoDesarme (costo_adquisicion, etapa)
    ├── lee ← PiezaDesarme (precio_venta_sugerido, cantidad, estado, publicada)
    ├── lee ← LineaRepuesto (subtotal, origen_repuesto=ORIGEN_DESARME)
    └── lee ← LineaVentaDesarme (cantidad × precio_unitario)
```
