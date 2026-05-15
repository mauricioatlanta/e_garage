# Desarme Fase 3 — Inventario de dependencias y diseño técnico

Documento de revisión: **solo inventario + modelo propuesto + bosquejo de migraciones Fase A/B**. Sin ejecutar cambios destructivos. Sin tocar forms/views/templates aún.

---

## 1. Inventario de dependencias del diseño actual

### 1.1 Búsquedas realizadas

| Término | Archivos afectados |
|---------|--------------------|
| `tipo_uso` | taller/models/vehiculos.py, taller/desarme/forms.py, taller/desarme/views.py, taller/documentos/desarme/forms.py, taller/documentos/desarme/views.py, taller/views_autocomplete.py, taller/autocomplete.py, taller/forms/documento_form.py, taller/documentos/forms.py, taller/models/pieza_desarme.py, taller/tests/test_desarme_fase1.py, taller/migrations/0075_vehiculo_tipo_uso_desarme.py |
| `TIPO_USO_DESARME` | taller/models/vehiculos.py, taller/desarme/forms.py, taller/desarme/views.py, taller/documentos/desarme/forms.py, taller/documentos/desarme/views.py, taller/tests/test_desarme_fase1.py |
| `estado_desarme` | taller/models/vehiculos.py, taller/desarme/views.py, taller/documentos/desarme/views.py, taller/documentos/desarme/forms.py, templates/taller/desarme/*.html |
| `costo_adquisicion` | taller/models/vehiculos.py, taller/documentos/desarme/forms.py, templates/taller/desarme/*.html |
| `fecha_ingreso_desarme` | taller/models/vehiculos.py, taller/desarme/views.py, taller/documentos/desarme/views.py, taller/documentos/desarme/forms.py, templates/taller/desarme/*.html |
| `fecha_baja_desarme` | taller/models/vehiculos.py |
| `ubicacion_fisica` (en Vehiculo) | taller/models/vehiculos.py, taller/documentos/desarme/forms.py, templates/taller/desarme/*.html |
| `observaciones_desarme` | taller/models/vehiculos.py, taller/documentos/desarme/forms.py, templates/taller/desarme/*.html |
| `PiezaDesarme` | taller/models/__init__.py, taller/models/pieza_desarme.py, taller/models/lineas_documento.py, taller/desarme/views.py, taller/desarme/forms.py, taller/documentos/desarme/views.py, taller/documentos/desarme/forms.py, taller/admin.py, taller/services/inventory_service.py, taller/tests/test_desarme_fase1.py |
| `.piezas_desarme` | taller/desarme/views.py, taller/documentos/desarme/views.py |

---

### 1.2 Vistas afectadas

| Archivo | Uso |
|---------|-----|
| `taller/desarme/views.py` | CRUD vehículos desarme (Vehiculo tipo_uso=DESARME), CRUD piezas, inventario por vehículo, filtros por estado_desarme, orden por fecha_ingreso_desarme, accesso a vehiculo.piezas_desarme |
| `taller/documentos/desarme/views.py` | Mismo patrón que desarme/views; variante para módulo documentos |

---

### 1.3 Templates afectados

| Archivo | Uso |
|---------|-----|
| `templates/taller/desarme/lista_vehiculos.html` | Listado; usa `v.estado_desarme`, `v.ubicacion_fisica` |
| `templates/taller/desarme/ver_vehiculo.html` | Detalle; usa `vehiculo.estado_desarme`, `vehiculo.costo_adquisicion`, `vehiculo.fecha_ingreso_desarme`, `vehiculo.ubicacion_fisica`, `vehiculo.observaciones_desarme` |
| `templates/taller/desarme/vehiculo_form.html` | Formulario; decide qué campos mostrar según nombre (incluye patente, vin, marca, modelo, anio, costo_adquisicion, fecha_ingreso_desarme, estado_desarme, ubicacion_fisica, observaciones_desarme) |
| `templates/taller/desarme/pieza_form.html` | Formulario pieza; usa ubicacion_fisica (de PiezaDesarme, no Vehiculo) |
| `templates/taller/desarme/inventario_vehiculo.html` | Inventario de piezas por vehículo |
| `templates/taller/desarme/lista_piezas.html` | Listado de piezas |
| `templates/taller/desarme/unavailable.html` | Fallback cuando desarme no carga |

---

### 1.4 Admin

| Archivo | Uso |
|---------|-----|
| `taller/admin.py` | PiezaDesarmeAdmin: list_display (vehiculo), list_select_related ("vehiculo"), raw_id_fields ("vehiculo"). Depende de PiezaDesarme.vehiculo → Vehiculo. |

---

### 1.5 Forms

| Archivo | Uso |
|---------|-----|
| `taller/desarme/forms.py` | VehiculoDesarmeForm (model=Vehiculo, fuerza tipo_uso=DESARME); PiezaDesarmeForm (queryset vehiculo filtrado por tipo_uso=DESARME) |
| `taller/documentos/desarme/forms.py` | Variante con más campos de desarme (costo_adquisicion, fecha_ingreso_desarme, estado_desarme, ubicacion_fisica, observaciones_desarme); PiezaDesarmeForm similar |

---

### 1.6 Autocomplete y otros helpers

| Archivo | Uso |
|---------|-----|
| `taller/views_autocomplete.py` | VehiculoAutocomplete: filtra `tipo_uso=Vehiculo.TIPO_USO_CLIENTE` (documentos; excluye desarme) |
| `taller/autocomplete.py` | VehiculoAutocomplete legacy: filtra `tipo_uso=Vehiculo.TIPO_USO_CLIENTE` |
| `taller/forms/documento_form.py` | Queryset vehiculo: `tipo_uso=Vehiculo.TIPO_USO_CLIENTE` |
| `taller/documentos/forms.py` | Queryset vehiculo: `tipo_uso=Vehiculo.TIPO_USO_CLIENTE` |

---

### 1.7 Servicios

| Archivo | Uso |
|---------|-----|
| `taller/services/inventory_service.py` | ORIGEN_DESARME: usa PiezaDesarme, pieza_desarme_id, _actualizar_stock_desarme; select_related("pieza_desarme"); LineaRepuesto con pieza_desarme. No depende de Vehiculo tipo_uso; solo de PiezaDesarme. |

---

### 1.8 Modelos

| Archivo | Uso |
|---------|-----|
| `taller/models/vehiculos.py` | Vehiculo: tipo_uso, TIPO_USO_*, campos desarme, validación cliente/tipo_uso en clean() |
| `taller/models/pieza_desarme.py` | PiezaDesarme.vehiculo FK a Vehiculo con limit_choices_to={"tipo_uso":"DESARME"}; clean() valida vehiculo.tipo_uso=="DESARME" |
| `taller/models/lineas_documento.py` | LineaRepuesto.pieza_desarme FK a PiezaDesarme; validaciones origen DESARME |
| `taller/models/documento.py` | Comentario "desarme no aplica aquí" en validación vehiculo.cliente |

---

### 1.9 Tests

| Archivo | Uso |
|---------|-----|
| `taller/tests/test_desarme_fase1.py` | Tests de Vehiculo tipo_uso CLIENTE/DESARME, PiezaDesarme, LineaRepuesto origen DESARME, InventoryService con PiezaDesarme |

---

### 1.10 Señales y comandos de gestión

- **Señales**: No se encontraron referencias a Vehiculo tipo_uso, PiezaDesarme o desarme en signals.
- **Reportes**: No se encontraron referencias a desarme en taller/reportes/.
- **Management commands**: Ningún comando específico de desarme detectado.

---

### 1.11 Dependencias directas e indirectas

**Directas (código que usa Vehiculo con tipo_uso=DESARME o campos de desarme)**:
- taller/desarme/views.py
- taller/desarme/forms.py
- taller/documentos/desarme/views.py
- taller/documentos/desarme/forms.py
- taller/models/pieza_desarme.py (FK + limit_choices_to + clean)
- templates/taller/desarme/*.html

**Indirectas**:
- taller/views_autocomplete.py, taller/autocomplete.py (excluyen DESARME explícitamente)
- taller/forms/documento_form.py, taller/documentos/forms.py (filtran CLIENTE)
- taller/admin.py (PiezaDesarme; vehiculo como FK)
- taller/services/inventory_service.py (usa PiezaDesarme; no Vehiculo directamente)
- taller/models/lineas_documento.py (LineaRepuesto.pieza_desarme → PiezaDesarme)

---

### 1.12 Riesgos especiales

1. **Doble módulo desarme**: Existen `taller/desarme/` y `taller/documentos/desarme/`. Ambos usan Vehiculo tipo_uso=DESARME y PiezaDesarme. Hay que migrar ambos.
2. **urls_desarme**: Carga vistas con try/except; si falla import PiezaDesarme, usa fallback. Tras migrar PiezaDesarme.vehiculo a VehiculoDesarme, el import seguirá funcionando; solo cambia el tipo del FK.
3. **LineaRepuesto.pieza_desarme**: La migración de PiezaDesarme.vehiculo a VehiculoDesarme no afecta LineaRepuesto; sigue apuntando a PiezaDesarme. Riesgo: si algún reporte o serializer recorre pieza_desarme.vehiculo, pasará a obtener VehiculoDesarme (tras Fase C).
4. **InventoryService**: Opera sobre PiezaDesarme; no sobre Vehiculo. Cambio transparente cuando PiezaDesarme.vehiculo pase a VehiculoDesarme.

---

## 2. Diseño técnico del modelo VehiculoDesarme

### 2.1 Base y relaciones

- **Hereda de TenantScoped** (como Vehiculo).
- **No tiene `cliente`** ni lógica de documento/reparación.
- **Campo temporal de migración**: `vehiculo_origen_id`.

### 2.2 Campos propuestos

```python
ESTADO_DESARME_CHOICES = [
    ("INGRESADO", "Ingresado"),
    ("DESARMANDO", "Desarmando"),
    ("DESARMADO", "Desarmado"),
    ("BAJA", "Baja"),
]


class VehiculoDesarme(TenantScoped):
    """
    Vehículo comprado por el taller para desarme.
    Entidad separada de Vehiculo (cliente/reparación).
    """
    # --- Campo temporal de migración (mapeo por ID) ---
    vehiculo_origen_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID del Vehiculo origen (solo para migración; dejar null en registros nuevos).",
    )

    # --- Identificación (espejo de Vehiculo para desarme) ---
    empresa = ...  # heredado de TenantScoped
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)
    marca_texto = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True, blank=True)
    modelo_texto = models.CharField(max_length=150, blank=True, null=True)
    patente = models.CharField(max_length=20, db_index=True, blank=True, default="")  # vacío si solo VIN
    anio = models.PositiveIntegerField(verbose_name="Año", null=True, blank=True)  # no inventar; copiar tal cual
    color = models.ForeignKey(ColorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    vin = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    motor = models.ForeignKey(MotorVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    caja = models.ForeignKey(CajaVehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    millas = models.PositiveIntegerField(blank=True, null=True, verbose_name="Millas/Kilometraje")

    # --- Campos de desarme ---
    costo_adquisicion = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_ingreso_desarme = models.DateField(null=True, blank=True)
    estado_desarme = models.CharField(
        max_length=20,
        choices=ESTADO_DESARME_CHOICES,
        null=True,
        blank=True,
    )
    ubicacion_fisica = models.CharField(max_length=120, null=True, blank=True)
    fecha_baja_desarme = models.DateField(null=True, blank=True)
    observaciones_desarme = models.TextField(blank=True, null=True)
```

### 2.3 Validaciones (clean)

- **Identificación mínima**: `patente` o `vin` (al menos uno no vacío). Si ambos vacíos → warning en migración, pero no bloquear guardado.
- **Empresa coherente** con TenantScoped.
- **Marca/modelo**: reglas por país (CL vs US) equivalentes a Vehiculo; sin cliente.

### 2.4 Meta e índices

Índices conservadores al inicio (evitar redundancia con posibles UniqueConstraint futuros):

```python
class Meta(TenantScoped.Meta):
    ordering = ["-fecha_ingreso_desarme", "-id"]
    verbose_name = "Vehículo de desarme"
    verbose_name_plural = "Vehículos de desarme"
    indexes = [
        models.Index(fields=["empresa"]),
        models.Index(fields=["empresa", "estado_desarme"]),
        models.Index(fields=["vehiculo_origen_id"]),
    ]
```

### 2.5 Restricciones

- **Unicidad en `vehiculo_origen_id`**: NO en 0077 ni 0078. Se agregará en migración posterior (ej. 0079) tras validar Fase B. Debe ser **parcial** para permitir registros nuevos (vehiculo_origen_id=None):

```python
models.UniqueConstraint(
    fields=["vehiculo_origen_id"],
    condition=~models.Q(vehiculo_origen_id__isnull=True),
    name="unique_vehiculo_origen_id_not_null",
)
```
- **UniqueConstraint empresa+patente / empresa+vin**: Opcional; Vehiculo los tiene. Para Fase A se puede omitir y añadir después si hace falta.

---

## 3. Bosquejo de migraciones Fase A y Fase B

### 3.1 Migración de esquema (Fase A)

**Nombre sugerido**: `0077_vehiculodesarme.py`

**Dependencia**: `("taller", "0076_empresa_is_trial_restore")`

**Operaciones**:
- `CreateModel` para `VehiculoDesarme` con todos los campos listados en 2.2 (incluyendo `vehiculo_origen_id`).
- Índices definidos en Meta (sin UniqueConstraint sobre `vehiculo_origen_id` todavía).

**Notas**:
- No se toca `Vehiculo` ni `PiezaDesarme`.
- Tabla resultante: `taller_vehiculodesarme`.

---

### 3.2 Data migration (Fase B)

**Nombre sugerido**: `0078_migrate_vehiculo_desarme_to_vehiculodesarme.py`

**Dependencia**: `("taller", "0077_vehiculodesarme")`

**Reglas explícitas para datos incompletos**:

| Caso | Regla |
|------|-------|
| `patente` y `vin` ambos vacíos | Migrar tal como está; registrar warning; incluir en reporte. |
| `marca`/`modelo` vs `marca_texto`/`modelo_texto` inconsistentes | Copiar ambos tal cual; no intentar reconciliar. |
| Marca/modelo nulos | Permitido; copiar null. |
| Cualquier otro campo nulo | Copiar null; no inventar datos. |

**Pseudocódigo de la migración**:

```python
def forwards(apps, schema_editor):
    Vehiculo = apps.get_model("taller", "Vehiculo")
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")
    qs = Vehiculo.objects.filter(tipo_uso="DESARME")
    total_leidos = qs.count()
    total_creados = 0
    total_existentes = 0
    total_warnings = 0
    ids_warnings = []

    for v in qs.iterator():
        # Idempotencia: si ya existe por vehiculo_origen_id, saltar
        if VehiculoDesarme.objects.filter(vehiculo_origen_id=v.id).exists():
            total_existentes += 1
            continue

        warning = False
        patente_ok = v.patente and str(v.patente).strip()
        vin_ok = v.vin and str(v.vin).strip()
        if not (patente_ok or vin_ok):
            warning = True
            total_warnings += 1
            ids_warnings.append(v.id)

        vd = VehiculoDesarme(
            empresa_id=v.empresa_id,
            vehiculo_origen_id=v.id,
            marca_id=v.marca_id,
            marca_texto=v.marca_texto,
            modelo_id=v.modelo_id,
            modelo_texto=v.modelo_texto,
            patente=v.patente or "",
            anio=v.anio,  # no inventar; null si es null en origen
            color_id=v.color_id,
            vin=v.vin,
            motor_id=v.motor_id,
            caja_id=v.caja_id,
            millas=v.millas,
            costo_adquisicion=v.costo_adquisicion,
            fecha_ingreso_desarme=v.fecha_ingreso_desarme,
            estado_desarme=v.estado_desarme,
            ubicacion_fisica=v.ubicacion_fisica,
            fecha_baja_desarme=v.fecha_baja_desarme,
            observaciones_desarme=v.observaciones_desarme,
        )
        vd.save()
        total_creados += 1

    # Log/resumen auditable (salida por consola o logger)
    # - total_leidos, total_creados, total_existentes, total_warnings, ids_warnings
```

**Logging/Reporte**:
- Usar `logging` (no `print`). Ejemplo:

```python
import logging
logger = logging.getLogger(__name__)
logger.info(
    "Desarme migration: leidos=%s creados=%s existentes=%s warnings=%s ids_warnings=%s",
    total_leidos, total_creados, total_existentes, total_warnings, ids_warnings[:50]
)
```

**UniqueConstraint sobre `vehiculo_origen_id`**:
- **No** en 0078. Se añadirá en migración **posterior** (0079 o similar) tras validar Fase B. Debe ser parcial (`condition=~Q(vehiculo_origen_id__isnull=True)`).

---

### 3.3 Checklist de validación Fase B (recordatorio)

- [ ] `#Vehiculo(tipo_uso=DESARME)` == `#VehiculoDesarme`
- [ ] Ningún VehiculoDesarme sin empresa
- [ ] Todos los `vehiculo_origen_id` no nulos
- [ ] Todos los `vehiculo_origen_id` distintos
- [ ] Revisión de nulos críticos según reglas actuales
- [ ] Muestreo manual de varios casos reales

---

## 4. Archivos a crear/modificar (resumen)

**En esta fase (solo A y B)**:

| Acción | Archivo |
|--------|---------|
| Crear | `taller/models/vehiculo_desarme.py` (modelo VehiculoDesarme) |
| Modificar | `taller/models/__init__.py` (añadir import y export de VehiculoDesarme) |
| Crear | `taller/migrations/0077_vehiculodesarme.py` (CreateModel) |
| Crear | `taller/migrations/0078_migrate_vehiculo_desarme_to_vehiculodesarme.py` (RunPython data migration) |

**No se toca** (hasta Fase C/D/E):

- forms, views, templates
- PiezaDesarme
- Vehiculo (campos, clean, tipo_uso)

---

### Preflight antes de migrate

Ejecutar en entorno controlado para validar datos reales:

```bash
python manage.py shell
```

```python
from taller.models import Vehiculo

# 1. Constante tipo_uso
print("TIPO_USO_DESARME =", repr(Vehiculo.TIPO_USO_DESARME))  # debe ser "DESARME"

# 2. Conteo
count = Vehiculo.objects.filter(tipo_uso="DESARME").count()
print("Vehiculo DESARME count:", count)

# 3. Valores distintos de estado_desarme (crítico: si hay fuera de choices, decidir mapeo)
estados = list(Vehiculo.objects.filter(tipo_uso="DESARME").values_list("estado_desarme", flat=True).distinct())
print("estado_desarme distintos:", estados)
# Choices esperados: INGRESADO, DESARMANDO, DESARMADO, BAJA
# Valores fuera de catálogo se copiarán igual (CharField no valida choices en save).

# 4. Muestreo anio (verificar que son int, no basura)
from django.db.models import Count
anios_ok = Vehiculo.objects.filter(tipo_uso="DESARME").exclude(anio__isnull=True).count()
anios_null = Vehiculo.objects.filter(tipo_uso="DESARME", anio__isnull=True).count()
print("anio: con valor =", anios_ok, ", null =", anios_null)
```

### Orden de ejecución recomendado

1. **Preflight**: ejecutar el bloque anterior y revisar conteo y estados.
2. Actualizar documento con ajustes.
3. Crear modelo + 0077 + 0078.
4. Revisar antes de ejecutar `migrate`.
5. Tras validar Fase B: migración 0079 para UniqueConstraint parcial sobre `vehiculo_origen_id`.

---

*Documento actualizado. Listo para generar código: `vehiculo_desarme.py`, 0077, 0078.*
