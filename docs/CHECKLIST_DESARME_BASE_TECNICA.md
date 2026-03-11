# Checklist base técnica – Desarme (fase A)

Revisión ejecutada según tu lista previa a QA. Resumen y alertas.

---

## 1. Campos en modelos vs. informe

| Campo / concepto | Vehiculo | Repuesto | PlantillaPieza | Notas |
|-----------------|----------|----------|----------------|-------|
| **tipo_uso** | ✅ | — | — | En `Vehiculo` (choices cliente/desarme). |
| **estado_desarme** | ✅ | — | — | En `Vehiculo` (ingresado, en_desarme, con_piezas, agotado, cerrado). |
| **activo_operacional** | ✅ | — | — | En `Vehiculo` (Boolean, False al cerrar). |
| **vehiculo_origen** | — | ✅ | — | FK en `Repuesto` → `Vehiculo`. |
| **tipo_origen** | — | ✅ | — | En `Repuesto` (stock, direct, directo, desarme). |
| **estado_pieza** | — | ✅ | — | En `Repuesto` (disponible, dañado, scrap, vendido, reservada). No en PlantillaPieza (la plantilla no tiene estado; el repuesto creado sí). |
| **zona_mapa** | — | ✅ | ✅ | En `Repuesto` y en `PlantillaPieza`. |
| **vista_mapa** | — | ✅ | ✅ | En `Repuesto` y en `PlantillaPieza`. |
| **lado_pieza** | — | — | ✅ (como **lado**) | En `PlantillaPieza` el campo se llama **lado** (left/right/vacío). Código/UI que use “lado_pieza” debe mapear a `lado`. |
| **precio_venta** | — | ✅ | — | En `Repuesto`. |
| **observacion_estado** | — | ✅ (como **observaciones**) | — | En `Repuesto` el campo es **observaciones**. En servicios/vistas se usa el nombre `observacion_estado` en la API y se persiste en `repuesto.observaciones`. Mapeo correcto; no falta campo. |

**Conclusión 1:** Todos los conceptos existen en los modelos. Solo diferencias de nombre: `lado` en plantilla, `observaciones` en repuesto (expuesto como observacion_estado en API).

---

## 2. Migraciones aplicadas y cobertura desarme

- **Estado:** `python manage.py showmigrations taller` → **todas aplicadas** (0001 hasta **0088**).

Cadena relevante para desarme:

| Migración | Contenido |
|-----------|-----------|
| **0083** | Repuesto: `tipo_origen`, `origen_costo`, `vehiculo_origen`. |
| **0084** | Vehiculo: desarme (tipo_uso, estado_desarme, activo_operacional, costos, fechas, etc.). Repuesto: es_usado, controlar_stock. **CostoVehiculoDesarme** creado. Constraint `uq_empresa_patente` con condition. |
| **0085** | **PlantillaDesarme** y **PlantillaPieza** creados. Repuesto: `estado_pieza`. |
| **0086** | Repuesto: `zona_mapa`, `vista_mapa`. Estado_pieza ampliado (reservada). |
| **0087** | PlantillaPieza: `lado`, `zona_mapa`, `vista_mapa`. Repuesto: `observaciones`. Constraint sin condition (corregido en 0088). |
| **0088** | **Constraint `uq_empresa_patente`**: unicidad solo cuando patente informada; permite múltiples vehículos con patente vacía por empresa. |

**Conclusión 2:** **0083–0088 aplicadas**; 0088 deja resuelto el problema de unicidad de patente vacía y forma parte de la base estable.

---

## 3. Constraint `uq_empresa_patente` — corregido (0088)

- En **0087** la constraint quedaba sin `condition`, lo que impedía tener más de un vehículo con patente vacía por empresa.
- **Corrección aplicada:** migración **0088** y modelo actualizados para que la unicidad sea solo cuando la patente está informada:
  - `UniqueConstraint(condition=Q(patente__isnull=False) & ~Q(patente=""), fields=("empresa", "patente"), name="uq_empresa_patente")`
- Resultado: se permiten **múltiples vehículos con patente vacía o null** por empresa (desarme); la patente solo debe ser única cuando tiene valor.

---

## 4. Resumen ejecutivo

- **Campos:** Ok. Todos los conceptos existen donde corresponde.
- **Migraciones:** Ok. **0083–0088 aplicadas**; 0088 deja resuelto el problema de unicidad de patente vacía (forma parte de la base estable).
- **Constraint uq_empresa_patente:** Corregido en 0088 y en modelo.

**Vigilado en QA (no bloquea):** mapeos `lado_pieza` ↔ `lado` y `observacion_estado` ↔ `observaciones` durante aplicación de plantilla, edición de pieza en mapa, guardado AJAX y visualización posterior.

---

## 5. Veredicto y siguientes fases

**Fase A: aprobada ✅**

Orden siguiente:

- **Fase B** — Seed: `seed_plantillas_desarme`, visibilidad de plantillas globales, cantidad de piezas por plantilla.
- **Fase C** — Flujo operativo: crear vehículo desarme → aplicar plantilla → mapa → editar piezas → dashboard → cerrar vehículo.
- **Fase D** — Revisiones finas: tenant, permisos, KPIs, nombres de rutas, consistencia visual y UX.

Guía ejecutable para B/C: ver **docs/FASE_B_C_DESARME.md**.
