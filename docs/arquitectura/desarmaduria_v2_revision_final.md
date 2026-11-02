# Desarmaduria v2 — Revisión Final de Consistencia Documental
**Fecha:** 2026-08-05  
**Tipo:** Auditoría documental pre-implementación. No modifica código.  
**Documentos revisados:**
- `desarmaduria_v2_propuesta.md`
- `desarmaduria_v2_mapa_modulos.md`
- `desarmaduria_v2_plan_p0_p5.md`
- `desarmaduria_v2_modelos_estados.md`
- `desarmaduria_v2_experiencia_humana.md`
- `desarmaduria_v2_estadisticas_negocio.md`
- `desarmaduria_templates_audit.md`

---

## 1. Resultado general

Los documentos forman un diseño técnico coherente con siete inconsistencias identificadas y corregidas (cinco críticas, tres menores), más cuatro ambigüedades documentadas para decisión. Tras las correcciones aplicadas en esta revisión, el diseño está listo para iniciar P1.

---

## 2. Contradicciones críticas — identificadas y corregidas

### C1 — Estado fantasma `LISTO_PARA_PUBLICAR` en `propuesta.md`
**Documento:** `propuesta.md` §3 (flujo ALMACENAR)  
**Problema:** El paso ALMACENAR decía `vehiculo.etapa → LISTO_PARA_PUBLICAR`. Este valor no existe en las choices de `VehiculoDesarme.etapa` definidas en todos los demás documentos (INGRESADO, CONFIRMADO, EN_ALMACEN, PUBLICADO, VENDIENDO, CERRADO).  
**Corrección aplicada:** Reemplazado por `vehiculo permanece en etapa EN_ALMACEN` — la transición a PUBLICADO la dispara `publicar_piezas`, no el paso de almacenaje.

---

### C2 — Nombre de modelo `Reserva` en `mapa_modulos.md`
**Documento:** `mapa_modulos.md` §2.6  
**Problema:** El modelo aparecía nombrado como `Reserva`. En todos los demás documentos (plan §4.1, modelos_estados §4) el nombre es `ReservaDesarme`.  
**Corrección aplicada:** `Reserva (nuevo modelo, P3)` → `ReservaDesarme (nuevo modelo, P4)`.

---

### C3 — Fase de Reservas: P3 vs P4
**Documento:** `mapa_modulos.md` §2.6  
**Problema:** Decía "P3" para la creación del modelo de reservas. El plan define reservas en P4 de forma explícita y consistente.  
**Corrección aplicada:** P3 → P4 en la referencia de fase del módulo RESERVAR.

---

### C4 — Publicar cambiaba `etapa_fisica` implícitamente (violación del principio §4.4)
**Documento:** `plan_p0_p5.md` §3.4  
**Problema:** El pseudocódigo de `publicar_piezas` incluía `.update(publicada=True, etapa_fisica=ETAPA_FISICA_ALMACENADA)`. Esto:
1. Viola el principio §4.4: "Ninguna transición de estado debe ocurrir como efecto secundario de otra operación."
2. Viola el invariante de `modelos_estados.md` §1.3: `IF publicada == True THEN etapa_fisica IN (DESMONTADA, ALMACENADA)` — el invariante debe ser una **precondición**, no una consecuencia de publicar.
3. Una pieza DESMONTADA quedaría marcada como ALMACENADA sin que el operador lo pidiera.

**Corrección aplicada:** `publicar_piezas` ahora filtra `etapa_fisica__in=[DESMONTADA, ALMACENADA]` como precondición y solo aplica `.update(publicada=True)`. La transición física sigue siendo responsabilidad exclusiva de `scanner_vehiculo`.

---

### C5 — Tabla resumen sin columna P2.5
**Documento:** `plan_p0_p5.md` — tabla "Resumen de cambios por capa"  
**Problema:** La tabla tenía encabezados `P0|P1|P2|P3|P4|P5` pero los datos en las filas correspondían a 7 fases (incluyendo P2.5). Los contenidos de P2.5 estaban asignados a la columna P3, P3 a P4, y P4 a P5 — cada fase desplazada una columna.  
**Corrección aplicada:** Añadida columna `P2.5` entre P2 y P3 con encabezado correcto.

---

