# Desarmaduria v2 — P2-DB · Resultado de Implementación
**Fecha:** 2026-08-05  
**Estado:** COMPLETO  
**Referencia:** `docs/arquitectura/desarmaduria_v2_plan_p0_p5.md`

---

## 1. Auditoría previa

### 1.1 Campos encontrados en VehiculoDesarme

| Campo | Tipo | Valores posibles |
|-------|------|-----------------|
| `estado_desarme` | CharField (legacy) | INGRESADO, DESARMANDO, DESARMADO, AGOTADO, RECUPERADO, CERRADO, BAJA |
| `estado_operativo` | CharField (nuevo P2-DB) | INGRESADO, EN_REVISION, EN_PROCESAMIENTO, EN_CIERRE, CERRADO |

`estado_desarme` no se elimina. Ambos coexisten hasta consolidación futura respaldada por evidencia.

### 1.2 Modelos existentes antes de P2-DB

| Modelo | Propósito | ¿Reutilizable para eventos operacionales? |
|--------|-----------|------------------------------------------|
| `VehicleFinancialEvent` | Eventos financieros (compra, venta, ajuste de dinero) | No — propósito diferente |
| `VehiculoFinancialSnapshot` | Snapshot financiero instantáneo | No — es snapshot, no evento |
| `vehicle_lifecycle_service.py` | Gestión de `Vehiculo` (reparación, NO VehiculoDesarme) | No — entidad diferente |

**Conclusión:** No existe equivalente operacional. Se creó `VehiculoDesarmeEvent`.

### 1.3 Mixins disponibles

| Mixin | Campos |
|-------|--------|
| `TenantScoped` (core.models) | `empresa` (FK), `created_at`, `updated_at` |
| `AuditMixin` (taller.models.mixins) | `created_at`, `updated_at`, `created_by`, `updated_by` |

`VehiculoDesarmeEvent` hereda de `TenantScoped` únicamente. Añade `created_by` manualmente para evitar duplicación de `created_at`/`updated_at` con AuditMixin.

### 1.4 Valores reales de Documento.estado

| Valor DB | Label | Default |
|----------|-------|---------|
| `BORRADOR` | Borrador | No |
| `EMITIDO` | Emitido | **Sí** |
| `ANULADO` | Anulado | No |

El filtro de ingresos debe excluir `estado IN ('BORRADOR', 'ANULADO')` y `fecha_emision IS NOT NULL`.

### 1.5 Última migración previa

`0161_piezadesarme_publicada` (P1)

---

## 2. Cambios implementados

### 2.1 `taller/models/vehiculo_desarme.py`

- Añadido `EstadoOperativo(TextChoices)` con 5 estados.
- Añadido `estado_operativo = CharField(max_length=24, default=INGRESADO, db_index=True)`.
- Añadido índice compuesto `(empresa, estado_operativo)`.

### 2.2 `taller/models/vehiculo_desarme_event.py` (nuevo)

- Modelo `VehiculoDesarmeEvent(TenantScoped)` — registro append-only.
- Clase `TipoEventoDesarme(TextChoices)` — 17 tipos incluyendo `MIGRACION_ESTADO_INICIAL`.
- FKs: `vehiculo` (CASCADE), `pieza` (SET_NULL, nullable), `documento` (SET_NULL, nullable), `created_by` (SET_NULL, nullable).
- Campos: `tipo`, `metadata (JSONField)`, `idempotency_key`, `occurred_at`.
- Validaciones en `clean()`: empresa coherente, pieza del mismo vehículo y empresa, documento de la misma empresa, metadata es dict.
- Orden de validación: empresa primero (violación más grave), luego vehículo.

### 2.3 `taller/models/__init__.py`

- Exporta `VehiculoDesarme`, `EstadoOperativo`, `VehiculoDesarmeEvent`, `TipoEventoDesarme`.

### 2.4 `taller/services/vehicle_state_service.py` (nuevo)

- Clase `VehicleStateService` con método `transition()`.
- Matriz de transiciones en `_TRANSITIONS` (única fuente de verdad).
- `select_for_update()` + `transaction.atomic()` para bloqueo transaccional.
- Idempotencia: si `idempotency_key` ya existe en el tenant, retorna evento existente sin crear duplicado.
- Genera evento `ESTADO_OPERATIVO_CAMBIADO` con metadata `{from, to, reason}`.
- `TransicionInvalidaError` para transiciones no permitidas.

### 2.5 Migraciones

| Migración | Tipo | Contenido |
|-----------|------|-----------|
| `0162` | Esquema | `estado_operativo`, modelo `VehiculoDesarmeEvent`, índices, constraint de idempotencia |
| `0163` | Datos | Backfill de `estado_operativo` + evento `MIGRACION_ESTADO_INICIAL` por vehículo |

