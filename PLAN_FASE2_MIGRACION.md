# PLAN FASE 2 — Repunte FK vehiculo → vehiculo_desarme
Generado: 2026-06-25
Opción de gap seleccionada: **Opción A** (top-up sync dentro de 0143)

---

## Contexto

Fase 1 cerrada y ensayada: migraciones 0137–0141 crean `VehiculoDesarme` y copian
los 49 `Vehiculo(tipo_uso='DESARME')` con IDs explícitos idénticos al origen.
Producción aún no tocada; todo lo de Fase 1 está en archivos locales sin commitear.

Fase 2: repuntar el FK `vehiculo` (→ `taller.Vehiculo`) de 5 tablas hacia
`vehiculo_desarme` (→ `taller.VehiculoDesarme`), renombrando el campo.

Invariante clave que permite el UPDATE directo:
```
VehiculoDesarme.id == Vehiculo(tipo_uso='DESARME').id   (garantizado por 0141)
→ UPDATE tabla SET vehiculo_desarme_id = vehiculo_id  (sin mapeo de IDs)
```

---

## Secuencia de migraciones

```
0142  ADD nullable FK vehiculo_desarme en las 5 tablas     (schema-only)
0143  Top-up sync + poblar vehiculo_desarme_id             (data)
0144  NOT NULL + constraints + índices                     (schema)
0145  Limpieza: RemoveField vehiculo de las 5 tablas       (schema — DIFERIDA)
```

---

## 0142 — `0142_fase2_add_vehiculo_desarme_nullable`

Tipo: schema-only. Una migración, 5 AddField.
No se tocan constraints ni índices existentes.

### Campos a agregar

```python
# PiezaDesarme
vehiculo_desarme = models.ForeignKey(
    "taller.VehiculoDesarme",
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name="piezas_desarme",
)

# SugerenciaPiezaDesarme
vehiculo_desarme = models.ForeignKey(
    "taller.VehiculoDesarme",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="sugerencias_piezas",
)

# PrecioHistoricoPieza
vehiculo_desarme = models.ForeignKey(
    "taller.VehiculoDesarme",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="precios_historicos_pieza",
)

# VehiculoFinancialSnapshot
vehiculo_desarme = models.ForeignKey(
    "taller.VehiculoDesarme",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="financial_snapshots",
)

# VehicleFinancialEvent
vehiculo_desarme = models.ForeignKey(
    "taller.VehiculoDesarme",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="financial_events",
)
```

Ninguna lleva `limit_choices_to` — VehiculoDesarme es siempre desarme por definición.

### Nota sobre related_names durante la transición (intencional, no es un error)

Durante el período entre 0142 y 0145 (mientras ambos campos coexisten en el modelo),
cada tabla tendrá dos FKs activos:

- `vehiculo`       → `Vehiculo`       con `related_name="piezas_desarme"` (ejemplo)
- `vehiculo_desarme` → `VehiculoDesarme` con `related_name="piezas_desarme"` (mismo nombre)

Esto es válido en Django porque `related_name` es único **por modelo destino**, no
globalmente. `vehiculo.piezas_desarme` existe en `Vehiculo`; `vehiculo_desarme.piezas_desarme`
existe en `VehiculoDesarme`. Son dos modelos distintos — Django no los confunde y
`manage.py check` no genera ningún error. Esta coexistencia es intencional y temporal.

La misma situación aplica a las otras 4 tablas con sus respectivos `related_name`.

---

## 0143 — `0143_fase2_poblar_vehiculo_desarme`

Tipo: data migration. `RunPython`.

### Por qué se necesita top-up sync (Opción A)

0141 copia todos los `Vehiculo(tipo_uso='DESARME')` existentes en el momento
de aplicarse. Después de 0141 y antes de 0143, el código de producción sigue
creando `Vehiculo(tipo_uso='DESARME')` nuevos (aún no fue actualizado a
VehiculoDesarme). Esos Vehiculo nuevos NO tendrán VehiculoDesarme correspondiente.
Si 0143 hace el UPDATE sin el top-up sync previo, el FK constraint fallará para
esas filas. El top-up sync replica exactamente la lógica de 0141 para cubrir
el gap.

### Función `forwards`