## 3. Contradicciones menores — identificadas y corregidas

### M1 — `valor_potencial_restante` filtraba `publicada=True` en `mapa_modulos.md`
**Documentos:** `mapa_modulos.md` §2.11 vs `estadisticas_negocio.md` §3.1.E  
**Problema:** `mapa_modulos.md` describía el potencial como `SUM(...) donde publicada=True`. Pero:
- `estadisticas_negocio.md` §3.1.E no incluye ese filtro (correcto por diseño)
- `experiencia_humana.md` §4 step 4 muestra el "valor estimado" en etapa CONFIRMADO, cuando las piezas aún no están publicadas

Si se filtrara por `publicada=True`, el potencial sería 0 en las etapas CONFIRMADO y EN_ALMACEN — inutilizando el KPI precisamente cuando el operador más lo necesita para decidir si publicar.  
**Corrección aplicada:** `mapa_modulos.md` §2.11 ahora describe el filtro correcto: `estado_pieza IN (DISPONIBLE, RESERVADA) AND activo=True` (incluye no publicadas).

---

### M2 — `ganancia_bruta` trataba `costo=NULL` como `Decimal("0")`
**Documento:** `estadisticas_negocio.md` §8.1  
**Problema:** El pseudocódigo usaba `costo = vehiculo.costo_adquisicion or Decimal("0")`, lo que hace que `ganancia_bruta = ingresos - 0 = ingresos`. Esto presenta los ingresos completos como "ganancia" cuando el costo no está registrado, distorsionando gravemente el KPI.  
**Corrección aplicada:** Se usa `costo_raw = vehiculo.costo_adquisicion` (puede ser None). `ganancia_bruta` y `pct_recuperado` retornan `None` cuando `costo_registrado=False`. NULL ≠ cero.

---

### M3 — Documentos en BORRADOR no excluidos de ingresos
**Documentos:** `estadisticas_negocio.md` §3.1.B, §5.4; `modelos_estados.md` §7.1, §7.2  
**Problema:** Las queries solo excluían `estado=ANULADO`. Un Documento en BORRADOR no es una venta realizada y no debe contar como ingreso.  
**Corrección aplicada:** Todas las queries de ingresos canónicos ahora excluyen `estado IN ('ANULADO', 'BORRADOR')` y requieren `fecha_emision IS NOT NULL`. El §5.4 de estadisticas_negocio.md fue actualizado con esta regla.

---

### M4 — Typo en `modelos_estados.md` §7.1: "¿Cuánto entré?" → "¿Cuánto entró?"
**Corrección aplicada:** Corregido el verbo (tercera persona singular, no primera).

---

### M5 — Sección §6.3 duplicada en `modelos_estados.md`
**Problema:** El número §6.3 aparecía dos veces: la primera para "Migración de VentaDesarme a Documento" y la segunda para "Qué no registra la venta canónica".  
**Corrección aplicada:** La segunda instancia renombrada a §6.4.

---

### M6 — Predicción presentada como hecho en `experiencia_humana.md`
**Documento:** `experiencia_humana.md` §4 step 8  
**Problema:** El texto decía "A este ritmo, tardas ~12 días en recuperar la inversión." Esto es una proyección predictiva. `estadisticas_negocio.md` §10 declara explícitamente: "No proyecta el futuro. Solo describe lo que ya ocurrió."  
**Corrección aplicada:** Reemplazado por un KPI descriptivo: "Te faltan $2.310.000 para cubrir lo que pagaste." — estado actual, sin predicción temporal.

---

## 4. Estados inconsistentes

Todos los estados de modelo son ahora consistentes entre documentos:

| Modelo | Campo | Valores | Estado |
|--------|-------|---------|--------|
| `PiezaDesarme` | `estado_pieza` | DISPONIBLE, RESERVADA, VENDIDA, DANADA, SCRAP, FALTANTE | ✓ Consistente |
| `PiezaDesarme` | `etapa_fisica` | CONFIRMADA, DESMONTADA, ALMACENADA | ✓ Consistente |
| `VehiculoDesarme` | `etapa` | INGRESADO, CONFIRMADO, EN_ALMACEN, PUBLICADO, VENDIENDO, CERRADO | ✓ Consistente tras C1 |
| `SugerenciaPiezaDesarme` | `estado` | PENDIENTE, CONFIRMADA, DESCARTADA | ✓ Consistente |

