# Auditoría: Soporte para desarmadurías en eGarage

**Objetivo:** Determinar qué partes del flujo de desarmaduría (vehículos fuente de repuestos) ya existen y qué falta para un flujo completo.

**Alcance:** Modelos, vistas, URLs, templates, navegación y lógica de negocio. **No se modificó código**; solo análisis técnico.

---

## 1) Qué partes del sistema de desarme YA existen

### 1.1 Modelos

| Elemento | Ubicación | Estado |
|----------|-----------|--------|
| **Vehiculo** | `taller/models/vehiculos.py` | ✅ Completo para desarme |
| **Repuesto** | `taller/models/repuesto.py` | ✅ Campos desarme presentes |
| **PlantillaDesarme** | `taller/models/plantilla_desarme.py` | ✅ |
| **PlantillaPieza** | `taller/models/plantilla_desarme.py` | ✅ |
| **CostoVehiculoDesarme** | `taller/models/costo_vehiculo_desarme.py` | ✅ |

**Campos en Vehiculo (desarmaduría):**

- `tipo_uso`: CharField, choices `("cliente", "desarme")`, default `"cliente"`.
- `estado_desarme`: CharField, choices `("ingresado", "en_desarme", "con_piezas", "agotado", "cerrado")`, blank/default `""`.
- `activo_operacional`: BooleanField, default True (False al cerrar).
- `fecha_ingreso_desarme`, `fecha_cierre_desarme`: DateField.
- `proveedor_nombre`, `proveedor_rut`, `proveedor_telefono`.
- `precio_compra`, `costo_transporte`, `costo_grua`, `costo_papeles`, `otros_costos_base`.
- `peso_final_kg`, `valor_final_por_kg`, `ingreso_final_chatarra`, `observaciones_desarme`.

**Métodos en Vehiculo:**

- `costo_total_base`, `costos_adicionales_total`, `costo_total_desarme`.
- `ingresos_repuestos_total`, `ingresos_totales`, `utilidad_total`, `porcentaje_recuperacion`.
- `cerrar_desarme(fecha_cierre, peso_kg, valor_por_kg)`.

**Relación Vehiculo ↔ Repuesto:**

- En **Repuesto**: `vehiculo_origen` (ForeignKey a Vehiculo, null/blank), `related_name="repuestos_desarme"`.
- En **Vehiculo**: acceso vía `vehiculo.repuestos_desarme`.

**Campos en Repuesto (desarme):**

- `tipo_origen`: choices incluyen `"desarme"`.
- `vehiculo_origen`: FK a Vehiculo (solo para tipo_origen=desarme).
- `origen_costo`: incluye `"desarme"`.
- `es_usado`, `controlar_stock`.
- `estado_pieza`: choices `("disponible", "dañado", "scrap", "vendido", "reservada")`.
- `zona_mapa`, `vista_mapa`: para mapa interactivo.

**Validaciones:**

- `Vehiculo.clean()`: si `tipo_uso == "desarme"` exige `fecha_ingreso_desarme`; si `tipo_uso != "desarme"` limpia `estado_desarme`.
- `Repuesto.clean()`: si `tipo_origen == "desarme"` exige `vehiculo_origen`.

---

### 1.2 Vistas

| Vista | Archivo | Función |
|-------|---------|--------|
| **demo_mapa_desarme** | `taller/views_desarme/mapa.py` | Demo del mapa (datos mock). |
| **vehiculo_mapa_desarme** | `taller/views_desarme/mapa.py` | Mapa interactivo de piezas por vehículo. |
| **pieza_por_zona** | `taller/views_desarme/mapa.py` | GET/POST AJAX: obtener/crear-actualizar pieza por zona. |
| **resumen_json** | `taller/views_desarme/mapa.py` | GET JSON: KPIs y resumen de piezas. |
| **dashboard_vehiculo_desarme** | `taller/views_desarme/dashboard_financiero.py` | Dashboard financiero (costos, ingresos, utilidad, piezas, ventas). |
| **cerrar_vehiculo_desarme** | `taller/views_desarme/cierre.py` | Formulario de cierre (fecha, peso, valor/kg). |
| **plantilla_list** | `taller/views_desarme/plantillas.py` | Listado de plantillas de desarme. |
| **plantilla_detail** | `taller/views_desarme/plantillas.py` | Detalle de plantilla. |
| **plantilla_create** | `taller/views_desarme/plantillas.py` | Crear plantilla. |
| **plantilla_edit** | `taller/views_desarme/plantillas.py` | Editar plantilla. |
| **plantilla_aplicar** | `taller/views_desarme/plantillas.py` | Aplicar plantilla a un vehículo de desarme (genera repuestos). |