```python
def forwards(apps, schema_editor):
    Vehiculo        = apps.get_model("taller", "Vehiculo")
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")

    # ── Paso 1: Top-up sync ──────────────────────────────────────────────────
    # Crear VehiculoDesarme para cualquier Vehiculo(DESARME) sin entrada aún.
    # Misma lógica de 0141; es idempotente (el filter(vehiculo_origen_id=v.id).exists()
    # evita duplicados).
    nuevos = 0
    for v in Vehiculo.objects.filter(tipo_uso="DESARME").order_by("id").iterator():
        if VehiculoDesarme.objects.filter(vehiculo_origen_id=v.id).exists():
            continue
        vd = VehiculoDesarme(
            id=v.id,
            empresa_id=v.empresa_id,
            vehiculo_origen_id=v.id,
            marca_id=v.marca_id,
            marca_texto=v.marca_texto,
            modelo_id=v.modelo_id,
            modelo_texto=v.modelo_texto,
            patente=v.patente or "",
            anio=v.anio,
            color_id=v.color_id,
            vin=v.vin,
            motor_id=v.motor_id,
            caja_id=v.caja_id,
            millas=v.millas,
            fecha_ingreso_desarme=v.fecha_ingreso_desarme,
            estado_desarme=v.estado_desarme,
            ubicacion_fisica=v.ubicacion_fisica,
            fecha_baja_desarme=v.fecha_baja_desarme,
            observaciones_desarme=v.observaciones_desarme,
            es_placeholder=bool(v.es_placeholder),
            tipo_carroceria=v.tipo_carroceria,
            precio_compra=v.precio_compra,
            monto_chatarra=v.monto_chatarra,
            transporte_grua_desarme=v.transporte_grua_desarme,
            otros_gastos_desarme=v.otros_gastos_desarme,
            vendedor_desarme_id=v.vendedor_desarme_id,
        )
        vd.save(force_insert=True)
        nuevos += 1

    if nuevos > 0 and schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval("
                "    pg_get_serial_sequence('taller_vehiculodesarme', 'id'),"
                "    COALESCE((SELECT MAX(id) FROM taller_vehiculodesarme), 1)"
                ")"
            )

    # ── Paso 2: UPDATEs directos ─────────────────────────────────────────────
    # vehiculo_desarme_id = vehiculo_id es válido porque 0141 + top-up garantizan
    # que cada vehiculo_id en estas tablas tiene VehiculoDesarme.id idéntico.
    tablas = [
        "taller_piezadesarme",
        "taller_sugerenciapiezadesarme",
        "taller_preciohistoricopieza",
        "taller_vehiculofinancialsnapshot",
        "taller_vehiclefinancialevent",
    ]
    with schema_editor.connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(
                f"UPDATE {tabla} SET vehiculo_desarme_id = vehiculo_id"
                f" WHERE vehiculo_desarme_id IS NULL"
            )

    # ── Paso 3: Validación — abort si queda algún NULL ───────────────────────
    with schema_editor.connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(
                f"SELECT COUNT(*) FROM {tabla} WHERE vehiculo_desarme_id IS NULL"
            )
            count = cursor.fetchone()[0]
            if count > 0:
                raise ValueError(
                    f"0143 abortado: {tabla} tiene {count} filas con "
                    f"vehiculo_desarme_id NULL tras el UPDATE. "
                    f"Revisar si hay vehiculo_id sin VehiculoDesarme correspondiente."
                )
```

Nota: `SugerenciaPiezaDesarme` y `PrecioHistoricoPieza` pueden tener 0 filas
(tabla nueva / tabla vacía en producción). UPDATE y COUNT sobre tablas vacías
son válidos — el COUNT da 0 y pasa la validación.

### Función `backwards`

```python
def backwards(apps, schema_editor):
    tablas = [
        "taller_piezadesarme",
        "taller_sugerenciapiezadesarme",
        "taller_preciohistoricopieza",
        "taller_vehiculofinancialsnapshot",
        "taller_vehiclefinancialevent",
    ]
    with schema_editor.connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(
                f"UPDATE {tabla} SET vehiculo_desarme_id = NULL"
            )
    # El top-up sync no se deshace: los VehiculoDesarme creados en el sync
    # se dejan en la tabla (equivalen a haber corrido 0141 sobre ellos).
```

---

## 0144 — `0144_fase2_schema_vehiculo_desarme`

Tipo: schema migration. Sin datos. Transforma el campo nullable en NOT NULL
y reemplaza todos los constraints/índices que referencian la columna vieja.

### PiezaDesarme (5 operaciones)

```
1. RemoveConstraint("piezadesarme", "unique_codigo_por_empresa_vehiculo")
       Dropa: UNIQUE (empresa_id, vehiculo_id, codigo)

2. RemoveIndex("piezadesarme", "<nombre auto-generado por Django>")
       Dropa: INDEX (empresa_id, vehiculo_id)
       Nombre real resuelto por makemigrations al leer el estado actual del modelo.

3. AlterField("piezadesarme", "vehiculo_desarme")
       vehiculo_desarme: null=True, blank=True  →  null=False, blank=False

4. AddConstraint("piezadesarme",
       UniqueConstraint(
           fields=["empresa", "vehiculo_desarme", "codigo"],
           name="unique_codigo_por_empresa_vehiculo_desarme",
       ))

5. AddIndex("piezadesarme",
       Index(fields=["empresa", "vehiculo_desarme"]))
```

