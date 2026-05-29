# Cierre de arquitectura del módulo Desarme

**Estado:** En curso (pasos 1–4 aplicados en código).  
**Última actualización:** 2026-03-15.

## Resumen del problema

El módulo desarme quedó a medio camino entre una primera implementación funcional (sobre `Vehiculo`) y una segunda arquitectura (`VehiculoDesarme`), sin cerrar la transición. En producción:

- **Entidad raíz real:** `Vehiculo(tipo_uso=DESARME)` → `PiezaDesarme` (no `VehiculoDesarme`).
- **Stock documental:** El diseño con `LineaRepuesto.pieza_desarme` y `origen_repuesto=DESARME` existe; `InventoryService` ya procesa líneas con `pieza_desarme` y actualiza `PiezaDesarme.cantidad` y `estado_pieza`. Lo que falta en producción es uso real (formularios/UI que creen líneas con `pieza_desarme`).
- **Valorización v4:** No existían tabla histórica, campos de sugerencia separados, endpoints ni UI.

## Decisión arquitectónica: pausar VehiculoDesarme

**Opción elegida:** Consolidar todo sobre **Vehiculo** por ahora.

- Desarme sigue usando `Vehiculo(tipo_uso="DESARME")` como entidad raíz.
- `VehiculoDesarme` existe en modelo y migraciones pero **no se usa** en flujos operativos (scanner, forms, vistas, datos reales).
- No conviene migrar a `VehiculoDesarme` hasta cerrar modelo, stock documental e historial de precios; después se puede retomar la separación si se desea.

## Orden de implementación (y estado)

| Paso | Acción | Estado |
|------|--------|--------|
| 1 | Congelar dirección: desarme sobre Vehiculo; VehiculoDesarme pausado | ✅ Documentado |
| 2 | Ampliar PiezaDesarme (precio_referencia, precio_sugerido, origen_precio, prioridad, revisado, fecha_revision) | ✅ Hecho + migración 0087 |
| 3 | Crear modelo PrecioHistoricoPieza (empresa, pieza_desarme, vehiculo, codigo, nombre, marca, modelo, anio, precio, tipo_evento, origen_precio, fecha) | ✅ Hecho + migración 0087 |
| 4 | Asegurar InventoryService para pieza_desarme (descontar/reponer PiezaDesarme; al llegar a 0 → VENDIDA; al reponer de 0 → DISPONIBLE) | ✅ Ya estaba; añadida lógica de reposición → DISPONIBLE |
| 5 | Probar emisión/anulación con piezas de desarme (y que la UI permita elegir pieza_desarme en líneas) | Pendiente |
| 6 | Cargar inventario real (PiezaDesarme) para vehículos desarme existentes | Pendiente |
| 7 | Implementar v4: endpoints precio-sugerido, batch sugerencias, UI “usar sugerido”, alertas | Pendiente |
| 8 | Opcional: retomar migración a VehiculoDesarme cuando lo anterior esté estable | Futuro |

## Cambios realizados en código

### PiezaDesarme (`taller/models/pieza_desarme.py`)

- **Mantenido:** `precio_venta_sugerido` (base/legado).
- **Añadido:**
  - `precio_referencia` — referencia catálogo/lista.
  - `precio_sugerido` — sugerencia del sistema (modelo/IA/historial).
  - `origen_precio` — CATALOGO | MODELO | HISTORIAL | MANUAL.
  - `prioridad` — para ordenar sugerencias/alertas.
  - `revisado` — si el precio fue revisado por operador.
  - `fecha_revision` — cuándo se revisó.

### PrecioHistoricoPieza (nuevo modelo)

- Campos: empresa, pieza_desarme (nullable), vehiculo, codigo, nombre, marca, modelo, anio (nullable), precio, tipo_evento (VALORIZACION | VENTA | AJUSTE), origen_precio, fecha.
- Índices: (empresa, fecha), (empresa, tipo_evento), (pieza_desarme, fecha).

### InventoryService (`taller/services/inventory_service.py`)

- Ya procesaba líneas con `origen_repuesto=DESARME` y `pieza_desarme_id`.
- **Añadido:** al reponer cantidad (de 0 a >0), si `estado_pieza == VENDIDA` se actualiza a `DISPONIBLE` y `activo=True`.

## Próximos pasos recomendados

1. **Aplicar migración 0087 en servidor:**  
   La BD debe tener el esquema actualizado. En el servidor debe existir el archivo  
   `taller/migrations/0087_pieza_desarme_valorizacion_v4_precio_historico.py` (no generar otra 0087 con `makemigrations`).  
   Pasos y verificaciones detallados: **[APLICAR_MIGRACION_0087_SERVIDOR.md](APLICAR_MIGRACION_0087_SERVIDOR.md)**.

2. **Comprobar flujo documental con desarme:**  
   Que el formulario de documentos permita elegir origen “Desarme” y una `PiezaDesarme`; que al emitir/anular se llame a `InventoryService` y se vea el movimiento de stock en `PiezaDesarme`.

3. **Cargar inventario:**  
   Crear `PiezaDesarme` para los vehículos con `tipo_uso=DESARME` (por catálogo o proceso definido).

4. **V4:**  
   Implementar servicios que escriban/consulten `PrecioHistoricoPieza` y `precio_sugerido`/`origen_precio`; después endpoints y UI de sugerencias.

## Referencias

- Evidencia: VehiculoDesarme total = 0; Vehiculo con tipo_uso DESARME = 5; PiezaDesarme vinculada a Vehiculo.
- Scanner y flujo actual: `taller/desarme/`, `taller/documentos/` (líneas con `pieza_desarme`).
- Stock: `taller/services/inventory_service.py`; constantes en `taller/models/lineas_documento.py` (ORIGEN_DESARME, etc.).
