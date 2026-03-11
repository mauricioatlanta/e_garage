# Fase 1 – Cierre funcional módulo desarmaduría – Entregables

Implementación de los huecos detectados en la auditoría, sin rehacer arquitectura ni romper el flujo de vehículos de cliente.

---

## A. Resumen de cambios

1. **Formulario de vehículo para desarme**
   - Se añadieron al `VehiculoForm` los campos de desarmaduría: `fecha_ingreso_desarme`, `proveedor_nombre`, `proveedor_rut`, `proveedor_telefono`, `precio_compra`, `costo_transporte`, `costo_grua`, `costo_papeles`, `otros_costos_base`, `observaciones_desarme`.
   - Validación en `clean()`: si `tipo_uso == "desarme"` se exige `fecha_ingreso_desarme`.
   - En el template del formulario se añadió una sección “Datos de desarmaduría” que se muestra/oculta con JS según el valor de “Tipo de vehículo” (visible solo cuando se elige “Vehículo para desarme”).

2. **Filtro de repuestos por vehículo origen**
   - En `RepuestoListView.get_queryset()` se aplica filtro por `vehiculo_origen_id` cuando existe el parámetro GET `vehiculo_origen`, siempre que el valor sea un PK válido y el vehículo pertenezca a la empresa del usuario.
   - Se expone `vehiculo_origen_filter` en el contexto para el template.
   - En la lista de repuestos se muestra un aviso cuando hay filtro activo (“Filtrado por vehículo: …”) y un enlace “Ver todos”.

3. **Navegación principal**
   - En `templates/taller/common/base.html` se añadió el enlace “Desarme” / “Disassembly” en el menú principal, que apunta a `desarme:plantilla_list` (listado de plantillas de desarme como puerta de entrada al módulo).

---

## B. Archivos modificados

| # | Archivo |
|---|--------|
| 1 | `taller/vehiculos/forms.py` |
| 2 | `templates/taller/common/vehiculos/vehiculo_form.html` |
| 3 | `taller/repuestos/views_cbv.py` |
| 4 | `templates/taller/common/repuestos/repuesto_list.html` |
| 5 | `templates/taller/common/base.html` |

---

## C. Código completo de cada archivo modificado

Solo se incluyen los fragmentos relevantes (no el archivo completo donde es muy largo).

### 1. `taller/vehiculos/forms.py`

**Meta.fields** — se añadieron los campos de desarme:

```python
fields = [
    "tipo_uso",
    "cliente",
    "anio",
    "marca",
    "modelo",
    "patente",
    "vin",
    "color",
    "motor",
    "caja",
    "fecha_ingreso_desarme",
    "proveedor_nombre",
    "proveedor_rut",
    "proveedor_telefono",
    "precio_compra",
    "costo_transporte",
    "costo_grua",
    "costo_papeles",
    "otros_costos_base",
    "observaciones_desarme",
]
```

**Meta.widgets** — se añadieron widgets para los nuevos campos (fecha, texto, numéricos y textarea) con la misma clase CSS que el resto del formulario.

**clean()** — antes del `return cleaned_data` final:

```python
# Desarme: fecha de ingreso obligatoria cuando tipo_uso es desarme
tipo_uso = (cleaned_data.get("tipo_uso") or "").strip() or "cliente"
if tipo_uso == "desarme" and not cleaned_data.get("fecha_ingreso_desarme"):
    self.add_error(
        "fecha_ingreso_desarme",
        "Para vehículos de desarme debe indicar la fecha de ingreso.",
    )
```

---

### 2. `templates/taller/common/vehiculos/vehiculo_form.html`

Después del bloque de `tipo_uso` y antes del grid principal se añadió:

- Un bloque `{% if form.fecha_ingreso_desarme %}` con la sección “Datos de desarmaduría” que incluye todos los campos nuevos (fecha de ingreso, proveedor, costos, observaciones).
- Un script que muestra/oculta esa sección según el valor del `<select name="tipo_uso">` (visible solo cuando el valor es `desarme`).