Razonamiento sobre ventana de coexistencia: el UNIQUE viejo está sobre
`(empresa_id, vehiculo_id, codigo)` y el nuevo sobre `(empresa_id, vehiculo_desarme_id, codigo)`.
Son columnas distintas en Postgres. Pueden coexistir sin conflicto de datos.
La operación Remove→Add en la misma migración transaccional no deja ventana de
integridad comprometida — entre el Remove y el Add, no hay escrituras externas
(la migración corre dentro de una transacción).

---

### SugerenciaPiezaDesarme (7 operaciones)

```
1. RemoveConstraint("sugerenciapiezadesarme", "unique_sugerencia_por_vehiculo")
       Dropa: UNIQUE (vehiculo_id, codigo)

2. RemoveIndex("sugerenciapiezadesarme", "sug_pieza_emp_veh_idx")
       Dropa: INDEX (empresa_id, vehiculo_id)
       Nombre explícito en el modelo — referenciable directamente.

3. RemoveIndex("sugerenciapiezadesarme", "sug_pieza_emp_veh_est_idx")
       Dropa: INDEX (empresa_id, vehiculo_id, estado)
       Nombre explícito en el modelo — referenciable directamente.

4. AlterField("sugerenciapiezadesarme", "vehiculo_desarme")
       vehiculo_desarme: null=True, blank=True  →  null=False, blank=False

5. AddConstraint("sugerenciapiezadesarme",
       UniqueConstraint(
           fields=["vehiculo_desarme", "codigo"],
           name="unique_sugerencia_por_vehiculo_desarme",
       ))

6. AddIndex("sugerenciapiezadesarme",
       Index(
           fields=["empresa", "vehiculo_desarme"],
           name="sug_pieza_emp_veh_d_idx",
       ))

7. AddIndex("sugerenciapiezadesarme",
       Index(
           fields=["empresa", "vehiculo_desarme", "estado"],
           name="sug_pieza_emp_veh_d_est_idx",
       ))
```

---

### PrecioHistoricoPieza (1 operación)

No tiene UniqueConstraint ni índices nombrados sobre `vehiculo_id`.
Los 3 índices existentes son sobre `(empresa, fecha)`, `(empresa, tipo_evento)` y
`(pieza_desarme, fecha)` — ninguno toca vehiculo. Tabla vacía en producción.

```
1. AlterField("preciohistoricopieza", "vehiculo_desarme")
       vehiculo_desarme: null=True, blank=True  →  null=False, blank=False
```

---

### VehiculoFinancialSnapshot (5 operaciones)

Dos índices compuestos que incluyen `vehiculo` sin nombre explícito →
sus nombres auto-generados por Django se resuelven al correr makemigrations.

```
1. RemoveIndex("vehiculofinancialsnapshot", "<nombre auto>")
       Dropa: INDEX (vehiculo_id, fecha)

2. RemoveIndex("vehiculofinancialsnapshot", "<nombre auto>")
       Dropa: INDEX (vehiculo_id, source_event_count)

3. AlterField("vehiculofinancialsnapshot", "vehiculo_desarme")
       vehiculo_desarme: null=True, blank=True  →  null=False, blank=False

4. AddIndex("vehiculofinancialsnapshot",
       Index(fields=["vehiculo_desarme", "fecha"]))

5. AddIndex("vehiculofinancialsnapshot",
       Index(fields=["vehiculo_desarme", "source_event_count"]))
```

No hay UniqueConstraint sobre `vehiculo` en esta tabla (el único UNIQUE es sobre
`snapshot_hash` — no se toca).

---

### VehicleFinancialEvent (3 operaciones)

Un único índice compuesto que incluye `vehiculo`. Sin nombre explícito →
nombre auto-generado resuelto por makemigrations.

```
1. RemoveIndex("vehiclefinancialevent", "<nombre auto>")
       Dropa: INDEX (vehiculo_id, tipo, fecha)

2. AlterField("vehiclefinancialevent", "vehiculo_desarme")
       vehiculo_desarme: null=True, blank=True  →  null=False, blank=False

3. AddIndex("vehiclefinancialevent",
       Index(fields=["vehiculo_desarme", "tipo", "fecha"]))
```

El UNIQUE condicional sobre `event_hash` no toca `vehiculo` — no se modifica.

---

## 0145 — `0145_fase2_limpieza_vehiculo` (DIFERIDA)

Tipo: schema-only. `RemoveField("vehiculo")` en las 5 tablas.

```
RemoveField("piezadesarme",             "vehiculo")
RemoveField("sugerenciapiezadesarme",   "vehiculo")
RemoveField("preciohistoricopieza",     "vehiculo")
RemoveField("vehiculofinancialsnapshot","vehiculo")
RemoveField("vehiclefinancialevent",    "vehiculo")
```

