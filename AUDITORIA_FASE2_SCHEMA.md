# AUDITORÍA FASE 2 — Schema exacto (verbatim)

Extraído de: `taller/models/pieza_desarme.py` y `taller/models/vehiculo_financial.py`
Fecha: 2026-06-24

---

## 1. PrecioHistoricoPieza — clase Meta completa

Fuente: `taller/models/pieza_desarme.py:459–467`

```python
    class Meta:
        verbose_name = "Precio histórico pieza"
        verbose_name_plural = "Precios históricos pieza"
        ordering = ["-fecha"]
        indexes = [
            Index(fields=["empresa", "fecha"]),
            Index(fields=["empresa", "tipo_evento"]),
            Index(fields=["pieza_desarme", "fecha"]),
        ]
```

**Conclusión:** NO hay `constraints = [...]` en esta clase Meta.
No existe ningún UniqueConstraint ni ningún índice que involucre `vehiculo_id`.
El único índice compuesto sobre `vehiculo_id` sería el FK implícito de Django.

---

## 2. PiezaDesarme — clase Meta completa

Fuente: `taller/models/pieza_desarme.py:292–305`

```python
    class Meta(TenantScoped.Meta):
        verbose_name = "Pieza de desarme"
        verbose_name_plural = "Piezas de desarme"
        indexes = [
            Index(fields=["empresa", "vehiculo"]),
            Index(fields=["empresa", "codigo"]),
            Index(fields=["empresa", "estado_pieza"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "vehiculo", "codigo"],
                name="unique_codigo_por_empresa_vehiculo",
            )
        ]
```

---

## 3. SugerenciaPiezaDesarme — FK vehiculo + clase Meta completa

### FK vehiculo (fuente: `taller/models/sugerencia_pieza_desarme.py:22–26`)

```python
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.CASCADE,
        related_name="sugerencias_piezas",
    )
```

### clase Meta completa (fuente: `taller/models/sugerencia_pieza_desarme.py:47–59`)

```python
    class Meta(TenantScoped.Meta):
        verbose_name = "Sugerencia pieza desarme"
        verbose_name_plural = "Sugerencias piezas desarme"
        constraints = [
            models.UniqueConstraint(
                fields=["vehiculo", "codigo"],
                name="unique_sugerencia_por_vehiculo",
            )
        ]
        indexes = [
            models.Index(fields=["empresa", "vehiculo"],           name="sug_pieza_emp_veh_idx"),
            models.Index(fields=["empresa", "vehiculo", "estado"], name="sug_pieza_emp_veh_est_idx"),
        ]
```

---

## 4. VehiculoFinancialSnapshot — FK vehiculo + clase Meta completa

### FK vehiculo (fuente: `taller/models/vehiculo_financial.py:16`)

```python
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="financial_snapshots")
```

### clase Meta completa (fuente: `taller/models/vehiculo_financial.py:46–61`)

```python
    class Meta:
        verbose_name = "Vehiculo Financial Snapshot"
        verbose_name_plural = "Vehiculo Financial Snapshots"

        constraints = [
            models.UniqueConstraint(
                fields=["snapshot_hash"],
                name="unique_vehicle_snapshot_hash",
            )
        ]

        indexes = [
            models.Index(fields=["vehiculo", "fecha"]),
            models.Index(fields=["vehiculo", "source_event_count"]),
            models.Index(fields=["snapshot_hash"]),
        ]
```

---

## 5. Nombre exacto de la clase + FK vehiculo + clase Meta completa

Fuente: `taller/models/vehiculo_financial.py:64–154`

### Nombre de la clase (línea 64)

```python
class VehicleFinancialEvent(models.Model):
```

El nombre es **`VehicleFinancialEvent`** (inglés: "Vehicle", no "Vehiculo").
La forma "VehiculoFinancialEvent" que aparecía en respuestas anteriores era un error de transcripción — en el código solo existe `VehicleFinancialEvent`.

### FK vehiculo (línea 94)

```python
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="financial_events")
```

### clase Meta completa (líneas 139–154)

```python
    class Meta:
        verbose_name = "Vehicle Financial Event"
        verbose_name_plural = "Vehicle Financial Events"
        constraints = [
            models.UniqueConstraint(
                fields=["event_hash"],
                condition=Q(event_hash__isnull=False),
                name="uniq_vehicle_financial_event_hash",
            )
        ]
        indexes = [
            models.Index(fields=["vehiculo", "tipo", "fecha"]),
            models.Index(fields=["linea_repuesto"]),
            models.Index(fields=["event_hash"]),
            models.Index(fields=["event_type"]),
        ]
```

---

## Tabla resumen de constraints que involucran vehiculo_id

| Tabla | Constraint | Tipo | Columnas exactas | Nombre |
|---|---|---|---|---|
| `taller_piezadesarme` | UniqueConstraint | UNIQUE | `(empresa_id, vehiculo_id, codigo)` | `unique_codigo_por_empresa_vehiculo` |
| `taller_piezadesarme` | Index | INDEX | `(empresa_id, vehiculo_id)` | (auto) |
| `taller_sugerenciapiezadesarme` | UniqueConstraint | UNIQUE | `(vehiculo_id, codigo)` | `unique_sugerencia_por_vehiculo` |
| `taller_sugerenciapiezadesarme` | Index | INDEX | `(empresa_id, vehiculo_id)` | `sug_pieza_emp_veh_idx` |
| `taller_sugerenciapiezadesarme` | Index | INDEX | `(empresa_id, vehiculo_id, estado)` | `sug_pieza_emp_veh_est_idx` |
| `taller_preciohistoricopieza` | — | — | — | ninguno sobre vehiculo_id |
| `taller_vehiculofinancialsnapshot` | Index | INDEX | `(vehiculo_id, fecha)` | (auto) |
| `taller_vehiculofinancialsnapshot` | Index | INDEX | `(vehiculo_id, source_event_count)` | (auto) |
| `taller_vehiclefinancialevent` | Index | INDEX | `(vehiculo_id, tipo, fecha)` | (auto) |