Todas usan `_get_vehiculo_desarme(request, pk)` (empresa + `tipo_uso="desarme"`) y están protegidas con `@login_required`.

---

### 1.3 URLs

**Inclusión en taller:** `taller/urls.py`:

```python
path("desarme/", include(("taller.urls_desarme", "desarme"), namespace="desarme")),
```

**Rutas en `taller/urls_desarme.py` (app_name = "desarme"):**

| Ruta | name | Vista |
|------|------|--------|
| `desarme/demo/` | `demo` | demo_mapa_desarme |
| `desarme/vehiculos/<pk>/mapa/` | `mapa_piezas` | vehiculo_mapa_desarme |
| `desarme/vehiculos/<pk>/pieza-por-zona/` | `pieza_por_zona` | pieza_por_zona |
| `desarme/vehiculos/<pk>/resumen-json/` | `resumen_json` | resumen_json |
| `desarme/vehiculos/<pk>/dashboard/` | `dashboard_financiero` | dashboard_vehiculo_desarme |
| `desarme/vehiculos/<pk>/cerrar/` | `cerrar_vehiculo` | cerrar_vehiculo_desarme |
| `desarme/vehiculos/<pk>/aplicar-plantilla/` | `aplicar_plantilla` | plantilla_aplicar |
| `desarme/plantillas/` | `plantilla_list` | plantilla_list |
| `desarme/plantillas/nueva/` | `plantilla_create` | plantilla_create |
| `desarme/plantillas/<pk>/` | `plantilla_detail` | plantilla_detail |
| `desarme/plantillas/<pk>/editar/` | `plantilla_edit` | plantilla_edit |

**Nota:** La URL real depende del prefijo país/idioma (ej. `/cl/es/desarme/`, `/us/en/desarme/`). No existe ruta `/vehiculos/desarme/` ni `/repuestos/desarme/` como tal; el módulo es `.../desarme/...`.

---

### 1.4 Lógica de negocio (servicios)

| Servicio | Archivo | Responsabilidad |
|----------|---------|------------------|
| **plantilla_desarme_service** | `taller/services/plantilla_desarme_service.py` | `aplicar_plantilla(vehiculo, plantilla)` → crea Repuestos con `tipo_origen=desarme`, `vehiculo_origen=vehiculo`; validaciones (no duplicar, vehículo tipo desarme, no cerrado, plantilla activa). |
| **desarme_piece_service** | `taller/services/desarme_piece_service.py` | `get_piece_by_zone`, `create_or_update_piece`: crear/actualizar pieza por zona/vista en el mapa. |
| **desarme_kpis** | `taller/services/desarme_kpis.py` | `build_vehicle_desarme_kpis`, `get_kpis`, `get_piece_summary`, mapeo estado backend↔frontend. |

---

### 1.5 Templates existentes

**Desarme:**

- `templates/taller/desarme/mapa_piezas.html` — Mapa interactivo del vehículo.
- `templates/taller/desarme/demo_mapa.html` — Demo del mapa.
- `templates/taller/desarme/dashboard_financiero.html` — Dashboard financiero.
- `templates/taller/desarme/cierre_vehiculo_form.html` — Formulario de cierre.
- `templates/taller/desarme/plantillas/plantilla_list.html`
- `templates/taller/desarme/plantillas/plantilla_detail.html`
- `templates/taller/desarme/plantillas/plantilla_form.html` (crear/editar)
- `templates/taller/desarme/plantillas/plantilla_aplicar.html`
- `templates/taller/desarme/partials/_header_desarme.html`
- `templates/taller/desarme/partials/_header_kpis.html`
- `templates/taller/desarme/partials/_footer_desarme.html`
- `templates/taller/desarme/partials/_footer_resumen.html`
- `templates/taller/desarme/partials/_piece_drawer.html`
- `templates/taller/desarme/partials/_piece_drawer_desarme.html`
- `templates/taller/desarme/svg/_vehicle_front.html`, `_vehicle_left.html`
- `templates/taller/desarme/_svg_sedan_frontal.html`, `_svg_sedan_lateral.html`

