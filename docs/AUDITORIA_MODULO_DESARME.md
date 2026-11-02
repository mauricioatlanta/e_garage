# Auditoría del módulo Desarme – eGarage

**Fecha:** 2025-03-11  
**Objetivo:** Documentar el estado actual del módulo de desarmaduría antes de crear funcionalidad nueva.

---

## 1. Modelos existentes

### 1.1 Vehiculo

| Aspecto | Detalle |
|--------|---------|
| **Archivo** | `taller/models/vehiculos.py` |
| **Campos relevantes** | `cliente`, `marca`, `modelo`, `patente`, `anio`, `vin`, `motor`, `caja`, `millas`, `marca_texto`, `modelo_texto` |
| **Relaciones** | `Cliente`, `Marca`, `Modelo`, `ColorVehiculo`, `MotorVehiculo`, `CajaVehiculo` |
| **Flujo desarme** | **No.** No existe `vehiculo_origen`, `tipo_origen`, `estado_desarme`, `activo_operacional` ni ningún campo que identifique un vehículo como “para desarme” o “desarmado”. |

### 1.2 Repuesto (taller.models.repuesto)

| Aspecto | Detalle |
|--------|---------|
| **Archivo** | `taller/models/repuesto.py` |
| **Campos** | `part_number`, `nombre`, `categoria`, `precio_compra`, `precio_venta`, `cantidad_stock`, `proveedor` |
| **Relaciones** | `CategoriaRepuesto` (FK), `TenantScoped` → `empresa` |
| **Flujo desarme** | **No.** No tiene `vehiculo_origen`, `tipo_origen`, `estado_pieza`, `estado_desarme`, `tipo_uso` ni `activo_operacional`. Es un repuesto genérico (compra/venta/stock). |

### 1.3 Part (catálogo I18N)

| Aspecto | Detalle |
|--------|---------|
| **Archivo** | `taller/models/catalogo_repuestos.py` |
| **Campos** | `empresa`, `sku`, `category`, `brand`, `unit`, `weight_kg`, `purchase_price`, `stock_quantity`, `stock_min`, `active` |
| **Relaciones** | `Empresa`, `PartI18N`, `PartPrice` |
| **Flujo desarme** | **No.** Catálogo de repuestos con precios y stock; sin relación con vehículo origen ni estados de desarme. |

### 1.4 PlantillaPieza

| Estado | Detalle |
|--------|---------|
| **Existencia** | **No existe** en el proyecto. No hay modelo `PlantillaPieza` ni `plantillapieza` en el código. |

### 1.5 LineaRepuesto (líneas de documento)

| Aspecto | Detalle |
|--------|---------|
| **Archivo** | `taller/models/lineas_documento.py` |
| **Campos** | `documento`, `repuesto`, `part`, `codigo`, `nombre`, `cantidad`, `precio_unitario`, `descuento`, `observaciones`, `tecnico_responsable` |
| **Relaciones** | `Documento`, `Repuesto` (legacy), `Part` (catálogo I18N), `Tecnico` |
| **Flujo desarme** | **No.** Línea de documento genérica; no hay FK a “vehículo origen” ni campos de estado de pieza/desarme. |

### 1.6 RepuestoDocumento

| Aspecto | Detalle |
|--------|---------|
| **Archivo** | `taller/models/repuesto_documento.py` |
| **Contenido** | Modelo casi vacío (solo `Meta` con índices `documento`, `mecanico`, `documento+mecanico`). No define campos explícitos en el fragmento revisado. |
| **Uso** | En el código se usa `LineaRepuesto` para “repuesto en documento”; `RepuestoDocumento` parece legacy o no usado para el flujo actual. |

### Resumen modelos y desarme

- **Implementado:** `Vehiculo`, `Repuesto`, `Part`, `LineaRepuesto` como modelos genéricos de taller/repuestos/documentos.
- **No implementado para desarme:**  
  - Campos: `vehiculo_origen`, `tipo_origen`, `estado_pieza`, `estado_desarme`, `tipo_uso`, `activo_operacional`.  
  - Modelo: `PlantillaPieza`.  
  - Ningún modelo distingue “pieza de desarme” ni “vehículo en desarme”.

---

## 2. Vistas existentes

### 2.1 Vistas con “desarme” en el código

- **No existe** ninguna vista que reciba o maneje rutas bajo el namespace `desarme`.  
- Las únicas referencias a “desarme/desarmaduría” están en:
  - `taller/urls.py` (include de `urls_desarme`),
  - `taller/urls_desarme.py` (comentarios),
  - Textos de ayuda/landing (ej. “talleres y desarmadurías”).