Cada `RemoveField` dropa en Postgres:
- La columna `vehiculo_id`
- El FK constraint automático de Django (`taller_TABLA_vehiculo_id_XXXX_fk`)
- El índice de FK automático creado por Postgres sobre la columna FK

### Cuándo aplicar 0145

Esta migración se escribe en el mismo commit que 0142–0144 pero **NO se aplica
en la misma ventana**. Es una migración de limpieza diferida.

Condiciones para aplicarla (todas deben cumplirse):
1. Los 17 archivos de código de la lista siguiente están actualizados y desplegados.
2. La aplicación lleva **mínimo 14 días en producción** sin ninguna referencia a
   `.vehiculo` o `vehiculo_id` en logs de error provenientes de las 5 tablas.
3. `grep -r "\.vehiculo\b\|vehiculo_id" taller/` sobre las rutas de las 5 tablas
   devuelve cero ocurrencias en código activo (excluyendo la propia definición
   del campo en los modelos, que ya no existe tras el commit de código de Fase 2).
4. Aprobación explícita antes de correr el migrate en producción.
5. `_ensure_vehiculo_desarme()` en `taller/desarme/services.py` eliminada: la función
   bridge es temporal y existe solo mientras algún call-site pueda recibir un `Vehiculo`
   legacy en lugar de `VehiculoDesarme`. Una vez que los 14 archivos no bloqueantes
   leen `vehiculo_desarme` directamente y ningún código pasa un `Vehiculo` a estas
   funciones, eliminar `_ensure_vehiculo_desarme`, el import de `Vehiculo` de ese
   módulo, y los guards `isinstance(vehiculo, Vehiculo)` en `inicializar_sugerencias`.

### Por qué diferida

La columna `vehiculo_id` vieja tiene datos reales (todos los FKs históricos).
Si hay algún código que no fue actualizado y sigue leyendo esa columna, falla
silenciosamente antes de la limpieza pero con datos; después de la limpieza,
falla con `column does not exist` (error visible). Mantenerla 14 días da margen
para detectar rutas poco ejercidas en producción (vistas de bajo tráfico,
exports nocturnos, management commands que solo corren semanalmente).

---

## Archivos de código a actualizar — lista completa (1–17)

### BLOQUEANTES — manage.py check falla o makemigrations genera basura sin ellos

Estos 5 archivos deben estar actualizados **antes de correr cualquier migración
de Fase 2**, porque definen los campos que 0142 va a agregar y 0144 va a modificar,
o porque causan `FieldError` en tiempo de importación (ModelForm.__new__ valida
`fields` contra el modelo al cargar el módulo, antes de que llegue ninguna request).

---

**1. `taller/models/pieza_desarme.py`**

Cambios en `PiezaDesarme`:
- Renombrar FK `vehiculo` → `vehiculo_desarme`, target `"taller.VehiculoDesarme"`,
  eliminar `limit_choices_to={"tipo_uso": "DESARME"}`, mantener `on_delete=PROTECT`.
- En `clean()`: eliminar bloque que valida `vehiculo.tipo_uso != "DESARME"`
  (VehiculoDesarme no tiene campo `tipo_uso`; la validación es redundante por diseño).
- En `Meta`: actualizar `UniqueConstraint` (campo `vehiculo` → `vehiculo_desarme`,
  nuevo nombre `unique_codigo_por_empresa_vehiculo_desarme`).
- En `Meta.indexes`: actualizar `Index(["empresa", "vehiculo"])` → `Index(["empresa", "vehiculo_desarme"])`.

Cambios en `PrecioHistoricoPieza`:
- Renombrar FK `vehiculo` → `vehiculo_desarme`, target `"taller.VehiculoDesarme"`,
  mantener `on_delete=CASCADE`. Sin cambios en Meta (no tenía índices sobre vehiculo).

---

**2. `taller/models/sugerencia_pieza_desarme.py`**

Cambios en `SugerenciaPiezaDesarme`:
- Renombrar FK `vehiculo` → `vehiculo_desarme`, target `"taller.VehiculoDesarme"`,
  mantener `on_delete=CASCADE`.
- En `Meta.constraints`: `UniqueConstraint(["vehiculo", "codigo"], name="unique_sugerencia_por_vehiculo")`
  → `UniqueConstraint(["vehiculo_desarme", "codigo"], name="unique_sugerencia_por_vehiculo_desarme")`.
- En `Meta.indexes`:
  - `Index(["empresa", "vehiculo"], name="sug_pieza_emp_veh_idx")`
    → `Index(["empresa", "vehiculo_desarme"], name="sug_pieza_emp_veh_d_idx")`
  - `Index(["empresa", "vehiculo", "estado"], name="sug_pieza_emp_veh_est_idx")`
    → `Index(["empresa", "vehiculo_desarme", "estado"], name="sug_pieza_emp_veh_d_est_idx")`

---