**Vehículos:**

- `templates/taller/common/vehiculos/_table.html`: muestra botón "Desarme" (mapa) solo si `vehiculo.tipo_uso == 'desarme'` y existe `desarme_map_url_name`.
- `templates/taller/common/vehiculos/vehiculo_form.html`: incluye campo `tipo_uso` y texto que indica usar "Vehículo para desarme" para el módulo de desarmaduría.

---

### 1.6 Formularios

- **CierreVehiculoDesarmeForm** (`taller/forms/cierre_vehiculo_desarme.py`): fecha_cierre, peso_final_kg, valor_final_por_kg, observaciones.
- **PlantillaDesarmeForm**, **PlantillaPiezaForm** (`taller/forms/plantilla_desarme.py`).
- **PlantillaAplicarForm** (`taller/forms/plantilla_aplicar.py`): selección de plantilla para aplicar a un vehículo.

---

### 1.7 Integración lista de vehículos

- `taller/vehiculos/views_fbv.py` (lista_vehiculos): calcula `desarme_map_url_name` según namespace (país) y lo pasa al template.
- Template `taller/common/vehiculos/_table.html`: en cada tarjeta de vehículo con `tipo_uso == 'desarme'` muestra enlace al mapa de piezas (Desarme).

---

### 1.8 Admin Django

- `PlantillaDesarme`, `PlantillaPieza` registrados en `taller/admin.py` (PlantillaPiezaInline en PlantillaDesarme).

---

### 1.9 Comando de gestión

- `taller/management/commands/seed_plantillas_desarme.py`: crea plantillas globales (Sedan, SUV, Pickup, etc.).

---

### 1.10 Estáticos

- `static/js/desarme/vehicle-map.js`, `piece-drawer.js`, `desarme-summary.js`
- `static/taller/desarme/vehicle-map.css`
- `static/taller/desarme/svg/sedan_lateral.svg`

---

## 2) Qué partes están incompletas

### 2.1 Formulario de vehículo (crear/editar)

- **VehiculoForm** (`taller/vehiculos/forms.py`) incluye `tipo_uso` en `Meta.fields`, pero **no incluye** campos específicos de desarme:
  - `fecha_ingreso_desarme` (obligatorio en `Vehiculo.clean()` cuando `tipo_uso == "desarme"`).
  - `precio_compra`, `costo_transporte`, `costo_grua`, `costo_papeles`, `otros_costos_base`.
  - `proveedor_nombre`, `proveedor_rut`, `proveedor_telefono`.
  - `estado_desarme` (opcional en formulario; el modelo puede inicializarlo).
- **Consecuencia:** Si el usuario crea un vehículo con tipo "desarme" y guarda, la validación del modelo puede fallar por falta de `fecha_ingreso_desarme`, o el vehículo queda sin costos iniciales y sin estado. No hay pantalla dedicada "ingreso vehículo para desarme" con todos estos campos.

### 2.2 Lista de repuestos y filtro por vehículo origen

- En **dashboard** y **plantilla_aplicar** se redirige a repuestos con `?vehiculo_origen=<pk>` (ej. `lista_repuestos` + query string).
- **RepuestoListView** (`taller/repuestos/views_cbv.py`) en `get_queryset()` **no** filtra por `vehiculo_origen`: solo filtra por `q` (búsqueda por nombre/part_number/categoría). El parámetro `vehiculo_origen` en la URL no tiene efecto en el queryset.
- **Consecuencia:** El enlace "Piezas" / "Ver piezas" abre la lista general de repuestos de la empresa, no solo las del vehículo seleccionado.

### 2.3 Navegación al módulo desarme

- En `templates/taller/common/base.html` hay enlaces a: Ajustes, Centro, Clientes, Documentos, Extra, Repuestos, Reportes, Servicios, Vehículos, Crear vehículo, etc.
- **No hay** enlace directo a:
  - Listado de plantillas de desarme (`desarme:plantilla_list`).
  - Listado de vehículos de desarme (no existe vista específica; solo lista general de vehículos).
  - Demo del mapa (`desarme:demo`).
