# Propuesta técnica: arquitectura Desarme y orígenes de repuesto

**Fecha:** 2025-03-11  
**Objetivo:** Definir la estrategia de modelado para (1) dos tipos de vehículo y (2) tres orígenes de repuesto en documentos, sin duplicar la arquitectura actual y minimizando impacto en el flujo existente.

---

## 1. Resumen ejecutivo

| Área | Decisión recomendada | Motivo principal |
|------|----------------------|------------------|
| **Vehículos** | Un solo modelo `Vehiculo` + campo `tipo_uso` | Reutiliza CRUD, reportes y documentos; evita duplicar lógica y vistas. |
| **Origen repuesto** | Campo `origen_repuesto` en `LineaRepuesto` + modelo `PiezaDesarme` para inventario de yarda | Un solo flujo de documentos; inventario de desarme separado y trazable. |
| **Inventario** | Extender `InventoryService` por tipo de origen; nuevo modelo solo para piezas de desarme | Stock bodega sigue en `Repuesto`; piezas de desarme en `PiezaDesarme`. |

---

## 2. Vehículos: un solo modelo con `tipo_uso`

### 2.1 Reglas de negocio

- **Vehículo de cliente:** entra al taller para reparación/mantención/servicio; no es inventario del negocio; siempre asociado a un `Cliente`.
- **Vehículo comprado para desarme:** pertenece al negocio; fuente de piezas; debe permitir costo de adquisición, recuperación y utilidad.

### 2.2 Opciones evaluadas

| Enfoque | Pros | Contras |
|---------|------|--------|
| **A) Un modelo `Vehiculo` + `tipo_uso`** | Un solo CRUD, una sola lista con filtros, documentos y reportes reutilizan todo; menos código. | `cliente` debe ser opcional o usar “cliente interno” para desarme; validaciones condicionales. |
| **B) Dos entidades (`Vehiculo` + `VehiculoDesarme`)** | Separación nítida de responsabilidades. | Duplicación de campos (marca, modelo, VIN, patente, año…), dos listas, dos flujos, reportes que cruzan tablas. |

### 2.3 Recomendación: un solo modelo con `tipo_uso`

- Mantener **un solo modelo** `Vehiculo`.
- Añadir un campo **`tipo_uso`** (choices) que distinga el rol del vehículo en el negocio.
- Para desarme, **`cliente` en `Vehiculo`** puede manejarse de dos formas (elegir una):

  - **Opción recomendada:** `cliente` **nullable** cuando `tipo_uso == DESARME`. El vehículo de desarme no es de un cliente; es del negocio. En `Documento` el cliente sigue siendo el comprador del servicio/repuesto; el `vehiculo` del documento (si se usa) sería solo para vehículos de cliente.
  - **Alternativa:** Crear un **Cliente interno** por empresa (ej. “Inventario desarme – [Empresa]”) y asignar los vehículos de desarme a ese cliente. Así `cliente` no es nunca null y no se tocan constraints ni listados que asumen “vehículo → cliente”.