**3. `taller/models/vehiculo_financial.py`**

Cambios en el import (línea 7):
```python
# ANTES
from .vehiculos import Vehiculo
# DESPUÉS
from .vehiculo_desarme import VehiculoDesarme
```

Cambios en `VehiculoFinancialSnapshot`:
- Renombrar FK `vehiculo` → `vehiculo_desarme = ForeignKey(VehiculoDesarme, ...)`,
  mantener `on_delete=CASCADE`.
- En `Meta.indexes`:
  - `Index(["vehiculo", "fecha"])` → `Index(["vehiculo_desarme", "fecha"])`
  - `Index(["vehiculo", "source_event_count"])` → `Index(["vehiculo_desarme", "source_event_count"])`
  (el `Index(["snapshot_hash"])` no se toca)

Cambios en `VehicleFinancialEvent` (nombre exacto: inglés, "Vehicle" no "Vehiculo"):
- Renombrar FK `vehiculo` → `vehiculo_desarme = ForeignKey(VehiculoDesarme, ...)`,
  mantener `on_delete=CASCADE`.
- En `Meta.indexes`:
  - `Index(["vehiculo", "tipo", "fecha"])` → `Index(["vehiculo_desarme", "tipo", "fecha"])`
  (los índices sobre `linea_repuesto`, `event_hash`, `event_type` no se tocan)

---

**4. `taller/desarme/forms.py`** ← PROMOVIDO A BLOQUEANTE (descubierto en dry-run)

Bloqueante por `FieldError` al importar: `ModelForm.__new__` evalúa `Meta.fields`
contra el modelo en tiempo de importación. Con la ruta del servidor activa, Django
importa este módulo al arrancar → falla antes de atender ninguna request.

Cambios ya aplicados:
- Línea 4 (imports): agregar `from taller.models.vehiculo_desarme import VehiculoDesarme`
- Línea 439 (Meta.fields): `"vehiculo"` → `"vehiculo_desarme"` ← ERA EL BLOQUEANTE
- Línea 454: `self.fields["vehiculo"].queryset = Vehiculo.objects.filter(empresa=self.empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)`
  → `self.fields["vehiculo_desarme"].queryset = VehiculoDesarme.objects.filter(empresa=self.empresa)`
- Línea 458: `self.fields["vehiculo"].initial` → `self.fields["vehiculo_desarme"].initial`
- Línea 459: `self.fields["vehiculo"].disabled` → `self.fields["vehiculo_desarme"].disabled`

Pendiente (mismo archivo, no bloqueante — va en el commit de los 14 no-bloqueantes):
- Líneas 131, 393: `instance.tipo_uso = Vehiculo.TIPO_USO_DESARME` en `VehiculoDesarmeForm`
  → eliminar (VehiculoDesarme no tiene campo `tipo_uso`; actualizar cuando la vista
  deje de crear Vehiculo y empiece a crear VehiculoDesarme).

---

**5. `taller/documentos/desarme/forms.py`** ← PROMOVIDO A BLOQUEANTE (activa, 4 call-sites en views.py)

Misma causa que archivo 4: `PiezaDesarmeForm` importa desde `PiezaDesarme` y evalúa
`fields = PIEZA_DESARME_PRINCIPALES + PIEZA_DESARME_OPCIONALES` en tiempo de importación.
`PIEZA_DESARME_PRINCIPALES` incluía `"vehiculo"` (definición a nivel de módulo, línea 73).

Cambios ya aplicados:
- Línea 5 (imports): agregar `from taller.models.vehiculo_desarme import VehiculoDesarme`
- Línea 73 (PIEZA_DESARME_PRINCIPALES): `"vehiculo"` → `"vehiculo_desarme"` ← ERA EL BLOQUEANTE
- Línea 109: `self.fields["vehiculo"].queryset = Vehiculo.objects.filter(empresa=self.empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)`
  → `self.fields["vehiculo_desarme"].queryset = VehiculoDesarme.objects.filter(empresa=self.empresa)`
- Línea 113: `self.fields["vehiculo"].initial` → `self.fields["vehiculo_desarme"].initial`
- Línea 114: `self.fields["vehiculo"].disabled` → `self.fields["vehiculo_desarme"].disabled`

Pendiente (mismo archivo, no bloqueante):
- Línea 63 (`VehiculoDesarmeForm.save`): `instance.tipo_uso = Vehiculo.TIPO_USO_DESARME`
  → eliminar (cuando la vista actualice a VehiculoDesarme).

---

**6. `taller/admin.py`** ← PROMOVIDO A BLOQUEANTE (detectado por manage.py check)

No encontrado en la auditoría de texto porque el patrón grep buscaba `.vehiculo_id` o
`tipo_uso='DESARME'`; los literales de texto en tuplas de admin (`"vehiculo"` sin punto)
no coinciden. El check sí recorre todo el registro de admin de la app — y pasó limpio
tras corregir esta clase, confirmando que ninguna otra clase de admin para las otras
4 tablas tiene el mismo problema.

