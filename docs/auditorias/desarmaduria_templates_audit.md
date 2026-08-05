# Auditoría de Templates — Módulo Desarmaduria
**Fecha:** 2026-08-05  
**Alcance:** Solo lectura. Sin modificaciones a vistas, modelos, forms, templates ni migraciones.  
**Método:** Inspección directa de archivos, grep de símbolos, trazado de rutas URL → view → template.

---

## 1. Inventario completo de templates

### 1.1 Panel operador — `templates/taller/desarme/`

| # | Archivo | Líneas | View que lo renderiza | Función |
|---|---------|--------|-----------------------|---------|
| 1 | `vehiculo_form.html` | 887 | `crear_vehiculo` (v:577), `editar_vehiculo` (v:771) | Alta y edición de VehiculoDesarme. Incluye SVG interactivo de daños |
| 2 | `ver_vehiculo.html` | 391 | `ver_vehiculo` (v:623) | Hub de detalle: links a scanner, inventarios, piezas |
| 3 | `revisar_vehiculo.html` | 540 | `revisar_vehiculo` (v:1637) | Revisión de SugerenciaPiezaDesarme por zona. AJAX JSON |
| 4 | `scanner_vehiculo.html` | 1092 | `scanner_vehiculo` (v:1252) | UI futurista por zona. Inline edit de estado/precio. CTA vender |
| 5 | `inventario_vehiculo.html` | 994 | `inventario_vehiculo` (v:1055) | Inventario "clásico" tabla. Tiene formulario de venta propio |
| 6 | `inventario_inteligente.html` | 53 | `inventario_inteligente` (vi:31) | Shell Alpine.js. Incluye los 4 partials de inventario |
| 7 | `configurar_catalogo.html` | 126 | `configurar_catalogo` (v:2122) | Grid incluido/precio por pieza del catálogo |
| 8 | `lista_vehiculos.html` | 255 | `lista_vehiculos` (v:375) | Lista con filtros de estado y búsqueda |
| 9 | `lista_vehiculos_partial.html` | 48 | `lista_vehiculos` (v:437, AJAX) | Respuesta parcial para búsqueda en tiempo real |
| 10 | `lista_piezas.html` | 327 | `lista_piezas` (v:818) | Lista global de piezas con filtros vehiculo/estado |
| 11 | `pieza_form.html` | 256 | `crear_pieza` (v:892), `editar_pieza` (v:1020) | Alta/edición pieza vinculada a vehículo |
| 12 | `pieza_suelta_form.html` | 160 | `crear_pieza_suelta` (v:953) | Alta pieza sin vehículo (crea VehiculoDesarme placeholder) |
| 13 | `confirmar_venta_desde_inventario.html` | 374 | `confirmar_venta_desde_inventario` (vi:386), `finalizar_venta_desde_inventario` (vi:451, 472) | Confirmación de venta vía inventario inteligente. Crea Documento |
| 14 | `dashboard.html` | 466 | `index` (v:259) | Dashboard operativo con KPIs y últimas piezas/vehículos |
| 15 | `dashboard_financiero.html` | 73 | **NINGUNA** | ⚠️ HUÉRFANO — extends `base.html` genérico, sin URL en urls_desarme.py |
| 16 | `reportes.html` | 240 | `reportes_desarme` (v:2089) | Reportes financieros y analytics de inventario |
| 17 | `crear_interchange.html` | 234 | `crear_interchange` (v:2010, 2017, 2066) | Alta de código interchange |
| 18 | `lista_interchange.html` | 212 | `lista_interchange` (v:1971) | Lista de intercambiabilidad |
| 19 | `unavailable.html` | 17 | Fallback en `urls_desarme.py` | Página de error si el módulo no importa |
| 20 | `ventas/confirmar.html` | 122 | `confirmar_venta_rapida` (vv:100) | Confirmación venta rápida — crea VentaDesarme |
| 21 | `ventas/lista.html` | 76 | `lista_ventas` (vv:207) | Lista ventas rápidas (VentaDesarme) |
| 22 | `ventas/recibo.html` | 207 | `recibo_venta` (vv:196) | Recibo de VentaDesarme con detalle de líneas |

> Abreviaciones: `v:` = `taller/desarme/views.py`, `vi:` = `views_inventario.py`, `vv:` = `views_venta.py`

**Subtotal panel operador: 22 templates, 7.150 líneas**

---