### 2.2 Vistas relacionadas (repuestos, vehículos, reportes, inventario)

| Archivo | Vista / Función | Tipo | Qué hace | Template | ¿Flujo desarme? |
|---------|-----------------|------|----------|----------|------------------|
| `taller/repuestos/views.py` | `lista_repuestos`, `crear_repuesto`, `editar_repuesto`, `ver_repuesto`, `eliminar_repuesto`, `buscar_repuestos_ajax` | FBV | CRUD repuestos (Repuesto) | repuesto_list, repuesto_form, etc. | No |
| `taller/vehiculos/views_fbv` | `lista_vehiculos`, `crear_vehiculo`, `ver_vehiculo`, `editar_vehiculo`, `eliminar_vehiculo` + APIs/AJAX | FBV | CRUD vehículos | vehiculo_list, vehiculo_form, etc. | No |
| `taller/reportes/views.py` | `reportes_dashboard`, `reporte_repuestos`, `reporte_servicios`, `centro_contable_chile`, `dashboard_inteligencia_operativa`, `reportes_mecanicos`, `reportes_por_fecha`, `diagnostico_ia`, `historial_mantenimiento_vehiculo`, etc. | FBV | Dashboards y reportes (repuestos, servicios, vehículos, kilometraje) | reportes.html, reporte_repuestos, etc. | No |
| `taller/reportes/reportes_avanzados.py` | `reportes_rentabilidad`, `dashboard_rentabilidad`, `reporte_comparativo_precios`, `reporte_servicios_subcontratados` | FBV | Rentabilidad por servicios (interno/externo), no por vehículo desarmado | rentabilidad.html, dashboard_rentabilidad.html | No |
| `taller/documentos/views*.py` | Creación/edición de documentos y líneas (servicio, repuesto, otro servicio) | FBV/CBV | Documentos con `LineaRepuesto` (repuesto genérico) | document_form, etc. | No |

Conclusión: no hay vistas específicas de “desarme” (vehículos en desarme, inventario de piezas de desarme, reportes de desarme). Las vistas de repuestos/vehículos/reportes son de taller genérico.

---

## 3. URLs existentes

### 3.1 Namespace `desarme`

| Archivo | Path completo (incluido) | Nombre ruta | Namespace |
|---------|--------------------------|-------------|-----------|
| `taller/urls.py` | `desarme/` | (include) | `taller:desarme` |
| `taller/urls_desarme.py` | (vacío) | — | `app_name = "desarme"` |

- **Contenido de `urls_desarme.py`:** solo `app_name = "desarme"` y `urlpatterns = []`. No hay rutas definidas.
- **Efecto:** La URL `/desarme/` existe a nivel de include (según la configuración de país/idioma), pero al no haber ninguna `path()` dentro del include, **no hay ninguna vista asociada**. Acceder a `/desarme/` puede devolver 404 o comportamiento por defecto según la configuración global.

### 3.2 Rutas relacionadas (repuestos, vehículos, reportes)

Estas están bajo otros namespaces (no `desarme`):

| Módulo | Ejemplo de path (según país) | Namespace |
|--------|------------------------------|-----------|
| Repuestos | `.../repuestos/`, `.../repuestos/crear/`, `.../repuestos/<pk>/` | `taller:repuestos:*` |
| Vehículos | `.../vehiculos/`, `.../vehiculos/crear/`, `.../vehiculos/<id>/` | `taller:vehiculos:*` |
| Reportes | `.../reportes/`, `.../reportes/repuestos/`, `.../reportes/dashboard-rentabilidad/` | `taller:reportes:*` |
| Documentos | `.../documentos/` | `taller:documentos:*` |

La aplicación principal está montada bajo prefijos tipo `/cl/es/` o `/us/en/` (según `gestion_taller/urls.py` y país/idioma). Ejemplos de URLs que sí puedes probar:

- Repuestos: `/{country}/{lang}/repuestos/` (ej. `/cl/es/repuestos/`)
- Vehículos: `/{country}/{lang}/vehiculos/`
- Reportes: `/{country}/{lang}/reportes/`
- Reportes repuestos: `/{country}/{lang}/reportes/repuestos/`
- Dashboard rentabilidad: `/{country}/{lang}/reportes/dashboard-rentabilidad/`

**Desarme:**

- No hay rutas bajo `desarme` (lista vacía). No hay URLs de desarme para probar (ej. `/desarme/vehiculos/`, `/desarme/inventario/`, `/desarme/reportes/`).

---

## 4. Templates existentes