Errores emitidos por manage.py check:
- `admin.E002` — `raw_id_fields[0]` refiere a `"vehiculo"`, no es campo de `taller.PiezaDesarme`
- `admin.E108` — `list_display[2]` refiere a `"vehiculo"`, no es callable ni atributo del modelo

Cambios ya aplicados en `PiezaDesarmeAdmin`:
- Línea 387 (list_display): `"vehiculo"` → `"vehiculo_desarme"`
- Línea 395 (list_select_related): `"vehiculo"` → `"vehiculo_desarme"`
- Línea 396 (raw_id_fields): `"vehiculo"` → `"vehiculo_desarme"`

---

### NO BLOQUEANTES — la app arranca, pero estas features fallan en runtime

Estos archivos se actualizan en el mismo PR/deploy que los modelos (antes del
primer uso en producción del código actualizado), pero no son necesarios para
que `manage.py check` pase.

---

**4. `taller/services/financial_event_service.py`**

- Línea 132: `vehiculo_obj = getattr(pieza, "vehiculo", None)`
  → `vehiculo_obj = getattr(pieza, "vehiculo_desarme", None)`
- Línea 74 y similares: `.filter(vehiculo=vehiculo, ...)` → `.filter(vehiculo_desarme=vehiculo_desarme, ...)`
- Línea 100–101: `VehicleFinancialEvent(vehiculo=vehiculo, ...)` → `VehicleFinancialEvent(vehiculo_desarme=vehiculo_desarme, ...)`
- Los métodos `create_purchase_event`, `create_cost_event`, `create_sale_event`
  reciben un objeto que antes era Vehiculo; ahora debe ser VehiculoDesarme.
  Los call-sites (archivos 6, 7, 9, 12) deben pasar VehiculoDesarme.

**5. `taller/services/snapshot_generator_service.py`**

- Línea 82: `Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)`
  → `VehiculoDesarme.objects.filter(empresa=empresa)`
- Línea 38: `VehicleFinancialEvent.objects.filter(vehiculo=vehiculo, ...)`
  → `.filter(vehiculo_desarme=vehiculo_desarme, ...)`

**6. `taller/services/desarme_financial_service.py`**

- Líneas 33, 88: `PiezaDesarme.objects.filter(vehiculo_id=vehiculo.id)`
  → `.filter(vehiculo_desarme_id=vehiculo_desarme.id)`
- Línea 12: `pieza_desarme__vehiculo_id=vehiculo.id`
  → `pieza_desarme__vehiculo_desarme_id=vehiculo_desarme.id`
- Línea 133: `vehiculo_id=vehiculo.id` (en creación de PrecioHistoricoPieza)
  → `vehiculo_desarme_id=vehiculo_desarme.id`
- Líneas 158, 166, 177: `Vehiculo.objects.filter(empresa=empresa, tipo_uso=DESARME)`
  → `VehiculoDesarme.objects.filter(empresa=empresa)`

**7. `taller/services/desarme_kpi_service.py`**

- Línea 28: `Vehiculo.objects.filter(empresa=empresa, tipo_uso=DESARME, es_placeholder=False)`
  → `VehiculoDesarme.objects.filter(empresa=empresa, es_placeholder=False)`
- Línea 79: `.values("pieza_desarme__vehiculo_id", "pieza_desarme__vehiculo__patente")`
  → `.values("pieza_desarme__vehiculo_desarme_id", "pieza_desarme__vehiculo_desarme__patente")`
- Línea 87: `"vehiculo_id": r.get("pieza_desarme__vehiculo_id")`
  → `"vehiculo_desarme_id": r.get("pieza_desarme__vehiculo_desarme_id")`
- Líneas 116, 118, 127: `pieza_desarme__vehiculo_id=vehiculo.id`, `filter(vehiculo_id=vehiculo.id)`
  → `pieza_desarme__vehiculo_desarme_id=vehiculo_desarme.id`, `filter(vehiculo_desarme_id=...)`
- Línea 195: `Vehiculo.objects.filter(empresa=empresa, tipo_uso=DESARME, es_placeholder=False)`
  → `VehiculoDesarme.objects.filter(empresa=empresa, es_placeholder=False)`

**8. `taller/services/inventory_service.py`**

Bloque completo (líneas 441–451) que actualiza el estado AGOTADO de un VehiculoDesarme
cuando sus piezas se agotan. El bug histórico: `VehiculoDesarme.objects.filter(id=veh_id)`
usaba un `veh_id` obtenido de `pieza.vehiculo_id` (FK a Vehiculo). Antes de Fase 1, la
tabla VehiculoDesarme estaba vacía → el filter devolvía queryset vacío → nunca se marcaba
AGOTADO. Tras Fase 2, `vehiculo_id` desaparece de PiezaDesarme, así que el `getattr` de
línea 441 devolvería `None` y el bloque completo quedaría como no-op.