### 1.2 Partials de inventario — `templates/taller/desarme/partials/`

| # | Archivo | Líneas | Incluido por | Estado |
|---|---------|--------|--------------|--------|
| 23 | `_inventario_toolbar.html` | 153 | `inventario_inteligente.html:36` | Activo |
| 24 | `_inventario_grid.html` | 89 | `inventario_inteligente.html:40` | Activo |
| 25 | `_inventario_drawer.html` | 134 | `inventario_inteligente.html:45` | Activo |
| 26 | `_inventario_mobile_bar.html` | 131 | `inventario_inteligente.html:46` | Activo |
| 27 | `_inventario_sale_panel.html` | 89 | **NINGUNO** | ⚠️ HUÉRFANO |

**Subtotal partials: 5 archivos, 596 líneas**

---

### 1.3 Kiosko y storefront público — `templates/public/storefront/`

| # | Archivo | Líneas | View | URL | Función |
|---|---------|--------|------|-----|---------|
| 28 | `kiosko.html` | 201 | `kiosko_centralizado` (storefront.py:253) | `/kiosko/` | Multi-empresa; filtra `kiosko_autorizado=True` |
| 29 | `tienda.html` | 402 | `_tienda_storefront_render` (storefront.py:40) | `/empresa/<id>/`, `/<slug>/` | Storefront individual por empresa |
| 30 | `_card_pieza.html` | 70 | — | — | Incluido solo por `kiosko.html:171` |
| 31 | `_modal_pieza.html` | 102 | — | — | Incluido por `kiosko.html:195` y `tienda.html:389` |
| 32 | `tienda_inactiva.html` | ~20 | `_tienda_storefront_render` (storefront.py:43) | — | Respuesta 410 si empresa inactiva |

**Subtotal storefront: 5 templates, ~795 líneas**

---

### 1.4 Inspección de ingreso — `templates/taller/documentos/`

| # | Archivo | Líneas | View | URL namespace | Conexión a desarme |
|---|---------|--------|------|---------------|-------------------|
| 33 | `inspeccion_ingreso_form.html` | 742 | `crear_inspeccion_ingreso` | `documentos:crear_inspeccion_ingreso` | Via modelo: `InspeccionIngreso.vehiculo_desarme FK` |
| 34 | `inspeccion_ingreso_detalle.html` | 210 | `ver_inspeccion_ingreso` | `documentos:ver_inspeccion_ingreso` | Idem |

**Nota:** Ningún template del módulo `desarme/` linka directamente a estas vistas. La conexión con el flujo de desarmaduria existe solo a nivel de modelo y de signal (`_sincronizar_estado_piezas`, `views.py:496-530`).

---

### 1.5 Vehículos regulares — `templates/taller/common/vehiculos/`

| Archivo | Líneas | Relación con desarme |
|---------|--------|----------------------|
| `vehiculo_form.html` | 1891 | **NINGUNA** — usado por `vehiculos/views_country_aware.py:170` y `views_fbv.py`. Solo vehículos de taller, no de desarme |
| `vehiculo_form.html.BAK_*` × 8 | ~65k total | ⚠️ Archivos de backup manual en el repo. No incluidos por nadie |

---

### 1.6 Otros templates relacionados (lectura, no núcleo)

- `templates/public/landing_desarmadurias.html` — landing marketing, no parte del flujo operativo
- `templates/public/landing_salvage.html` — landing USA, idem

---

## 2. Mapa completo del flujo