- El acceso a desarme es **solo** desde la lista de vehículos, haciendo clic en "Desarme" en un vehículo con `tipo_uso == 'desarme'`. Quien no tenga vehículos de desarme o no sepa que debe crearlos desde "Crear vehículo" con tipo desarme, no tiene un menú claro para el módulo.

### 2.4 Listado de “vehículos de desarme”

- No existe una vista/URL que muestre **solo** vehículos con `tipo_uso='desarme'` (por ejemplo `/desarme/vehiculos/` o filtro en lista general).
- La lista actual es única: todos los vehículos (cliente + desarme). El usuario debe distinguir por tipo_uso o por el botón "Desarme" en la tarjeta.

### 2.5 Alta de costos adicionales (CostoVehiculoDesarme)

- El modelo `CostoVehiculoDesarme` existe y se usa en el dashboard (listado de costos adicionales).
- No se encontró vista ni formulario público para **crear/editar/eliminar** costos adicionales desde el panel; solo se listan en `dashboard_financiero`. La gestión podría estar solo en admin o faltar en el flujo usuario.

### 2.6 Template de lista de repuestos

- No se comprobó que el template de lista de repuestos muestre columna o filtro "Vehículo origen" cuando `vehiculo_origen` está presente; incluso si se implementara el filtro en la vista, el template podría necesitar ajustes para mostrar el vehículo de origen en cada fila.

---

## 3) Qué falta para un flujo completo de desarmaduría

Resumen por etapa:

| Etapa | Estado | Qué falta |
|-------|--------|-----------|
| **1. Ingreso vehículo** | Parcial | Formulario de creación/edición con tipo_uso=desarme debe incluir al menos `fecha_ingreso_desarme` (obligatorio) y, recomendable, costos base y proveedor. Opcional: vista/pantalla específica "Ingresar vehículo para desarme" que reutilice o extienda el form. |
| **2. Inspección de piezas** | Implementado | Mapa interactivo por vehículo, drawer de pieza por zona, estados, precios. Falta solo asegurar que desde lista de vehículos se llegue bien (ya existe el botón Desarme). |
| **3. Generación de repuestos** | Implementado | Aplicar plantilla genera repuestos; creación/edición por zona en el mapa. Completo. |
| **4. Cierre de vehículo** | Implementado | Vista y formulario de cierre (fecha, peso, valor/kg), método `cerrar_desarme`, dashboard con datos de cierre. Completo. |

**Resumen de gaps:**

1. **Ingreso:** Incluir en el formulario de vehículo (o en un formulario específico desarme) los campos de desarme necesarios, como mínimo `fecha_ingreso_desarme`.
2. **Lista repuestos:** En `RepuestoListView.get_queryset()`, si existe `request.GET.get("vehiculo_origen")`, filtrar por `vehiculo_origen_id` (y por empresa para seguridad).
3. **Navegación:** Añadir en el menú principal (base.html) al menos un enlace al módulo desarme (por ejemplo "Desarme" o "Plantillas desarme" que lleve a `desarme:plantilla_list` o a una futura lista de vehículos de desarme).
4. **Opcional:** Vista que liste solo vehículos de desarme (o filtro tipo_uso en la lista actual) y, si se desea, CRUD de costos adicionales desde el panel (no solo listado en dashboard).

---

## 4) Lista de archivos donde aparece la lógica de desarme

### Modelos y migraciones

- `taller/models/vehiculos.py` — Vehiculo (tipo_uso, estado_desarme, activo_operacional, campos desarme, métodos, cerrar_desarme).
- `taller/models/repuesto.py` — Repuesto (tipo_origen, vehiculo_origen, estado_pieza, zona_mapa, vista_mapa, validación).
- `taller/models/plantilla_desarme.py` — PlantillaDesarme, PlantillaPieza.
- `taller/models/costo_vehiculo_desarme.py` — CostoVehiculoDesarme.
- `taller/models/__init__.py` — Exports.
- `taller/migrations/0083_repuesto_tipo_origen_vehiculo_origen_origen_costo.py`
- `taller/migrations/0084_vehiculo_desarme_costo_repuesto.py`
- `taller/migrations/0085_plantilla_desarme_estado_pieza.py`
- `taller/migrations/0086_repuesto_zona_mapa_vista.py`
- `taller/migrations/0087_plantilla_pieza_lado_zona.py`, `0087_merge_*`, `0088_*`, `0089_*`, etc. (relacionados).