Las tres líneas a actualizar, en orden:

```python
# ANTES
veh_id = getattr(pieza, "vehiculo_id", None)          # línea 441
...
    remaining = PiezaDesarme.objects.filter(
        vehiculo_id=veh_id,                           # línea 444
        ...
    ).exists()
    if not remaining:
        VehiculoDesarme.objects.filter(id=veh_id).update(estado_desarme="AGOTADO")  # línea 451

# DESPUÉS
veh_id = getattr(pieza, "vehiculo_desarme_id", None)  # línea 441
...
    remaining = PiezaDesarme.objects.filter(
        vehiculo_desarme_id=veh_id,                   # línea 444
        ...
    ).exists()
    if not remaining:
        VehiculoDesarme.objects.filter(id=veh_id).update(estado_desarme="AGOTADO")  # línea 451 — SIN CAMBIO
```

Línea 451 NO cambia: tras la corrección, `veh_id` viene de `vehiculo_desarme_id` que
ya es el PK de VehiculoDesarme → `filter(id=veh_id)` sigue siendo correcto.

**9. `taller/desarme/views.py`**

15+ referencias. Patrón principal:
- `Vehiculo.objects.filter(empresa=empresa, tipo_uso=Vehiculo.TIPO_USO_DESARME)`
  → `VehiculoDesarme.objects.filter(empresa=empresa)`
- `get_object_or_404(Vehiculo, pk=pk, empresa=empresa, tipo_uso=DESARME)`
  → `get_object_or_404(VehiculoDesarme, pk=pk, empresa=empresa)`
- `pieza.vehiculo_id` → `pieza.vehiculo_desarme_id`
- `str(pieza.vehiculo)` → `str(pieza.vehiculo_desarme)`
- `pieza_desarme__vehiculo_id=OuterRef("pk")` → `pieza_desarme__vehiculo_desarme_id=OuterRef("pk")`
- `.values("pieza_desarme__vehiculo_id")` → `.values("pieza_desarme__vehiculo_desarme_id")`
Líneas afectadas: 225, 326, 328, 343, 370, 528, 578, 679, 723, 793, 796, 836,
                  848, 850, 906, 964, 966, 995, 1071, 1138, 1177, 1198, 1549, 1588, 1860

**10. `taller/desarme/forms.py`**

- Líneas 131, 393: `instance.tipo_uso = Vehiculo.TIPO_USO_DESARME` — estas líneas
  asignan `tipo_uso` en un Vehiculo; en Fase 2 el form de alta/edición apuntará a
  VehiculoDesarme directamente y esta asignación desaparece.
- Línea 455: `Vehiculo.objects.filter(empresa=self.empresa, tipo_uso=DESARME)`
  → `VehiculoDesarme.objects.filter(empresa=self.empresa)`

**11. `taller/desarme/services.py`**

- Línea 18: `if vehiculo.tipo_uso != "DESARME": raise ...`
  → ELIMINAR (VehiculoDesarme no tiene campo `tipo_uso`; la validación es redundante
  por diseño: todo VehiculoDesarme ES desarme).
- Línea 55: ídem, eliminar la validación `tipo_uso`.
- Actualizar firmas de funciones que recibían un `Vehiculo` para recibir
  un `VehiculoDesarme`.

**12. `taller/documentos/desarme/views.py`**

- Mismo patrón que #9. Líneas: 43, 65, 100, 133, 163, 216, 219, 253, 265–266, 303–304, 332.
- `pieza.vehiculo_id` → `pieza.vehiculo_desarme_id` (redirects)
- `Vehiculo.objects.filter(tipo_uso=DESARME)` → `VehiculoDesarme.objects.all()`

**13. `taller/documentos/desarme/forms.py`**

- Línea 63: `instance.tipo_uso = Vehiculo.TIPO_USO_DESARME` → eliminar / adaptar a VehiculoDesarme
- Línea 110: `Vehiculo.objects.filter(empresa=self.empresa, tipo_uso=DESARME)`
  → `VehiculoDesarme.objects.filter(empresa=self.empresa)`

**14. `taller/management/commands/rebuild_financial_events.py`**

- Filtros y accesos a `VehicleFinancialEvent.vehiculo` → `vehiculo_desarme`.
- Líneas 37, 47, 78, 155, 163, 171: adaptar queries al nuevo nombre de campo.

---

### Management commands de demo (no bloquean producción, actualizar para coherencia)

**15. `taller/management/commands/seed_desarme_demo.py`**

- Líneas 46, 176: crean `Vehiculo(tipo_uso="DESARME")` → cambiar a `VehiculoDesarme(...)`.

**16. `taller/management/commands/seed_desarme_demo_mauricio.py`**