### 2.6 Admin

- `VehiculoDesarmeAdmin`: `list_display`, `list_filter`, `search_fields` con `estado_operativo`.
- `VehiculoDesarmeEventAdmin`: append-only (sin add, change, delete). Lista `occurred_at`, `tipo`, `vehiculo`, `created_by`.

### 2.7 Diagnóstico

- `python manage.py diagnostico_estados_desarme [--empresa-id ID]`
- Solo lectura. Muestra: totales, distribución por estado legacy y operativo, actividad operacional, eventos por tipo, inconsistencias detectadas.

---

## 3. Conteos antes y después del backfill

| Estado | Pre-backfill (todos INGRESADO default) | Post-backfill |
|--------|----------------------------------------|---------------|
| INGRESADO | 28 | 12 |
| EN_REVISION | 0 | 1 |
| EN_PROCESAMIENTO | 0 | 9 |
| EN_CIERRE | 0 | 0 |
| CERRADO | 0 | 6 |

Eventos `MIGRACION_ESTADO_INICIAL` creados: **28**

---

## 4. Matriz de transiciones permitidas

```
INGRESADO → EN_REVISION          (flujo normal)
INGRESADO → EN_PROCESAMIENTO     (flujo admin / directo)
EN_REVISION → EN_PROCESAMIENTO
EN_PROCESAMIENTO → EN_CIERRE
EN_CIERRE → CERRADO
CERRADO → (ninguno)              ← estado terminal en esta fase
```

Cualquier otra combinación lanza `TransicionInvalidaError`.

---

## 5. Constraints e índices

| Nombre | Tipo | Campos |
|--------|------|--------|
| `taller_veh_des_emp_est_op_idx` | Index | `empresa, estado_operativo` |
| `desarme_ev_emp_veh_occ_idx` | Index | `empresa, vehiculo, occurred_at` |
| `desarme_ev_emp_tipo_occ_idx` | Index | `empresa, tipo, occurred_at` |
| `uniq_desarme_event_idempotency_tenant` | UniqueConstraint (partial) | `empresa, idempotency_key` WHERE `NOT NULL` |

---

## 6. Tests

| Suite | Tests | Resultado |
|-------|-------|-----------|
| `test_p2_db_estado_operativo.py` | 30 | 30/30 ✓ |
| `test_p1_publicada.py` (regresión) | 9 | 9/9 ✓ |
| `test_venta_inventario_stock.py` (regresión) | 10 | 10/10 ✓ |

---

## 7. Archivos modificados

| Archivo | Operación |
|---------|-----------|
| `taller/models/vehiculo_desarme.py` | Modificado — `EstadoOperativo`, campo `estado_operativo`, índice |
| `taller/models/vehiculo_desarme_event.py` | Creado |
| `taller/models/__init__.py` | Modificado — exporta nuevos modelos |
| `taller/migrations/0162_vehiculodesarme_estado_operativo_events.py` | Creado |
| `taller/migrations/0163_backfill_estado_operativo.py` | Creado |
| `taller/services/vehicle_state_service.py` | Creado |
| `taller/management/commands/diagnostico_estados_desarme.py` | Creado |
| `taller/admin.py` | Modificado — admin para VehiculoDesarme y VehiculoDesarmeEvent |
| `taller/tests/test_p2_db_estado_operativo.py` | Creado |

---

## 8. Riesgos y rollback

**Rollback de migraciones:** `python manage.py migrate taller 0161` revertirá las migraciones 0163 (elimina eventos migración) y 0162 (elimina tabla y campo). El campo `estado_desarme` queda intacto.

**Riesgo bajo:** No se modificó ninguna view, template, URL ni lógica de ventas/kiosko.

**Riesgo pendiente:** `select_for_update()` en SQLite no bloquea (silenciosamente ignorado). Los tests de bloqueo real requieren PostgreSQL. Documentado en el código del servicio.

---

## 9. Trabajo pendiente para P2 visual

- Implementar `get_vehicle_operations_summary(vehiculo)` — selector de lectura pura.
- Conectar `VehicleStateService.transition()` a las views de revisión y publicación.
- Crear eventos `PIEZA_CONFIRMADA`, `PIEZA_PUBLICADA`, etc. desde las views existentes.
- Construir `centro_operaciones.html` según diseño de P1.5.
- Decidir D1 (EventoVehiculo propio vs query compuesta) — **ya resuelta**: se usó modelo propio.
- Decidir D3 (registro de fecha de cambio de etapa) — **ya resuelta**: `occurred_at` en VehiculoDesarmeEvent.
- Cerrar D4 (compartir link en storefront).