### Vistas y URLs

- `taller/urls.py` — Include de urls_desarme.
- `taller/urls_desarme.py` — Rutas del módulo desarme.
- `taller/views_desarme/__init__.py` — Exports mapa.
- `taller/views_desarme/mapa.py` — demo_mapa_desarme, vehiculo_mapa_desarme, pieza_por_zona, resumen_json.
- `taller/views_desarme/dashboard_financiero.py` — dashboard_vehiculo_desarme.
- `taller/views_desarme/cierre.py` — cerrar_vehiculo_desarme.
- `taller/views_desarme/plantillas.py` — plantilla_list, detail, create, edit, aplicar.

### Servicios

- `taller/services/plantilla_desarme_service.py` — aplicar_plantilla, plantillas_disponibles_para.
- `taller/services/desarme_piece_service.py` — get_piece_by_zone, create_or_update_piece, _piece_to_frontend.
- `taller/services/desarme_kpis.py` — build_vehicle_desarme_kpis, get_kpis, get_piece_summary, STATUS_*.

### Formularios

- `taller/forms/cierre_vehiculo_desarme.py` — CierreVehiculoDesarmeForm.
- `taller/forms/plantilla_desarme.py` — PlantillaDesarmeForm, PlantillaPiezaForm.
- `taller/forms/plantilla_aplicar.py` — Form aplicar plantilla (PlantillaAplicarForm / lógica).

### Vehículos (integración)

- `taller/vehiculos/views_fbv.py` — lista_vehiculos (desarme_map_url_name), crear_vehiculo.
- `taller/vehiculos/forms.py` — VehiculoForm (tipo_uso en fields; cliente opcional si desarme; **sin** campos desarme en Meta.fields).

### Repuestos

- `taller/repuestos/views_cbv.py` — RepuestoListView (get_queryset **sin** filtro vehiculo_origen).

### Admin y comandos

- `taller/admin.py` — PlantillaPiezaInline, PlantillaDesarmeAdmin, PlantillaPiezaAdmin.
- `taller/management/commands/seed_plantillas_desarme.py` — Seed plantillas globales.

### Templates

- `templates/taller/desarme/mapa_piezas.html`
- `templates/taller/desarme/demo_mapa.html`
- `templates/taller/desarme/dashboard_financiero.html`
- `templates/taller/desarme/cierre_vehiculo_form.html`
- `templates/taller/desarme/plantillas/plantilla_list.html`
- `templates/taller/desarme/plantillas/plantilla_detail.html`
- `templates/taller/desarme/plantillas/plantilla_form.html`
- `templates/taller/desarme/plantillas/plantilla_aplicar.html`
- `templates/taller/desarme/partials/_header_desarme.html`
- `templates/taller/desarme/partials/_header_kpis.html`
- `templates/taller/desarme/partials/_footer_desarme.html`
- `templates/taller/desarme/partials/_footer_resumen.html`
- `templates/taller/desarme/partials/_piece_drawer.html`
- `templates/taller/desarme/partials/_piece_drawer_desarme.html`
- `templates/taller/desarme/svg/_vehicle_front.html`, `_vehicle_left.html`
- `templates/taller/desarme/_svg_sedan_frontal.html`, `_svg_sedan_lateral.html`
- `templates/taller/common/vehiculos/_table.html` — Botón Desarme por vehículo.
- `templates/taller/common/vehiculos/vehiculo_form.html` — Campo tipo_uso y texto desarmaduría.
- `templates/taller/common/base.html` — Navegación (sin enlace desarme).

### Estáticos

- `static/js/desarme/vehicle-map.js`
- `static/js/desarme/piece-drawer.js`
- `static/js/desarme/desarme-summary.js`
- `static/taller/desarme/vehicle-map.css`
- `static/taller/desarme/svg/sedan_lateral.svg`

---

**Conclusión:** La base del flujo de desarmaduría está implementada (modelos, mapa de piezas, plantillas, aplicación de plantilla, dashboard, cierre). Los principales huecos son: (1) formulario de vehículo sin campos de desarme (sobre todo `fecha_ingreso_desarme`), (2) lista de repuestos sin filtro por `vehiculo_origen`, y (3) ausencia de enlace al módulo desarme en la navegación principal.