(Véase el archivo en el proyecto para el HTML/JS exacto.)

---

### 3. `taller/repuestos/views_cbv.py`

**get_queryset()** — después del filtro por `q` y antes de `order_by`:

```python
vo = (self.request.GET.get("vehiculo_origen") or "").strip()
self.vehiculo_origen_filter = None
if vo:
    try:
        pk = int(vo)
        from taller.models import Vehiculo

        empresa = getattr(self.request.user, "empresa", None)
        if empresa:
            vehiculo = Vehiculo.objects.filter(pk=pk, empresa=empresa).first()
            if vehiculo:
                qs = qs.filter(vehiculo_origen_id=pk)
                self.vehiculo_origen_filter = vehiculo
    except (ValueError, TypeError):
        pass
```

**get_context_data()** — antes del `return context`:

```python
context["vehiculo_origen_filter"] = getattr(self, "vehiculo_origen_filter", None)
```

---

### 4. `templates/taller/common/repuestos/repuesto_list.html`

Al inicio de `{% block page_stats %}`, antes del grid de estadísticas:

```django
{% if vehiculo_origen_filter %}
<div class="mb-3 p-3 rounded-lg bg-amber-900/30 border border-amber-500/40 text-sm">
  <span class="text-amber-200">{% if ... %}Filtered by vehicle:{% else %}Filtrado por vehículo:{% endif %}</span>
  <strong class="text-white">{{ vehiculo_origen_filter.get_marca_display }} ...</strong>
  <a href="{% country_url 'repuestos:lista_repuestos' %}" ...>Ver todos / Show all</a>
</div>
{% endif %}
```

---

### 5. `templates/taller/common/base.html`

Entre el enlace “Repuestos” y “Reportes”:

```django
<a href="{% country_url 'desarme:plantilla_list' %}" class="nav-button-standard">
  <span class="nav-icon">🔩</span>
  <span>{% if ... %}Disassembly{% else %}Desarme{% endif %}</span>
</a>
```

---

## D. Notas de compatibilidad y validación

- **Multi-tenant:** Los nuevos campos del formulario no alteran la lógica de empresa; `Vehiculo` sigue asignando `empresa` en la vista al guardar. El filtro de repuestos solo aplica cuando el vehículo pertenece a la empresa del usuario.
- **Vehículos de cliente:** Si `tipo_uso != "desarme"`, los campos de desarme no son obligatorios y la sección se oculta en el front; el modelo ya limpia `estado_desarme` cuando no es desarme.
- **Repuestos:** Si `vehiculo_origen` no es un entero o el vehículo no es de la empresa, el parámetro se ignora y la lista muestra todos los repuestos de la empresa (comportamiento seguro).
- **Navegación:** `country_url` con `desarme:plantilla_list` y `app_namespace='taller'` (por defecto) resuelve a la URL correcta por país (ej. `chile:taller:desarme:plantilla_list`).
- **Template formulario:** La sección de desarme solo se renderiza si el form tiene el campo `fecha_ingreso_desarme`, para no romper otras vistas que usen un form distinto.

---

## E. Observaciones adicionales (sin ampliar alcance)

- **Lista de vehículos:** Sigue siendo única (clientes + desarme). En la tarjeta de un vehículo con `tipo_uso == 'desarme'` ya existía el botón “Desarme” al mapa; no se modificó.
- **Estados desarme:** No se añadió selector de `estado_desarme` en el formulario; el modelo puede inicializarlo o dejarlo vacío; el flujo actual (ingreso → mapa → cierre) no lo exige en el alta.
- **Costos adicionales (CostoVehiculoDesarme):** Siguen sin CRUD en el panel; solo se listan en el dashboard; la Fase 1 no los incluye.

Flujo validado conceptualmente: crear vehículo tipo desarme con fecha de ingreso → guardar → lista de vehículos → “Desarme” al mapa → aplicar plantilla → “Piezas” con `?vehiculo_origen=<pk>` (lista filtrada) → dashboard financiero → cerrar vehículo. Todos los eslabones quedan cubiertos por los cambios de esta fase.