```
CREAR VEHÍCULO
└── GET  /desarme/vehiculos/crear/
    └── vehiculo_form.html (887L)
        ├── SVG interactivo 4 vistas carrocería (daños)
        ├── Form: VehiculoDesarmeForm
        └── POST → views.py:577
            ├── VehiculoDesarme.save()
            ├── _guardar_danos_carroceria() → InspeccionIngreso + DanoInspeccion
            └── inicializar_sugerencias() → SugerenciaPiezaDesarme × N (PENDIENTE)
                └── REDIRECT → /vehiculos/<pk>/revisar/

DESPIECE / REVISIÓN
└── GET  /desarme/vehiculos/<pk>/revisar/
    └── revisar_vehiculo.html (540L)
        ├── SugerenciaPiezaDesarme por zona (PENDIENTE / CONFIRMADA / DESCARTADA)
        └── POST (AJAX JSON) → views.py:1637
            ├── action=confirmar → PiezaDesarme.objects.create() (views.py:1768)  ← FUENTE 1
            │   └── SugerenciaPiezaDesarme.pieza_creada → FK a PiezaDesarme
            ├── action=descartar → sugerencia.estado = DESCARTADA
            ├── action=reabrir   → sugerencia.estado = PENDIENTE
            └── action=agregar   → PiezaDesarme.objects.create() (views.py:1866)  ← FUENTE 2

    BYPASS (generar inventario automático)
    └── GET  /desarme/vehiculos/<pk>/generar-inventario/
        └── generar_inventario_vehiculo() → services.py:36
            └── PiezaDesarme.objects.get_or_create() × N  ← FUENTE 3 (sin sugerencias)
                └── REDIRECT → /vehiculos/<pk>/scanner/

VER VEHÍCULO (hub de navegación)
└── GET  /desarme/vehiculos/<pk>/
    └── ver_vehiculo.html (391L)
        ├── → /vehiculos/<pk>/scanner/
        ├── → /vehiculos/<pk>/inventario/
        ├── → /vehiculos/<pk>/inventario-inteligente/
        ├── → /piezas/crear/?vehiculo=<pk>
        └── → /vehiculos/<pk>/revisar/

SCANNER (edición inline)
└── GET  /desarme/vehiculos/<pk>/scanner/
    └── scanner_vehiculo.html (1092L)
        ├── Cards por zona con Alpine.js
        ├── AJAX: api_pieza_actualizar_estado (api:1335) → PiezaDesarme.estado_pieza
        ├── AJAX: api_pieza_actualizar_precio (api:1359) → PiezaDesarme.precio_venta_sugerido
        └── Botón "Vender" → inventario_vehiculo o iniciar_venta_desde_inventario

INVENTARIO (dos vistas paralelas)
├── CLÁSICO
│   └── GET  /desarme/vehiculos/<pk>/inventario/
│       └── inventario_vehiculo.html (994L)
│           ├── Tabla con filtros, Alpine.js
│           ├── Botón "Inventario Inteligente" → inventario-inteligente/
│           ├── Botón "Escáner" → scanner/
│           └── form#inv-venta-form POST → crear_venta_desde_inventario
│               └── ↓ (VENTA VÍA DOCUMENTO, ver abajo)
│
└── INTELIGENTE (moderno)
    └── GET  /desarme/vehiculos/<pk>/inventario-inteligente/
        └── inventario_inteligente.html (53L) + 4 partials (596L)
            ├── _inventario_toolbar.html (153L) — búsqueda y filtros
            ├── _inventario_grid.html (89L)     — cards con checkboxes
            ├── _inventario_drawer.html (134L)  — panel lateral de selección
            └── _inventario_mobile_bar.html (131L) — barra flotante móvil
                └── POST crear_venta_desde_inventario → vi:87

VENTA (dos flujos paralelos e incompatibles)
├── FLUJO A — VÍA DOCUMENTO (inventario → confirmar)
│   └── POST /desarme/vehiculos/<pk>/crear-venta-desde-inventario/
│       → vi:87 → valida stock, guarda en sesión
│       └── GET/POST /vehiculos/<pk>/confirmar-venta-desde-inventario/
│           └── confirmar_venta_desde_inventario.html (374L)
│               └── POST /vehiculos/<pk>/finalizar-venta-desde-inventario/
│                   └── vi:423
│                       ├── Documento.save() (boleta/invoice)
│                       ├── LineaRepuesto × N (origen_repuesto=ORIGEN_DESARME)
│                       ├── PiezaDesarme.update(cantidad=F("cantidad")-cant) ← vi:533
│                       │   ⚠️ NO actualiza estado_pieza si cantidad llega a 0
│                       └── REDIRECT → documentos:imprimir_documento
│
└── FLUJO B — VENTA RÁPIDA (lista_piezas → carrito sesión → VentaDesarme)
    └── POST /desarme/piezas/vender/  (iniciar_venta_desde_lista)
        → vv:46 → carrito en request.session
        └── GET/POST /desarme/ventas/nueva/
            └── ventas/confirmar.html (122L)
                └── POST → vv:100
                    ├── VentaDesarme.save()      ← modelo diferente a Documento
                    ├── LineaVentaDesarme × N    ← modelo diferente a LineaRepuesto
                    ├── pieza.cantidad -= cant
                    ├── if cant ≤ 0: pieza.estado_pieza = ESTADO_VENDIDA
                    └── pieza.save(update_fields=[...])  ← vv:174
    └── GET /desarme/ventas/           → ventas/lista.html (76L)
    └── GET /desarme/ventas/<pk>/recibo/ → ventas/recibo.html (207L)
    └── POST /desarme/ventas/<pk>/anular/ → restaura stock

KIOSKO (vista pública)
└── GET /kiosko/
    └── kiosko_centralizado → storefront.py:253
        ├── PiezaDesarme.filter(
        │     empresa__kiosko_autorizado=True,
        │     estado_pieza=DISPONIBLE        ← filtra solo por estado, NO por cantidad
        │   )
        └── public/storefront/kiosko.html (201L)
            ├── {% include "_card_pieza.html" %} (70L)
            └── {% include "_modal_pieza.html" %} (102L)

└── GET /empresa/<id>/ o /<slug>/
    └── _tienda_storefront_render → storefront.py:40
        ├── mismo filtro que kiosko
        └── public/storefront/tienda.html (402L)
            └── {% include "_modal_pieza.html" %} (102L)
```