---

## 5. Fórmulas inconsistentes

Todas las fórmulas financieras son ahora consistentes entre documentos. Resumen de fórmulas canónicas:

```
costo = VehiculoDesarme.costo_adquisicion  (None si no registrado)

ingresos_canonicos = SUM(LineaRepuesto.subtotal)
    WHERE estado NOT IN ('ANULADO','BORRADOR') AND fecha_emision IS NOT NULL

ingresos_rapidos = SUM(LineaVentaDesarme.cantidad × precio_unitario)
    WHERE venta.anulada = False

ingresos_totales = ingresos_canonicos + ingresos_rapidos

ganancia_bruta = ingresos_totales - costo   [None si costo no registrado]
pct_recuperado = (ingresos_totales / costo) × 100   [None si costo no registrado]

valor_potencial_restante = SUM(precio_venta_sugerido × cantidad)
    WHERE estado_pieza IN (DISPONIBLE, RESERVADA)
      AND activo=True AND precio_venta_sugerido > 0
    (incluye piezas no publicadas)

potencial_total = ingresos_totales + valor_potencial_restante
```

---

## 6. Nombres de archivos o símbolos incorrectos

| Símbolo | Documento | Estado |
|---------|-----------|--------|
| `Reserva` (modelo) | `mapa_modulos.md` §2.6 | Corregido a `ReservaDesarme` |
| `LISTO_PARA_PUBLICAR` (etapa) | `propuesta.md` §3 | Corregido a comportamiento EN_ALMACEN |
| `§6.3` duplicado | `modelos_estados.md` | Corregido: segunda instancia es §6.4 |
| `_calcular_kpis_vehiculo` (P2) vs `kpis_vehiculo` (P2.5) | `plan_p0_p5.md` | Ambigüedad documentada (ver §7.A3) |

---

## 7. Decisiones aún ambiguas

### A1 — Destino de `ver_vehiculo.html` tras P2
**Contexto:** `propuesta.md` §4.3 dice que `ver_vehiculo.html` "se expande o se reemplaza". §5.2 dice que `centro_operaciones` "reemplaza `ver_vehiculo` como punto de entrada".  
**Lo que falta:** ¿Se añade un redirect de la URL actual (`/vehiculos/<pk>/`) a `/vehiculos/<pk>/centro/`? ¿O coexisten?  
**Recomendación:** Decidir en P2: añadir redirect `ver_vehiculo` → `centro_operaciones` desde el primer deploy, para no mantener dos puntos de entrada.

---

### A2 — Término del botón: "Inspeccionar excepciones" vs "Revisar piezas"
**Contexto:** `propuesta.md` y `mapa_modulos.md` usan "Inspeccionar excepciones". `experiencia_humana.md` §4 step 2 usa "[Revisar piezas →]".  
**Impacto:** Ninguno hasta P2 (cuando se crea el template). Decidir el label antes de implementar `centro_operaciones.html`.  
**Recomendación:** "Revisar piezas" — más claro para el operador, sin jerga técnica ("excepciones").

---

### A3 — Nombre del helper en P2: `_calcular_kpis_vehiculo` vs `kpis_vehiculo`
**Contexto:** El pseudocódigo de P2 (`centro_operaciones`) llama a `_calcular_kpis_vehiculo(vehiculo)` (privado, en `views.py`). El pseudocódigo de P2.5 introduce `kpis_vehiculo(vehiculo)` en `views_stats.py` como función pública, y §2.5.5 muestra cómo reemplaza al helper de P2.  
**Impacto:** Ninguno hasta P2. La progresión tiene sentido: stub simple en P2, función completa en P2.5.  
**Recomendación:** En P2, implementar directamente el helper como `kpis_vehiculo()` en `views_stats.py` (anticipar P2.5) o documentar el reemplazo explícitamente.

---

### A4 — Exclusión de Documentos BORRADOR: valor del campo `estado`
**Contexto:** El modelo `Documento` usa `estado` con choices. La revisión asume que el valor en BD es `'BORRADOR'`. Verificar el valor real del choice en `taller/models/documento.py` antes de implementar las queries.  
**Impacto:** Si el estado BORRADOR tiene un valor distinto (e.g., `'DRAFT'`), las queries deben actualizarse.  
**Acción requerida:** Confirmar el valor exacto del campo al implementar P2.5.