### 4.1 Templates con “desarme” en la ruta

- **No existe** ningún template bajo una ruta tipo `templates/.../desarme/...`.
- Búsqueda de `**/desarme/**/*.html`: **0 archivos.**

### 4.2 Templates relacionados (repuestos, vehículos, reportes)

| Ruta aproximada | Uso |
|-----------------|-----|
| `taller/common/repuestos/repuesto_list.html`, `repuesto_form.html`, `tabla_repuestos.html` | Listado y formularios de repuestos |
| `taller/common/vehiculos/*.html` | Listado, detalle, formulario, confirmación eliminación |
| `taller/reportes/reportes.html` | Centro de reportes (enlaces a repuestos, rentabilidad, mecánicos, etc.) |
| `taller/reportes/reporte_repuestos`, `rentabilidad.html`, `dashboard_rentabilidad.html`, etc. | Reportes de repuestos y rentabilidad (servicios) |

Ninguno de estos templates es “de desarme”; son de taller/repuestos/reportes genéricos.

---

## 5. Integración con documentos

### 5.1 Repuesto ↔ LineaRepuesto ↔ Documento

- **LineaRepuesto** tiene:
  - `documento` (FK a `Documento`)
  - `repuesto` (FK opcional a `Repuesto` legacy)
  - `part` (FK opcional a `Part` catálogo I18N)
  - `codigo`, `nombre`, `cantidad`, `precio_unitario`, `descuento`, etc.
- **Sí:** las piezas (repuestos del catálogo) se usan como líneas de documento vía `LineaRepuesto`.
- **No:** no hay relación “repuesto → vehículo origen”. No existe FK en `Repuesto` ni en `LineaRepuesto` a un “vehículo de desarme”.

### 5.2 Lógica de descuento de stock

- **Sí existe** y está implementada:
  - `taller/reportes/services/inventory_service.py` (y copia en `taller/services/inventory_service.py`): `InventoryService.procesar_movimiento_stock(documento, 'descontar'|'reponer'|'ajustar')`, validación de stock, procesamiento en edición.
  - Solo considera líneas con `repuesto` (FK a `Repuesto`) no nulo; actualiza `Repuesto.cantidad_stock`.
- **Señales:** `taller/documentos/signals_inventory.py`: al cambiar estado del documento (BORRADOR→EMITIDO, EMITIDO→ANULADO, etc.) se llama a `InventoryService` para descontar/reponer stock.
- **Conclusión:** El descuento de stock por documento está implementado para **repuestos genéricos** (`Repuesto`), no para “piezas de desarme” ni vehículo origen.

---

## 6. Dashboards y reportes existentes

### 6.1 Qué hay implementado

- **Centro de reportes** (`reportes_dashboard`): `taller/reportes/reportes.html` con enlaces a:
  - Centro contable Chile
  - Inteligencia operativa
  - Reportes por técnico
  - Recordatorios mantenimiento
  - Dashboard repuestos (inventario, top ventas, márgenes, stock crítico)
  - Dashboard rentabilidad (servicios internos vs subcontratados)
  - Análisis rentabilidad, comparativo precios, servicios subcontratados
  - Reportes básicos (servicios, vehículos atendidos, clientes, facturación)
- **Rentabilidad:** por tipo de servicio (LineaServicio, LineaOtroServicio), no por “vehículo desarmado” ni “piezas de desarme”.
- **Reporte repuestos:** top ventas, márgenes, ingresos por repuesto (`LineaRepuesto`), stock bajo.
- **Kilometraje:** recordatorios e historial por vehículo (mantenimiento), no por desarme.

### 6.2 Qué no existe

- Rentabilidad por vehículo (desarmado).
- Reporte “piezas vendidas de desarme” o “ingresos por desarme”.
- KPIs específicos de desarmaduría (vehículos en desarme, piezas extraídas, etc.).

---

## 7. Navegación

### 7.1 Navbar / menús revisados

- **templates/taller/common/base.html** y **templates/base.html**: enlaces a:
  - Centro (workspace)
  - Clientes
  - Documentos
  - Extra (otros servicios)
  - Repuestos
  - Reportes
  - Servicios
  - Vehículos
  - (y según rol: Equipo, Configuración)
- **No hay** enlace a “Desarme” ni a “Desarmaduría” en ninguno de los dos.

### 7.2 Dashboard principal

- **templates/taller/dashboard/dashboard.html**: enlaces a Clientes, Vehículos, Servicios, Repuestos, Documentos, Reportes.
- **No hay** tarjeta ni enlace a Desarme.