---

## 3. Fuente real de stock y estados

### 3.1 Modelo de stock

La fuente autoritativa es `PiezaDesarme` (`taller/models/pieza_desarme.py`):

| Campo | Tipo | Significado |
|-------|------|-------------|
| `cantidad` | `PositiveIntegerField(default=1)` | Unidades físicamente disponibles |
| `estado_pieza` | `CharField(choices=ESTADO_PIEZA_CHOICES)` | Estado semántico de la pieza |
| `activo` | `BooleanField` | Soft-delete operacional |

**Estados posibles** (`pieza_desarme.py:16-28`):
```
DISPONIBLE  → visible en kiosko, vendible
RESERVADA   → en proceso de venta, no disponible
VENDIDA     → cantidad llegó a 0
DANADA      → mal estado, no vendible
SCRAP       → chatarra
FALTANTE    → no se encontró físicamente
```

**Invariante declarado** (`pieza_desarme.py:282-285`): `estado_pieza=VENDIDA` solo es válido cuando `cantidad == 0`. Se valida en `clean()`.

### 3.2 Puntos de creación de PiezaDesarme

| Fuente | Archivo:línea | Vía | Detalles |
|--------|---------------|-----|----------|
| Confirmación en revisar_vehiculo | `views.py:1768` | Sugerencia confirmada (AJAX) | `estado=DISPONIBLE`, `revisado=True` |
| Agregar en revisar_vehiculo | `views.py:1866` | Acción `agregar` (AJAX) | `estado=DISPONIBLE`, `revisado=True` |
| Pieza suelta | `views.py:984` | Form `crear_pieza_suelta` | Crea VehiculoDesarme placeholder |
| Generar inventario (bypass) | `services.py:55` | `get_or_create` desde catálogo | `estado=DISPONIBLE`, sin revisar |
| Seed demo | `seed_desarme_demo.py:94` | Management command | Solo desarrollo |

### 3.3 Puntos de decremento de stock

| Flujo | Archivo:línea | Operación | Actualiza estado_pieza |
|-------|---------------|-----------|------------------------|
| Venta rápida | `views_venta.py:169-174` | `pieza.cantidad -= cant; pieza.save()` | ✅ Sí — marca VENDIDA si ≤ 0 |
| Finalizar inventario | `views_inventario.py:533-534` | `.update(cantidad=F("cantidad")-cant)` | ❌ No — solo decrementa cantidad |
| Anular venta rápida | `views_venta.py:233-236` | Restaura cantidad + DISPONIBLE | ✅ Sí |

### 3.4 Filtro del kiosko

```python
# storefront.py:51-53 y :270-272
PiezaDesarme.objects.filter(
    empresa=empresa,
    estado_pieza=ESTADO_DISPONIBLE,   # filtro por estado semántico
    # cantidad NO se filtra aquí
)
```

**Consecuencia**: una pieza con `cantidad=0` y `estado_pieza=DISPONIBLE` (posible tras flujo de inventario) aparecería en el kiosko como disponible pero no podría venderse.

---

## 4. Problemas detectados

### 4.1 Templates huérfanos (sin URL ni include)

| Archivo | Evidencia | Diagnóstico |
|---------|-----------|-------------|
| `taller/desarme/dashboard_financiero.html` | Sin URL en `urls_desarme.py`. Sin `{% include %}` en ningún template. Extends `base.html` (no `base_egarage_panel.html`). | Template de una iteración anterior que no llegó a conectarse |
| `taller/desarme/partials/_inventario_sale_panel.html` | `grep -rn "_inventario_sale_panel"` sin resultados en templates ni en Python | Partial preparado pero nunca incluido |