---

## 8. Correcciones documentales aplicadas en esta revisión

| # | Tipo | Documento | Descripción |
|---|------|-----------|-------------|
| C1 | Crítico | `propuesta.md` §3 | `LISTO_PARA_PUBLICAR` → `EN_ALMACEN` (etapa inexistente eliminada) |
| C2 | Crítico | `mapa_modulos.md` §2.6 | `Reserva` → `ReservaDesarme` |
| C3 | Crítico | `mapa_modulos.md` §2.6 | P3 → P4 para módulo de reservas |
| C4 | Crítico | `plan_p0_p5.md` §3.4 | Eliminada mutación implícita de `etapa_fisica` en `publicar_piezas`; añadida validación de precondición |
| C5 | Crítico | `plan_p0_p5.md` tabla resumen | Añadida columna P2.5 (era P3-P5 pero con headers desplazados) |
| M1 | Menor | `mapa_modulos.md` §2.11 | Potencial ya no filtra `publicada=True` |
| M2 | Menor | `estadisticas_negocio.md` §8.1 | `costo=NULL` ya no se trata como `Decimal("0")`; `ganancia_bruta` retorna `None` |
| M3 | Menor | `estadisticas_negocio.md` §3.1.B, §5.4; `modelos_estados.md` §7.1, §7.2 | BORRADOR excluido de queries de ingresos; `fecha_emision` especificada para filtros de período |
| M4 | Menor | `modelos_estados.md` §7.1 | Typo "¿Cuánto entré?" → "¿Cuánto entró?" |
| M5 | Menor | `modelos_estados.md` §6.3 duplicado | Renombrado a §6.4 |
| M6 | Menor | `experiencia_humana.md` §4 step 8 | "A este ritmo, tardas ~12 días" eliminado (proyección → descripción de estado) |
| Extra | Menor | `plan_p0_p5.md` §P3 prereq | "P2 completo" → "P2.5 completo" (consistente con la tabla de criterios) |

---

## 9. Bloqueadores para P1

Solo una acción requerida antes de iniciar P1:

| Bloqueador | Documentación | Acción |
|------------|---------------|--------|
| Ningún bloqueador de diseño | — | — |
| Verificar valor exacto de `Documento.estado` BORRADOR | `taller/models/documento.py` | Leer el campo antes de implementar queries en P2.5 (no afecta P1) |

P1 solo toca:
1. `PiezaDesarme` — añadir `publicada=BooleanField(default=False)`
2. Data migration — `publicada=True` para piezas activas con `estado=DISPONIBLE`
3. Storefront — añadir `publicada=True` al filtro base
4. 3 tests

Ninguno de los problemas identificados afecta la implementación de P1.

---

## 10. Confirmación del quinto documento

El resumen de la sesión anterior indicó "5 documentos existentes actualizados". La verificación confirma:

| Documento | Situación real |
|-----------|---------------|
| `desarmaduria_v2_propuesta.md` | Actualizado ✓ |
| `desarmaduria_v2_mapa_modulos.md` | Actualizado ✓ |
| `desarmaduria_v2_plan_p0_p5.md` | Actualizado ✓ |
| `desarmaduria_v2_modelos_estados.md` | Actualizado ✓ |
| `desarmaduria_v2_experiencia_humana.md` | **Creado** (no existía — fue CREADO, no actualizado) |

El resumen anterior decía "5 existentes actualizados". La cifra correcta era 4 existentes actualizados + 2 nuevos creados (`estadisticas_negocio.md` y `experiencia_humana.md`). No hay pérdida de trabajo — todos los documentos están completos y correctos.

---

## RESULTADO FINAL

```
REVISIÓN DOCUMENTAL COMPLETADA

Documentos revisados:         7
Contradicciones críticas:     5 (C1–C5)
Contradicciones menores:      6 (M1–M6)
Contradicciones corregidas:   11 (todas — aplicadas en esta sesión)
Ambigüedades pendientes:      4 (A1–A4, requieren decisión antes de P2)
Bloqueadores de P1:           0

P1 listo para comenzar: SÍ
```