- Línea 131: ídem.

**17. `taller/management/commands/bootstrap_ve_demo.py`**

- Línea 177: ídem.

---

## on_delete — confirmación para las 5 tablas

| Tabla | on_delete | Justificación |
|---|---|---|
| PiezaDesarme | **PROTECT** | No borrar VehiculoDesarme con piezas activas — la lógica de negocio no cambia |
| SugerenciaPiezaDesarme | CASCADE | Las sugerencias son satélites del vehículo; sin él no tienen sentido |
| PrecioHistoricoPieza | CASCADE | Historial de precios tiene valor solo mientras existe el vehículo |
| VehiculoFinancialSnapshot | CASCADE | El snapshot es de ese vehículo específico; sin él es huérfano |
| VehicleFinancialEvent | CASCADE | El evento financiero es atómico y está ligado a ese vehículo |

Sin cambios en ninguno. El PROTECT de PiezaDesarme es más importante ahora:
impide eliminar un VehiculoDesarme que todavía tiene stock de piezas.

---

## limit_choices_to — confirmación

`limit_choices_to={"tipo_uso": "DESARME"}` en `PiezaDesarme.vehiculo` se elimina
al renombrar el campo. En el nuevo `vehiculo_desarme`, este parámetro **no se
incluye**: apunta a `VehiculoDesarme`, que es siempre desarme por definición.
No hay tipo_uso en VehiculoDesarme — el filtro es estructuralmente imposible
e innecesario.

---

## Verificaciones de campo antes de escribir las migraciones

Todos los campos referenciados en el plan fueron confirmados en el código real
(lectura directa de archivos, no de memoria):

| Campo | Modelo | Archivo | Línea | OK |
|---|---|---|---|---|
| `vehiculo_id` (fuente) | PiezaDesarme | pieza_desarme.py | 65 | ✓ |
| `vehiculo_id` (fuente) | SugerenciaPiezaDesarme | sugerencia_pieza_desarme.py | 22 | ✓ |
| `vehiculo_id` (fuente) | PrecioHistoricoPieza | pieza_desarme.py | 433 | ✓ |
| `vehiculo_id` (fuente) | VehiculoFinancialSnapshot | vehiculo_financial.py | 16 | ✓ |
| `vehiculo_id` (fuente) | VehicleFinancialEvent | vehiculo_financial.py | 94 | ✓ |
| `id` (destino) | VehiculoDesarme | vehiculo_desarme.py | (TenantScoped pk) | ✓ |
| `source_event_count` | VehiculoFinancialSnapshot | vehiculo_financial.py | 34 | ✓ |
| `tipo` (en el índice) | VehicleFinancialEvent | vehiculo_financial.py | 96 | ✓ |
| `sug_pieza_emp_veh_idx` | SugerenciaPiezaDesarme | sugerencia_pieza_desarme.py | 57 | ✓ |
| `sug_pieza_emp_veh_est_idx` | SugerenciaPiezaDesarme | sugerencia_pieza_desarme.py | 58 | ✓ |
| Clase `VehicleFinancialEvent` | — | vehiculo_financial.py | 64 | ✓ (inglés, no español) |

`costo_adquisicion` fue removido de Vehiculo en migración 0098 y NO existe —
esta verificación fue el origen del bug en 0141 (ya corregido). El campo
equivalente en VehiculoDesarme es `precio_compra` (línea 158), copiado en 0141.
No aparece en ningún UPDATE de Fase 2.

---

## Resumen operativo

```
Commit de Fase 2:
  taller/models/pieza_desarme.py            (archivo 1 — bloqueante ✓)
  taller/models/sugerencia_pieza_desarme.py (archivo 2 — bloqueante ✓)
  taller/models/vehiculo_financial.py       (archivo 3 — bloqueante ✓)
  taller/desarme/forms.py                   (archivo 10 → bloqueante 4 ✓)
  taller/documentos/desarme/forms.py        (archivo 13 → bloqueante 5 ✓)
  taller/admin.py                           (sin número — bloqueante 6 ✓)
  taller/migrations/0142_*
  taller/migrations/0143_*
  taller/migrations/0144_*
  taller/migrations/0145_*  ← escrita pero NO aplicada en misma ventana
  taller/services/ (archivos 4–8)
  taller/desarme/views.py + services.py (archivos 9, 11)
  taller/documentos/desarme/views.py (archivo 12)
  taller/management/commands/ (archivos 14–17)

Ventana de mantenimiento:
  1. Aplicar Fase 1 (0137–0141) si aún no está en producción
  2. Aplicar Fase 2 (0142–0143–0144)
  3. Desplegar código actualizado
  4. Verificar en producción

14 días después (mínimo):
  5. Verificar 0 referencias a vehiculo_id en logs de error
  6. Aplicar 0145 (limpieza)
```