### 4.2 Redundancia de flujo de venta

Existen **dos modelos de venta completamente paralelos**:

| Aspecto | Venta rápida | Venta desde inventario |
|---------|-------------|----------------------|
| Modelo principal | `VentaDesarme` + `LineaVentaDesarme` | `Documento` + `LineaRepuesto` |
| Modelo archivo | `models/venta_desarme.py` | `documentos/models.py` + `lineas_documento.py` |
| Template confirmación | `ventas/confirmar.html` | `confirmar_venta_desde_inventario.html` |
| Recibo | `ventas/recibo.html` | Vista de Documento del sistema |
| Actualiza estado_pieza | Sí | No (solo cantidad) |
| Anulación soportada | Sí (`anular_venta`) | No — no hay rollback |
| Integración contable | No (modelo propio) | Sí (Documento del sistema) |

Ambos flujos modifican el mismo `PiezaDesarme.cantidad` pero con lógica divergente.

### 4.3 Redundancia de vistas de inventario

Dos vistas sirven el mismo propósito (ver y operar el stock de un vehículo):

| Aspecto | `inventario_vehiculo.html` | `inventario_inteligente.html` |
|---------|--------------------------|-------------------------------|
| Tamaño | 994 líneas (monolítico) | 53 líneas (shell) + 596L partials |
| JS framework | Alpine.js propio | Alpine.js via partials |
| Venta inline | Sí (formulario propio en línea 640) | Sí (via partials) |
| Destino venta | `crear_venta_desde_inventario` (mismo) | `crear_venta_desde_inventario` (mismo) |
| Enlace desde | `ver_vehiculo.html`, `scanner_vehiculo.html` | `inventario_vehiculo.html`, `ver_vehiculo.html` |
| Estado | Mantenido | Nuevo (reemplaza al clásico) |

### 4.4 Dos vías de inicializar inventario con comportamiento diferente

| Vía | Intermediario | Crea en BD | Estado inicial | Editable antes de confirmar |
|-----|--------------|-----------|----------------|----------------------------|
| `crear_vehiculo` → `revisar_vehiculo` | `SugerenciaPiezaDesarme` | Solo al confirmar | PENDIENTE → confirmación manual | Sí |
| `generar_inventario_view` | Ninguno | Inmediatamente | DISPONIBLE directo | No (ya en stock) |

El bypass de `generar_inventario_view` crea piezas en stock sin revisión. El botón "Generar inventario" está visible en `inventario_vehiculo.html:714` y `scanner_vehiculo.html:550`.

### 4.5 Archivos BAK en el repositorio git

```
templates/taller/common/vehiculos/
├── vehiculo_form.html.BAK_CLIENTE_PLUS_20260512_124707  (61 KB)
├── vehiculo_form.html.BAK_FETCH_CREDENTIALS             (63 KB)
├── vehiculo_form.html.BAK_FINAL_CLEAN                   (65 KB)
├── vehiculo_form.html.BAK_FIX_CLIENTE_URL               (63 KB)
├── vehiculo_form.html.BAK_JS_EDIT_FIX                   (64 KB)
├── vehiculo_form.html.BAK_MODEL_SELECT2_FIX             (64 KB)
├── vehiculo_form.html.BAK_URL_DIRECTA_CLIENTE_CREAR     (63 KB)
└── vehiculo_form.html.bak_unificar_fondo                (44 KB)
```

8 archivos de backup manual trackeados en git (~500 KB total). No son incluidos por ninguna vista. El historial de git cubre el mismo propósito.

### 4.6 Confusión de nombres — dos vehiculo_form.html sin relación

| Template | Propósito | View que lo usa |
|----------|-----------|-----------------|
| `taller/desarme/vehiculo_form.html` | Alta/edición de **VehiculoDesarme** | `desarme:crear_vehiculo`, `desarme:editar_vehiculo` |
| `taller/common/vehiculos/vehiculo_form.html` | Alta/edición de **Vehiculo** (vehículo regular de taller) | `vehiculos:crear`, `vehiculos:editar` |

Mismo nombre de archivo, directorio diferente, propósito y modelo completamente distintos.

---

## 5. Recomendaciones de consolidación

