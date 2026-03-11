# Reglas: documento y repuestos (eGarage)

## Vehículo de desarme (tipo_uso)

`Vehiculo` soporta dos mundos mediante `tipo_uso`:

- **cliente**: vehículo de cliente (requiere `cliente`, aparece en documentos)
- **desarme**: vehículo para desarme (sin cliente, acumula costos, genera repuestos)

Campos clave para desarme: `estado_desarme`, `fecha_ingreso_desarme`, costos base, `CostoVehiculoDesarme` (costos adicionales). Métricas: `costo_total_desarme`, `ingresos_repuestos_total`, `utilidad_total`, `porcentaje_recuperacion`. Método `cerrar_desarme()` para cierre lógico sin borrar.

---

## Tipos de origen del repuesto (catálogo)

El modelo `Repuesto` distingue tres naturalezas mediante `tipo_origen`:

| tipo_origen | Descripción | Stock | Al vender |
|-------------|-------------|--------|-----------|
| **stock**   | Comprado para inventario (filtros, pastillas, etc.) | Sí, se controla | Se descuenta `cantidad_stock` |
| **direct**  | Compra directa para vender sin almacenar | No | No se toca inventario |
| **desarme** | Pieza de vehículo desarmado | Típicamente 1 | Se descuenta (stock → 0) |

- **origen_costo** (opcional): `compra` \| `desarme` \| `consignacion` — para reportes y rentabilidad.
- **vehiculo_origen** (solo desarme): FK al vehículo del que proviene la pieza.

El servicio de inventario (`InventoryService`) solo mueve stock en líneas cuyo repuesto tiene `tipo_origen` en `("stock", "desarme")`. Los repuestos `direct` no participan en validación ni descuento de stock.

---

## Reglas de ingreso de repuestos en el documento (bloque 4)

- **4.1** Cada línea de repuesto guarda: repuesto origen, nombre en documento, cantidad, precio unitario, descuento, subtotal.
- **4.2** Búsqueda prioriza part number y nombre.
- **4.3** Al seleccionar repuesto se autocompleta nombre y precio sugerido.
- **4.4** Cantidad y precio recalculan subtotal en vivo.
- **4.5** El subtotal oficial se recalcula en backend.
- **4.6** Si se crea un repuesto nuevo desde el flujo, debe volver al documento y autoinsertarse.

---

## Relación con LineaRepuesto.source_type

En la **línea del documento** (`LineaRepuesto`) existe `source_type`:

- **IN_STOCK**: repuesto de nuestro inventario.
- **CUSTOMER_SUPPLIED**: lo trae el cliente (precio 0).
- **SOURCED**: conseguido afuera.

`Repuesto.tipo_origen` es una propiedad del **catálogo** (qué tipo de parte es).  
`LineaRepuesto.source_type` es el **origen en este documento** (quién lo aporta).  
Ambos conviven: por ejemplo, un repuesto de catálogo `tipo_origen=stock` en una línea puede ser `source_type=IN_STOCK` o `CUSTOMER_SUPPLIED` si el cliente lo trae.

---

## Plantillas de desarme

Plantillas globales (empresa=null) o por empresa para generar piezas automáticamente al ingresar un vehículo de desarme.

- **PlantillaDesarme**: nombre, descripción, activa. empresa=null → global; empresa no null → del suscriptor.
- **PlantillaPieza**: nombre_pieza, orden, codigo_base, activo, categoria (opcional).
- **Repuesto.estado_pieza** (solo desarme): disponible, dañado, scrap, vendido — checklist de inspección.

**Servicio** `aplicar_plantilla(vehiculo, plantilla)`:
- Validación multi-tenant: plantilla.empresa == vehiculo.empresa o plantilla global.
- Bloqueo de duplicados: si ya existen piezas de desarme del vehículo, lanza `PlantillaDesarmeError`.
- Transacción atómica.
- Crea repuestos con tipo_origen=desarme, vehiculo_origen=vehiculo, cantidad_stock=1.

**Seed**: `python manage.py seed_plantillas_desarme` crea plantillas globales Sedan, SUV, Pickup, Hatchback, Manual.

---

## Mapa interactivo de piezas

Vista visual del vehículo con zonas clickeables para crear/editar repuestos de desarme.

- **Modelo**: `Repuesto.zona_mapa`, `Repuesto.vista_mapa`, `Repuesto.estado_pieza` incluye "reservada".
- **Vista**: `/desarme/vehiculos/<pk>/mapa/` — `taller:desarme_mapa_piezas`.
- **API**: `POST /desarme/api/vehiculos/<id>/pieza/` — crear/actualizar pieza por zona.
- **Colores**: gris (no revisada), verde (disponible), rojo (dañada), negro (scrap), azul (vendida), amarillo (reservada).
