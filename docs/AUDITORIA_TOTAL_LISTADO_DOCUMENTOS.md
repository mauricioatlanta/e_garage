# Auditoría: Total $0.00 en listado de documentos

## 1) Campo exacto que se imprime en el listado

**Template:** `templates/taller/common/documentos/lista_documentos.html`

- **Vista previa (cards):** líneas 1117-1126  
  - Condición: `{% if documento.total and documento.total > 0 %}`  
  - Valor mostrado: `{{ documento.total|money_by_country:country }}`  
  - Fallback si 0: `$0` (CL) o `$0.00` (otros)

- **Vista tabla:** línea 1245  
  - `{{ documento.total|money_by_country:country|default:"$0" }}`

**Conclusión:** El campo que puede mostrar $0.00 es **`documento.total`**. Si ese atributo no se rellena en la vista (o viene 0 de BD), el template muestra $0.00.

---

## 2) Por qué el total puede ser 0

- El modelo `Documento` tiene el campo **`total`** (DecimalField, default 0.00).
- Si nunca se llama a `recompute_totals(persist=True)` tras guardar líneas, o si las anotaciones del listado fallan, `documento.total` queda en 0.
- En las líneas, **`subtotal` es una propiedad Python** (`@property`), no un campo en BD, por tanto **no** se puede usar en el ORM como `Sum("lineas_repuesto__subtotal")`. Las anotaciones deben usar `ExpressionWrapper(F("cantidad") * F("precio_unitario"))` (o equivalente por tipo de línea).
- Varios `Sum()` sobre distintas relaciones en el mismo `annotate()` pueden generar producto cartesiano en el JOIN y dar totales incorrectos (o 0 según el caso).

---

## 3) Fix aplicado (total “real” desde líneas)

**Vista:** `taller/documentos/views_migrated.py` — `DocumentoListView.get_context_data()`

1. **Cálculo principal:** Se usa el total que ya viene de las anotaciones del queryset (`total_display`, `legacy_total_general` o suma de `rep_sum` + `serv_sum` + `otros_sum` + `iva_calc`).
2. **Fallback:** Si `documento.total` sigue siendo `None` o ≤ 0, se llama a **`_total_from_documento_lines(documento)`**, que:
   - Suma desde las líneas ya cargadas (prefetch): repuestos (`cantidad * precio_unitario`), servicios (`cantidad * precio_unitario`), otros (`cantidad * precio_cliente`).
   - Aplica IVA solo sobre repuestos para país CL (19%).
   - Asigna `documento.total` y, si aplica, `documento.neto_repuestos`, `neto_servicios`, `neto_otros_servicios`.

Así, aunque el campo guardado esté en 0 o las anotaciones fallen, el listado muestra el total calculado desde las líneas.

---

## 4) Numeración automática por tipo (por empresa)

Ya está implementada:

- **Modelo:** `Documento.numero` (CharField). En `save()`: si `not self.numero` se llama a `generar_numero_documento()`.
- **Secuencia:** `taller.models.sequence.DocumentSequence` — `next(empresa, tipo)` con `select_for_update()` en transacción para evitar duplicados.
- **Prefijos:** Dependen de país y de `context` (WORKSHOP / PARTS / MIXED), por ejemplo US: WO (OT), E (PRES), I (FAC).

No es necesario un “correlativo por tipo” adicional si el flujo de creación deja `numero` vacío para que lo asigne `save()`.

---

## 5) Color de template por tipo de documento

En el listado ya existe **`data-tipo="{{ documento.tipo }}"`** en cada card (ej. `FAC`, `PRES`, `OT`).

Se añadió CSS en el mismo template:

- `.documento-card[data-tipo="FAC"]` → `--doc-accent: #00ffff`
- `.documento-card[data-tipo="PRES"]` → `--doc-accent: #ffd700`
- `.documento-card[data-tipo="OT"]` → `--doc-accent: #00ff88`

Se usa `var(--doc-accent)` en el bloque del total (color y sombra) para diferenciar visualmente el tipo de documento.

---

## Comandos útiles (servidor)

```bash
# Ver totales reales desde líneas vs campo guardado
./scripts/manage_prod.sh shell -c "
from decimal import Decimal
from taller.models import Documento
for d in Documento.objects.select_related('empresa').prefetch_related('lineas_repuesto','lineas_servicio','lineas_otro_servicio')[:5]:
    rep = sum(Decimal(str(l.cantidad or 0)) * Decimal(str(l.precio_unitario or 0)) for l in d.lineas_repuesto.all())
    srv = sum(Decimal(str(l.cantidad or 0)) * Decimal(str(l.precio_unitario or 0)) for l in d.lineas_servicio.all())
    otros = sum(Decimal(str(l.cantidad or 0)) * Decimal(str(l.precio_cliente or 0)) for l in d.lineas_otro_servicio.all())
    iva = (rep * Decimal('0.19')).quantize(Decimal('0.01')) if getattr(d.empresa,'pais',None) == 'CL' else Decimal('0')
    calc = rep + srv + otros + iva
    print(d.id, d.tipo, 'campo total=', d.total, 'calculado=', calc)
"
```

Si quieres **persistir** totales correctos en BD para todos los documentos existentes:

```bash
./scripts/manage_prod.sh shell -c "
from taller.models import Documento
updated = Documento.recalcular_totales_bulk(list(Documento.objects.values_list('id', flat=True)[:500]))
print('Recalculados:', updated)
"
```