Campos a agregar en **`Vehiculo`**:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo_uso` | `CharField(max_length=20, choices=[('CLIENTE','Cliente'), ('DESARME','Desarme')], default='CLIENTE')` | Define si el vehículo es de un cliente o de inventario para desarme. |
| `costo_adquisicion` | `DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)` | Solo sentido cuando `tipo_uso == 'DESARME'`. Costo de compra del vehículo. |
| `fecha_ingreso_desarme` | `DateField(null=True, blank=True)` | Fecha de ingreso a la yarda (desarme). |
| `estado_desarme` | `CharField(max_length=20, null=True, blank=True)` | Ej.: `'EN_YARDA'`, `'EN_DESARME'`, `'DESARMADO'`, `'BAJA'`. Opcional; útil para flujo y reportes. |

Ajustes de modelo y validación:

- **Constraints:**  
  - Si `cliente` pasa a ser nullable: en `clean()` (o constraint) validar: si `tipo_uso == 'CLIENTE'` entonces `cliente` obligatorio; si `tipo_uso == 'DESARME'` entonces `cliente` debe ser null (o el cliente interno según la alternativa).
  - Unicidad patente/VIN: mantener por `(empresa, patente)` y `(empresa, vin)`; aplica a ambos tipos.
- **Documento:**  
  - `Documento.vehiculo` sigue siendo el vehículo del cliente al que atiende la OT/presupuesto/factura. En listados y filtros de “vehículo del documento” se puede restringir a `tipo_uso='CLIENTE'` para no mostrar vehículos de desarme como opción en ese combo.

Con esto se evita duplicar vistas, formularios y reportes; solo se añaden filtros (por `tipo_uso`) donde haga falta (listado vehículos, reportes de desarme).

---

## 3. Repuestos: tres orígenes en documento

### 3.1 Los tres casos

1. **Repuesto nuevo o usado comprado externamente** (otro autopart/proveedor): se usa en el documento pero no sale de stock de bodega ni de inventario de desarme; puede o no actualizar stock si se registra como compra.
2. **Repuesto vendido desde stock en bodega:** ya existe en `Repuesto` (o `Part`); al emitir documento se descuenta de `Repuesto.cantidad_stock` (flujo actual).
3. **Repuesto proveniente de vehículo en desarme:** la pieza está en el inventario de la yarda; al venderla en un documento se debe descontar de ese inventario y permitir medir costo/recuperación/utilidad.

### 3.2 Estrategia recomendada: origen en línea + inventario de desarme

- **Un solo tipo de línea de documento:** `LineaRepuesto`.
- **Campo en `LineaRepuesto`:** **`origen_repuesto`** con tres valores que distinguen el caso sin crear modelos duplicados de “línea”.
- **Inventario de piezas de desarme:** modelo nuevo **`PiezaDesarme`** (una tabla de “stock por pieza extraída de vehículo X”). No reemplaza a `Repuesto`/`Part`; complementa para el flujo desarme.

Así:

- **Origen EXTERNO:** línea con `origen_repuesto='EXTERNO'`. No mueve stock de bodega ni de desarme. Opcional: `costo_linea` para rentabilidad (costo del repuesto comprado para este trabajo).
- **Origen STOCK_BODEGA:** línea con `origen_repuesto='STOCK_BODEGA'` (o valor por defecto para compatibilidad). Debe tener `repuesto` (y/o `part`) y el flujo actual de `InventoryService` descuenta de `Repuesto`.
- **Origen DESARME:** línea con `origen_repuesto='DESARME'` y FK opcional a **`PiezaDesarme`**. Al emitir documento se descuenta cantidad de `PiezaDesarme`; costo/recuperación se calculan con `PiezaDesarme.costo_asignado` y precio de la línea.

### 3.3 Modelo `PiezaDesarme`

Representa una partida de piezas (mismo tipo) provenientes de un vehículo de desarme. No sustituye a `Repuesto`/`Part`; puede vincularse opcionalmente a un catálogo para reutilizar nombre/código.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `vehiculo` | `ForeignKey(Vehiculo, on_delete=PROTECT)` | Vehículo de desarme (debe ser `tipo_uso='DESARME'`). |
| `empresa` | FK o heredado de tenant | Empresa propietaria. |
| `repuesto` | `ForeignKey(Repuesto, null=True, blank=True)` | Opcional: referencia al catálogo legacy. |
| `part` | `ForeignKey(Part, null=True, blank=True)` | Opcional: referencia al catálogo I18N. |
| `codigo` | `CharField(max_length=100)` | Código de la pieza (part number o propio). |
| `nombre` | `CharField(max_length=255)` | Descripción. |
| `cantidad` | `PositiveIntegerField(default=1)` | Unidades disponibles de esta partida (se descuenta al vender). |
| `costo_asignado` | `DecimalField(...)` | Costo imputado a esta partida (ej. prorrateo del costo del vehículo o costo directo). |
| `precio_venta_sugerido` | `DecimalField(..., null=True, blank=True)` | Sugerencia de venta. |
| `fecha_extraccion` | `DateField(null=True, blank=True)` | Cuándo se extrajo/registró. |
| `activo` | `BooleanField(default=True)` | Para no listar partidas ya agotadas o dadas de baja. |

Unicidad: por ejemplo `UniqueConstraint(empresa, vehiculo, codigo)` o (vehiculo, codigo) si el código es único por vehículo; según regla de negocio (¿múltiples partidas del mismo código en el mismo vehículo?).

### 3.4 Cambios en `LineaRepuesto`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `origen_repuesto` | `CharField(max_length=20, choices=[('EXTERNO','Externo'), ('STOCK_BODEGA','Stock bodega'), ('DESARME','Desarme')], default='STOCK_BODEGA')` | Origen de la pieza en esta línea. |
| `pieza_desarme` | `ForeignKey(PiezaDesarme, null=True, blank=True, on_delete=PROTECT)` | Obligatorio cuando `origen_repuesto == 'DESARME'`. |
| `costo_linea` | `DecimalField(..., null=True, blank=True)` | Costo de la línea para rentabilidad (EXTERNO: costo compra; DESARME: puede copiarse de `PiezaDesarme.costo_asignado` o dejarse editable). |

Validaciones en `clean()` de `LineaRepuesto`:

- Si `origen_repuesto == 'DESARME'` → exigir `pieza_desarme` y que `pieza_desarme.cantidad >= cantidad` (o validar en servicio al emitir).
- Si `origen_repuesto == 'STOCK_BODEGA'` → exigir `repuesto` o `part` (como hoy) para poder descontar stock.
- Si `origen_repuesto == 'EXTERNO'` → no descontar stock; opcionalmente exigir `costo_linea` para reportes de margen.

Compatibilidad: todas las líneas existentes pueden migrarse con `origen_repuesto='STOCK_BODEGA'` y `pieza_desarme=None`.

---

## 4. Impacto en creación de documentos

- **Formulario / vista de documento:**  
  - Por cada línea de repuesto, el usuario elige (o se infiere) **origen**: Externo, Stock bodega, Desarme.
  - Según origen:
    - **Externo:** no se exige repuesto/part; se puede pedir código, nombre, cantidad, precio, y opcionalmente costo.
    - **Stock bodega:** flujo actual (selector de repuesto/part, cantidad, precio); se valida stock en `Repuesto` antes de emitir.
    - **Desarme:** selector de `PiezaDesarme` (filtrable por vehículo o por código); cantidad ≤ disponible; precio (y opcionalmente costo desde `PiezaDesarme`).
  - No hace falta “tipos de documento” nuevos; el mismo documento puede mezclar líneas de los tres orígenes.
- **Señales / servicios:**  
  - Al pasar a EMITIDO (o equivalente), además del flujo actual de `InventoryService`:
    - Para líneas con `origen_repuesto == 'DESARME'` y `pieza_desarme` no nulo: descontar `cantidad` de `PiezaDesarme.cantidad` (y marcar inactivo si queda 0).
  - Al anular/revertir: reponer cantidad en `PiezaDesarme` y, como hoy, reponer en `Repuesto` para líneas STOCK_BODEGA.

---

## 5. Impacto en reportes y rentabilidad

- **Rentabilidad por línea:**  
  - Con `costo_linea` (y/o `PiezaDesarme.costo_asignado`) se puede calcular margen por línea: `precio_unitario * cantidad - costo_linea` (o suma de costos si se guarda por unidad).  
  - Por origen: márgenes de “repuesto externo”, “repuesto de bodega”, “pieza de desarme”.
- **Rentabilidad por vehículo de desarme:**  
  - Suma de ventas de líneas con `origen_repuesto='DESARME'` y `pieza_desarme.vehiculo_id = X`.  
  - Costo: `Vehiculo.costo_adquisicion` (y opcionalmente costos asignados a `PiezaDesarme` de ese vehículo).  
  - KPIs: recuperación (%), utilidad bruta por vehículo desarmado.
- **Reportes existentes:**  
  - Reporte de repuestos / dashboard: puede filtrar o desglosar por `origen_repuesto`.  
  - No es necesario duplicar reportes; solo ampliar filtros y columnas.

---

## 6. Resumen de campos a agregar

### 6.1 `Vehiculo`

| Campo | Tipo | Default / notas |
|-------|------|------------------|
| `tipo_uso` | CharField(20, choices) | `'CLIENTE'` |
| `costo_adquisicion` | Decimal(12,2), null | Solo desarme |
| `fecha_ingreso_desarme` | DateField, null | |
| `estado_desarme` | CharField(20), null | EN_YARDA, EN_DESARME, DESARMADO, BAJA |

Posible ajuste: `cliente` nullable cuando `tipo_uso == 'DESARME'` (o uso de cliente interno).

### 6.2 `LineaRepuesto`

| Campo | Tipo | Default / notas |
|-------|------|------------------|
| `origen_repuesto` | CharField(20, choices) | `'STOCK_BODEGA'` |
| `pieza_desarme` | FK PiezaDesarme, null | Cuando origen DESARME |
| `costo_linea` | Decimal(12,2), null | Rentabilidad |

### 6.3 Nuevo modelo `PiezaDesarme`

- `vehiculo`, `empresa`, `repuesto` (null), `part` (null), `codigo`, `nombre`, `cantidad`, `costo_asignado`, `precio_venta_sugerido`, `fecha_extraccion`, `activo`, timestamps.

---

## 7. Cómo no romper el flujo actual

1. **Defaults y migraciones:**  
   - `Vehiculo.tipo_uso` default `'CLIENTE'`.  
   - `LineaRepuesto.origen_repuesto` default `'STOCK_BODEGA'`; `pieza_desarme` y `costo_linea` null.  
   - Migración de datos: todas las líneas existentes quedan con `origen_repuesto='STOCK_BODEGA'`.
2. **InventoryService:**  
   - Mantener la lógica actual para líneas con `repuesto` (y/o `part`) y `origen_repuesto in (None, 'STOCK_BODEGA')`.  
   - Añadir rama: si `origen_repuesto == 'DESARME'` y `pieza_desarme_id`, descontar/reponer en `PiezaDesarme` en lugar de en `Repuesto`.  
   - No procesar stock para `origen_repuesto == 'EXTERNO'`.
3. **Validación de stock:**  
   - Antes de emitir: para STOCK_BODEGA, seguir validando `Repuesto.cantidad_stock`; para DESARME, validar `PiezaDesarme.cantidad >= linea.cantidad`.
4. **Vistas y formularios:**  
   - Listados de vehículos: filtro por `tipo_uso` (y en desarme por `estado_desarme`).  
   - En documento: selector de origen por línea; si es Desarme, mostrar selector de `PiezaDesarme` (y cantidad disponible).  
   - Autocompletes y APIs existentes de repuestos siguen igual; se añade autocomplete o lista de `PiezaDesarme` para líneas de origen desarme.
5. **Documento.vehiculo:**  
   - Sigue siendo el vehículo del cliente. En vistas de creación/edición, filtrar opciones de vehículo por `tipo_uso='CLIENTE'` (y mismo cliente del documento) para no ofrecer vehículos de desarme en ese combo.

---

## 8. Implementación por fases

### Fase 1 – Modelos y datos (sin cambiar flujo visible)

1. Añadir en `Vehiculo`: `tipo_uso`, `costo_adquisicion`, `fecha_ingreso_desarme`, `estado_desarme`; decidir y aplicar regla de `cliente` (nullable o cliente interno).  
2. Crear modelo `PiezaDesarme` y migración.  
3. Añadir en `LineaRepuesto`: `origen_repuesto`, `pieza_desarme`, `costo_linea`; migración con defaults.  
4. Migración de datos: actualizar todas las `LineaRepuesto` existentes a `origen_repuesto='STOCK_BODEGA'`.

### Fase 2 – Inventario y señales

5. Extender `InventoryService`:  
   - Para líneas con `origen_repuesto == 'DESARME'` y `pieza_desarme`, descontar/reponer en `PiezaDesarme`.  
   - Ignorar movimiento de stock para `origen_repuesto == 'EXTERNO'`.  
6. Ajustar validación de stock previa a emisión: incluir disponibilidad de `PiezaDesarme` cuando aplique.  
7. Revisar señales de documento (ej. `signals_inventory.py`) para que llamen a esta lógica al cambiar estado (emitir/anular/editar).

### Fase 3 – UI y flujos

8. Listado de vehículos: filtro por `tipo_uso`; pestaña o vista “Vehículos desarme”.  
9. Formulario de documento: por cada línea de repuesto, selector de origen y, si es Desarme, selector de `PiezaDesarme` y cantidad.  
10. CRUD de `PiezaDesarme` (alta/baja de piezas por vehículo de desarme) y posible pantalla “Inventario desarme” por vehículo.

### Fase 4 – Reportes y rentabilidad

11. Reporte (o sección) “Rentabilidad por vehículo de desarme” (costo vs ingresos por `PiezaDesarme` vendidas).  
12. Desglose por `origen_repuesto` en reportes de repuestos y márgenes.  
13. Dashboard o KPIs de desarme (vehículos en yarda, piezas vendidas, recuperación %).

---

## 9. Conclusión

- **Vehículos:** Un solo modelo `Vehiculo` con `tipo_uso` (CLIENTE | DESARME) y campos opcionales de costo y estado de desarme es la opción más limpia y que menos rompe el sistema actual.  
- **Repuestos en documento:** Un solo modelo de línea (`LineaRepuesto`) con `origen_repuesto` (EXTERNO | STOCK_BODEGA | DESARME) y un modelo nuevo `PiezaDesarme` para el inventario de la yarda permite cubrir los tres casos sin duplicar documentos ni flujos.  
- **Inventario:** Se extiende el `InventoryService` para tratar DESARME (y opcionalmente EXTERNO) además del flujo actual de bodega; no se reemplaza la arquitectura existente.  
- Con defaults adecuados y migraciones de datos, el comportamiento actual se preserva y la nueva funcionalidad se puede exponer de forma gradual por fases.