Conclusión: el módulo desarme **no está conectado a la navegación**. La única “conexión” es el include de `urls_desarme` bajo `desarme/`, sin rutas ni vistas.

---

## 8. Resultado estructurado

### 8.1 Lo que ya está implementado (sin ser desarme)

- CRUD de **Vehículos** y **Repuestos** (modelos genéricos).
- **Documentos** con **LineaRepuesto** (repuestos en presupuestos/OT/facturas).
- **InventoryService**: descuento/reposición de stock por documento (solo con `Repuesto`).
- **Reportes**: dashboard repuestos, rentabilidad por servicios, reportes por técnico, kilometraje, centro contable.
- **Navegación** a Repuestos, Vehículos, Reportes, Documentos (sin Desarme).

### 8.2 Lo que está parcialmente implementado

- **Namespace `desarme`:** existe el include y `app_name`, pero **urlpatterns vacío** → no hay rutas ni vistas.
- **Repuesto/Part:** sirven para cualquier repuesto; no hay distinción “pieza de desarme” ni vínculo a vehículo origen.

### 8.3 Lo que existe pero no está conectado a desarme

- Nada específico de desarme está implementado; por tanto no hay “vistas ocultas” de desarme. Lo que hay (vehículos, repuestos, reportes) está conectado a la navegación como taller genérico.

### 8.4 Lo que falta implementar para el módulo desarme

1. **Modelos:**
   - Extender **Repuesto** (o crear modelo “Pieza”) con: `vehiculo_origen` (FK a Vehiculo o a “VehículoDesarme”), `tipo_origen`, `estado_pieza`, `estado_desarme`, `tipo_uso`, `activo_operacional` (o equivalente).
   - Opcional: modelo **PlantillaPieza** si se desea catálogo de piezas por tipo de vehículo.
   - Decidir si los vehículos en desarme son los mismos `Vehiculo` con un estado/tipo o un modelo separado (ej. `VehiculoDesarme`).
2. **Vistas y URLs:**
   - Vistas bajo `taller/urls_desarme.py`: ej. listado de vehículos (desarme), inventario de piezas, reportes/KPIs de desarme.
   - Rutas como `/desarme/`, `/desarme/vehiculos/`, `/desarme/inventario/`, `/desarme/reportes/` (o equivalentes con prefijo país/idioma).
3. **Templates:**
   - Crear `templates/.../desarme/` y vistas que los usen.
4. **Documentos:**
   - Si las piezas de desarme deben poder usarse en documentos: que `LineaRepuesto` (o una línea específica) pueda referenciar “pieza de desarme” y que el descuento de stock use el inventario de desarme si aplica.
5. **Navegación:**
   - Añadir enlace “Desarme” o “Desarmaduría” en base/sidebar/dashboard que apunte a la nueva ruta principal de desarme.

### 8.5 URLs que puedes probar ahora (sin desarme)

Asumiendo base `/{country}/{lang}/` (ej. `cl`, `es` o `us`, `en`):

| URL relativa | Descripción |
|--------------|-------------|
| `/cl/es/repuestos/` | Lista de repuestos |
| `/cl/es/vehiculos/` | Lista de vehículos |
| `/cl/es/reportes/` | Centro de reportes |
| `/cl/es/reportes/repuestos/` | Dashboard de repuestos |
| `/cl/es/reportes/dashboard-rentabilidad/` | Dashboard rentabilidad (servicios) |
| `/cl/es/reportes/rentabilidad/` | Análisis rentabilidad |
| `/cl/es/documentos/` | Listado documentos |

**Desarme:** no hay URL útil; `/cl/es/desarme/` (o equivalente) no tiene vista asignada.

---

## 9. Resumen ejecutivo

- El **módulo desarme no está implementado**: no hay modelos con `vehiculo_origen`, `estado_desarme`, etc., no hay `PlantillaPieza`, no hay vistas ni templates bajo desarme, y la navegación no incluye Desarme.
- Lo que **sí está listo** es la base de taller: vehículos, repuestos, documentos con líneas de repuesto y descuento de stock para `Repuesto`.
- La **integración documento ↔ repuesto** existe para repuestos genéricos; para “piezas de desarme” haría falta extender modelos y, si aplica, la lógica de inventario.
- **Antes de crear código nuevo**, conviene: (1) definir si “piezas de desarme” son un tipo de `Repuesto` o un modelo aparte, (2) definir si el vehículo en desarme es `Vehiculo` con tipo/estado o un modelo nuevo, (3) reutilizar `LineaRepuesto` y `InventoryService` donde sea posible y extender solo lo necesario para desarme.