> Solo recomendaciones — sin implementación.

### P0 — Corrección de bug (no cosmético)

**R1 — Sincronizar `estado_pieza` en finalizar_venta_desde_inventario**  
`views_inventario.py:533-534` decrementa `cantidad` sin evaluar si llega a 0. Añadir lógica equivalente a `views_venta.py:170-172` para marcar `ESTADO_VENDIDA` cuando `cantidad <= 0`. De lo contrario el kiosko muestra stock agotado como disponible.

**Evidencia:**
```python
# views_inventario.py:533 — solo decrementa, no marca VENDIDA
PiezaDesarme.objects.filter(pk=pieza.pk).update(cantidad=F("cantidad") - cantidad)

# views_venta.py:169-172 — correcto
pieza.cantidad -= item["cantidad"]
if pieza.cantidad <= 0:
    pieza.estado_pieza = ESTADO_VENDIDA
pieza.save(update_fields=["cantidad", "estado_pieza", "activo"])
```

**Alternativa más robusta**: añadir `cantidad > 0` al filtro del kiosko en `storefront.py:51` como doble protección.

---

### P1 — Eliminar huérfanos confirmados

**R2 — Eliminar `dashboard_financiero.html`**  
73 líneas sin URL, sin include, sin ruta de acceso. Extends `base.html` genérico (no el panel). Candidato claro a borrar.

**R3 — Eliminar `_inventario_sale_panel.html`**  
89 líneas de partial nunca incluido. Si fue preparado para una funcionalidad futura, debe vivir en una rama o issue, no en main.

---

### P2 — Limpiar archivos BAK del repo

**R4 — Borrar los 8 archivos `.BAK*` / `.bak*`**  
Git ya almacena todo el historial. Los backups manuales en el filesystem son ruido. Un `git log --follow templates/taller/common/vehiculos/vehiculo_form.html` recupera cualquier versión anterior.

---

### P3 — Unificar vistas de inventario

**R5 — Deprecar `inventario_vehiculo.html` (994L) a favor de `inventario_inteligente.html` + partials**  
El inventario inteligente es más moderno, tiene la misma funcionalidad y mejor UX. La vista clásica añade ~1000 líneas de deuda.  
Requisito previo: verificar que el flujo de venta inline de `inventario_vehiculo.html:640` esté cubierto por los partials del inteligente.

---

### P4 — Decidir sobre los dos flujos de venta

**R6 — Documentar la intención de VentaDesarme vs Documento**  
Los dos flujos no son equivalentes:
- `VentaDesarme` es liviano y para ventas informales (sin cliente registrado, sin integración contable).
- `Documento` integra el sistema de facturación, correlativos, PDF.

Si la intención es reemplazar el primero con el segundo, eliminar las tres vistas de `ventas/` (`confirmar.html`, `lista.html`, `recibo.html`) y el modelo `VentaDesarme`. Si coexisten intencionalmente, documentarlo explícitamente y asegurar que ambos flujos manejen `estado_pieza` de forma consistente.

---

### P5 — Aclarar el bypass de generar inventario

**R7 — Eliminar o subordinar `generar_inventario_view`**  
El flujo `crear_vehiculo → revisar_vehiculo` es el correcto: crea sugerencias, el operador confirma, solo entonces las piezas entran al stock. El bypass de `generar_inventario_view` salta ese paso y pone piezas en `DISPONIBLE` inmediatamente sin revisión.  
Opciones: eliminar el botón "Generar inventario" de los templates que lo exponen, o redirigir a `revisar_vehiculo` en lugar del scanner.

---

## 6. Resumen ejecutivo

| Categoría | Cantidad | Acción sugerida |
|-----------|----------|-----------------|
| Templates activos y correctamente conectados | 27 | Mantener |
| Templates huérfanos (sin URL ni include) | 2 | Eliminar (R2, R3) |
| Archivos BAK en repo | 8 | Eliminar (R4) |
| Vistas de inventario duplicadas | 2 | Consolidar en inteligente (R5) |
| Flujos de venta paralelos | 2 | Decidir uno canonical (R6) |
| Bug de estado_pieza en finalizar venta | 1 | Corregir (R1) |

**Total templates del módulo desarmaduria (incluyendo público):** 34 archivos activos, ~8.500 líneas.  
**Candidatos a eliminar sin riesgo:** 10 archivos (~1.050 líneas de templates + 500 KB de BAKs).
