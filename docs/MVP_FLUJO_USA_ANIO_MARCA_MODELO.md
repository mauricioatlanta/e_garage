# MVP Flujo USA: Año → Marca → Modelo (CatalogoModeloAuto)

**Objetivo:** Implementar flujo año → marca → modelo usando la fuente canónica `CatalogoModeloAuto` con rangos de año.

---

## A) Archivos exactos a modificar

| Archivo | Cambio |
|---------|--------|
| `taller/models/catalogo.py` | Añadir `anio_desde`, `anio_hasta`; ajustar `unique_together`; nuevos métodos |
| `taller/migrations/0089_catalogo_anio_desde_hasta.py` | Nueva migración |
| `taller/vehiculos/views_fbv.py` | Nuevos endpoints `api_marcas_por_anio`, `api_modelos_por_marca_anio_usa` |
| `taller/vehiculos/urls.py` | Registrar rutas |
| `taller/vehiculos/forms.py` | Ajustar `_configurar_campos_usa` para flujo año→marca→modelo + fallback manual |
| `templates/us/en/vehiculos/crear_vehiculo.html` | Orden año→marca→modelo; `#vehiculos-endpoints`; JS |
| `templates/us/es/vehiculos/crear_vehiculo.html` | Idem US EN |
| `taller/management/commands/import_modelos_usa.py` | CSV con `anio_desde`, `anio_hasta` |
| `taller/views_fbv.py` (crear_vehiculo ctx) | Añadir `url_api_marcas_por_anio`, `url_api_modelos_por_marca_anio_usa` |

---

## B) Cambios exactos por archivo

### 1. `taller/models/catalogo.py`

```python
# Añadir después de la línea 22 (después de modelo = ...):
    anio_desde = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Año inicial del rango (ej: 2020 para Camry 2020-2024)"
    )
    anio_hasta = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Año final del rango (ej: 2024). Si null, rango abierto."
    )

# Cambiar Meta.unique_together (línea 29):
    unique_together = (("marca", "modelo", "anio_desde", "anio_hasta"),)
# O si se permite duplicados por rango, usar:
#    unique_together = (("marca", "modelo"),)  # Mantener y permitir múltiples rangos

# Añadir índices en Meta.indexes:
    models.Index(fields=["anio_desde", "anio_hasta"], name="idx_catalogo_anio"),

# Nuevos métodos de clase (después de get_modelos_por_marca):
    @classmethod
    def get_marcas_por_anio(cls, anio):
        """Marcas únicas con al menos un modelo activo en el año dado."""
        from django.db.models import Q
        qs = cls.objects.filter(activo=True)
        qs = qs.filter(
            Q(anio_desde__lte=anio) | Q(anio_desde__isnull=True)
        ).filter(
            Q(anio_hasta__gte=anio) | Q(anio_hasta__isnull=True)
        )
        return qs.values_list("marca", flat=True).distinct().order_by("marca")

    @classmethod
    def get_modelos_por_marca_anio(cls, marca, anio):
        """Modelos para marca y año, filtrados por rango."""
        from django.db.models import Q
        qs = cls.objects.filter(marca__iexact=marca, activo=True)
        qs = qs.filter(
            Q(anio_desde__lte=anio) | Q(anio_desde__isnull=True)
        ).filter(
            Q(anio_hasta__gte=anio) | Q(anio_hasta__isnull=True)
        )
        return qs.values_list("modelo", flat=True).distinct().order_by("modelo")
```

**Nota unique_together:** Si un mismo par (marca, modelo) puede tener varios rangos (ej. Camry 2018-2020 y Camry 2021-2024), usar `unique_together = (("marca", "modelo", "anio_desde", "anio_hasta"),)`. Si cada par es único y el rango se actualiza, mantener `(("marca", "modelo"),)`.

---

### 2. Migración

```bash
python manage.py makemigrations taller --name catalogo_anio_desde_hasta
```

Migración con `default=None` para `anio_desde`/`anio_hasta` (null=True). Datos existentes quedarán con null (equivalentes a "todos los años"); opcional: data migration para backfill 1970-actual.

---

### 3. `taller/vehiculos/views_fbv.py`

Añadir vistas (después de `api_modelos_usa`):

```python
@require_GET
@login_required
def api_marcas_por_anio(request):
    """Marcas USA por año desde CatalogoModeloAuto."""
    if _get_country(request) != "US":
        return JsonResponse([], safe=False)
    anio_str = request.GET.get("anio", "").strip()
    if not anio_str:
        return JsonResponse([], safe=False)
    try:
        anio = int(anio_str)
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)
    try:
        if CatalogoModeloAuto and hasattr(CatalogoModeloAuto, "get_marcas_por_anio"):
            marcas = list(CatalogoModeloAuto.get_marcas_por_anio(anio))[:200]
        else:
            marcas = list(CatalogoModeloAuto.get_marcas_activas())[:200]  # Fallback sin año
        data = [{"id": m, "nombre": m} for m in marcas]
        return JsonResponse(data, safe=False)
    except Exception as e:
        log.error(f"Error en api_marcas_por_anio: {e}")
        return JsonResponse([], safe=False)


@require_GET
@login_required
def api_modelos_por_marca_anio_usa(request):
    """Modelos USA por marca y año desde CatalogoModeloAuto."""
    if _get_country(request) != "US":
        return JsonResponse([], safe=False)
    marca = request.GET.get("marca", "").strip()
    anio_str = request.GET.get("anio", "").strip()
    if not marca:
        return JsonResponse([], safe=False)
    anio = None
    if anio_str:
        try:
            anio = int(anio_str)
        except (ValueError, TypeError):
            pass
    try:
        if CatalogoModeloAuto and hasattr(CatalogoModeloAuto, "get_modelos_por_marca_anio") and anio:
            modelos = list(CatalogoModeloAuto.get_modelos_por_marca_anio(marca, anio))[:200]
        else:
            modelos = list(CatalogoModeloAuto.get_modelos_por_marca(marca))[:200]  # Fallback sin año
        data = [{"id": m, "nombre": m} for m in modelos]
        return JsonResponse(data, safe=False)
    except Exception as e:
        log.error(f"Error en api_modelos_por_marca_anio_usa: {e}")
        return JsonResponse([], safe=False)
```

En `crear_vehiculo`, dentro del bloque `if country == "US"`:

```python
ctx["url_api_marcas_por_anio"] = reverse(f"{ns}:vehiculos:api_marcas_por_anio")
ctx["url_api_modelos_por_marca_anio_usa"] = reverse(f"{ns}:vehiculos:api_modelos_por_marca_anio_usa")
```

---

### 4. `taller/vehiculos/urls.py`

Añadir en urlpatterns:

```python
path("api/marcas-por-anio/", views.api_marcas_por_anio, name="api_marcas_por_anio"),
path("api/modelos-por-marca-anio-usa/", views.api_modelos_por_marca_anio_usa, name="api_modelos_por_marca_anio_usa"),
```

---

### 5. `taller/vehiculos/forms.py` — Solo USA

En `_configurar_campos_usa`:

- **Marca:** En lugar de pre-rellenar con `get_marcas_activas()`, usar choices iniciales vacías o placeholder:
  ```python
  marcas_choices = [("", "Select year first")]  # Se rellenará por JS
  self.fields["marca"] = forms.ChoiceField(
      choices=marcas_choices,
      required=True,
      label="Brand",
      widget=forms.Select(attrs={...}),
  )
  ```
- **Modelo:** Mantener `choices=[("", "Select brand first")]` (ya existe).
- **Attr para deshabilitar hasta tener año:** Añadir `attrs={"disabled": True}` o `data-requires-year="1"` al widget de marca; el JS quitará disabled al seleccionar año.
- **Fallback manual:** Si el usuario elige "Other / Manual", mostrar input de texto para marca y modelo. Reutilizar patrón de US ES: `marca-nuevo-container`, `modelo-nuevo-container` con inputs `marca_nuevo`, `modelo_nuevo` (o `nuevo_marca`, `nuevo_modelo`).

**Lógica de fallback manual:** Añadir opción `("__manual__", "Other / Enter manually")` al final del select de marca (cuando hay resultados) y de modelo. Al elegirla, mostrar inputs de texto. En `clean_marca`/`clean_modelo`, si valor es `__manual__`, leer de `nuevo_marca`/`nuevo_modelo` (o `marca_manual`/`modelo_manual`).

---

### 6. `templates/us/en/vehiculos/crear_vehiculo.html`

- **Orden de campos:** Mover `anio` antes de `marca` y `modelo` (ya está cerca; asegurar: Year → Brand → Model).
- **#vehiculos-endpoints:** Añadir:
  ```html
  data-ep-marcas-por-anio="{% if url_api_marcas_por_anio %}{{ url_api_marcas_por_anio }}{% else %}{% url 'us_en:vehiculos:api_marcas_por_anio' %}{% endif %}"
  data-ep-modelos-por-marca-anio-usa="{% if url_api_modelos_por_marca_anio_usa %}{{ url_api_modelos_por_marca_anio_usa }}{% else %}{% url 'us_en:vehiculos:api_modelos_por_marca_anio_usa' %}{% endif %}"
  ```
- **JS:**
  1. Listener en `id_anio` → llamar `cargarMarcasPorAnio(anio)`.
  2. Nueva función `cargarMarcasPorAnio(anio)` que haga fetch a `url_api_marcas_por_anio?anio=X` y rellene `#id_marca`.
  3. Modificar `cargarModelos` para que use `api_modelos_por_marca_anio_usa` con `marca` + `anio` cuando corresponda.
  4. Si marcas o modelos vienen vacíos, mostrar opción "Other / Enter manually" y contenedores de input manual.
- **Inicial:** Marca deshabilitada hasta que haya año; modelo deshabilitado hasta que haya marca.

---

### 7. `templates/us/es/vehiculos/crear_vehiculo.html`

Aplicar la misma lógica que en US EN, con textos en español ("Selecciona año primero", "Otra / Ingresar manualmente", etc.). Ya tiene `btn-add-marca`, `btn-add-modelo` y contenedores `marca-nuevo-container`, `modelo-nuevo-container`; adaptar para el flujo año→marca→modelo y para el fallback manual cuando no hay resultados.

---

### 8. `taller/management/commands/import_modelos_usa.py`

- **CSV:** Columnas `Marca`, `Modelo`, `anio_desde`, `anio_hasta` (o `Anio_Desde`, `Anio_Hasta`).
- **Lectura:**
  ```python
  anio_desde = (record.get("anio_desde") or record.get("Anio_Desde") or "").strip()
  anio_hasta = (record.get("anio_hasta") or record.get("Anio_Hasta") or "").strip()
  ad = int(anio_desde) if anio_desde.isdigit() else None
  ah = int(anio_hasta) if anio_hasta.isdigit() else None
  rows.append(CatalogoModeloAuto(marca=marca, modelo=modelo, anio_desde=ad, anio_hasta=ah))
  ```
- **Retrocompatibilidad:** Si el CSV no trae columnas de año, usar `anio_desde=None`, `anio_hasta=None` (equivalente a todos los años).

---

## C) Riesgos de compatibilidad

| Riesgo | Mitigación |
|--------|------------|
| `unique_together` en CatalogoModeloAuto | Decidir si se permiten múltiples filas por (marca, modelo) con distintos rangos. Si sí, cambiar a `(marca, modelo, anio_desde, anio_hasta)`. |
| CSVs antiguos sin año | Mantener `anio_desde`/`anio_hasta` nullables; tratarlos como "todos los años". |
| Chile/LATAM | No se toca `_configurar_campos_latam`. Flujo USA queda aislado. |
| `get_marcas_activas` sin año | Seguir disponible; `get_marcas_por_anio` es nuevo. Si no hay datos con año, `get_marcas_por_anio` puede devolver vacío; fallback a `get_marcas_activas` en endpoints si se desea. |
| `api_modelos_usa` existente | Se mantiene; el nuevo `api_modelos_por_marca_anio_usa` es complementario. |

---

## D) Propuesta de migración de datos

1. **Migración de esquema:** Añadir `anio_desde`, `anio_hasta` con `null=True`, `blank=True`.
2. **Data migration (opcional):** Si hay datos en CatalogoModeloAuto sin año:
   ```python
   CatalogoModeloAuto.objects.filter(anio_desde__isnull=True).update(anio_desde=1970, anio_hasta=date.today().year)
   ```
3. **Re-importación:** Ejecutar `import_modelos_usa --csv` con CSV que incluya columnas de año.
4. **Validación:** Verificar que `get_marcas_por_anio(2020)` devuelva marcas coherentes.

---

## E) Pruebas manuales y unitarias mínimas

### Pruebas manuales
1. Ir a `/us/en/vehiculos/crear/`.
2. Seleccionar año 2020 → debe cargar marcas.
3. Seleccionar marca → debe cargar modelos.
4. Completar y enviar formulario → vehículo creado.
5. Si no hay resultados para año/marca, verificar que aparezca fallback manual.

### Pruebas unitarias
```python
# tests/test_catalogo_usa.py
def test_get_marcas_por_anio():
    CatalogoModeloAuto.objects.create(marca="Toyota", modelo="Camry", anio_desde=2018, anio_hasta=2024, activo=True)
    marcas = list(CatalogoModeloAuto.get_marcas_por_anio(2020))
    assert "Toyota" in marcas

def test_get_modelos_por_marca_anio():
    CatalogoModeloAuto.objects.create(marca="Toyota", modelo="Camry", anio_desde=2018, anio_hasta=2024, activo=True)
    modelos = list(CatalogoModeloAuto.get_modelos_por_marca_anio("Toyota", 2020))
    assert "Camry" in modelos

def test_api_marcas_por_anio(client, user_usa):
    client.force_login(user_usa)
    resp = client.get("/us/en/vehiculos/api/marcas-por-anio/?anio=2020")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
```

---

## F) Impacto en Chile/LATAM

**Ninguno.** Los cambios se limitan a:

- `_configurar_campos_usa` (solo USA).
- Endpoints `api_marcas_por_anio` y `api_modelos_por_marca_anio_usa` con `if _get_country(request) != "US"` → devuelven `[]`.
- Templates `us/en/` y `us/es/` crear/editar vehículo.

Chile usa `_configurar_campos_latam`, `modelos_por_marca_api` y `ajax_modelos_por_marca_anio` sin modificación.

---

# Plan de implementación por commits

## Commit 1: Migración de catálogo
- **Archivos:** `taller/models/catalogo.py`, `taller/migrations/0089_*.py`
- **Objetivo:** Añadir `anio_desde`, `anio_hasta` y métodos `get_marcas_por_anio`, `get_modelos_por_marca_anio`
- **Riesgo:** Bajo. Campos nullables.
- **Validar:** `python manage.py migrate` sin errores.

---

## Commit 2: Importador
- **Archivos:** `taller/management/commands/import_modelos_usa.py`
- **Objetivo:** Importar CSV con columnas `anio_desde`, `anio_hasta`
- **Riesgo:** Bajo. Compatible con CSVs sin año.
- **Validar:** `python manage.py import_modelos_usa --csv archivo.csv --dry-run`

---

## Commit 3: Endpoints
- **Archivos:** `taller/vehiculos/views_fbv.py`, `taller/vehiculos/urls.py`, contexto en `crear_vehiculo`
- **Objetivo:** Crear `api_marcas_por_anio`, `api_modelos_por_marca_anio_usa` y registrar rutas
- **Riesgo:** Bajo.
- **Validar:** GET `/us/en/vehiculos/api/marcas-por-anio/?anio=2020` devuelve JSON.

---

## Commit 4: Form USA
- **Archivos:** `taller/vehiculos/forms.py`
- **Objetivo:** Marca vacía/deshabilitada hasta año; fallback manual
- **Riesgo:** Medio. Cambia UX de USA.
- **Validar:** Form USA renderiza sin error; marca con placeholder "Select year first".

---

## Commit 5: Template US EN
- **Archivos:** `templates/us/en/vehiculos/crear_vehiculo.html`
- **Objetivo:** Orden año→marca→modelo; data-ep; JS `cargarMarcasPorAnio`, `cargarModelos` actualizado
- **Riesgo:** Medio.
- **Validar:** Flujo año→marca→modelo funciona en US EN.

---

## Commit 6: Template US ES
- **Archivos:** `templates/us/es/vehiculos/crear_vehiculo.html`
- **Objetivo:** Idem US EN, textos en español
- **Riesgo:** Medio.
- **Validar:** Flujo año→marca→modelo funciona en US ES.

---

## Commit 7: Pruebas
- **Archivos:** `tests/test_catalogo_usa.py`, tests de endpoints
- **Objetivo:** Tests unitarios y de integración
- **Riesgo:** Bajo.
- **Validar:** `pytest tests/test_catalogo_usa.py -v`

---

# Análisis: fallback manual existente

## Template US EN
- **Color:** `#color-nuevo-container`, `#color_nuevo` para "Agregar nuevo color" (valor `__nuevo__`).
- **Motor:** `#motor-nuevo-container`, `#motor_nuevo`, `btn-add-motor`.
- **Caja:** `#caja-nueva-container`, `#caja_nuevo`, `btn-add-caja`.
- **Marca/Modelo:** No hay contenedores ni botones de "Agregar marca" ni "Agregar modelo". Solo selects.

## Template US ES
- **Marca:** `btn-add-marca`, `marca-nuevo-container`, `marca_nuevo` (name `nuevo_marca`).
- **Modelo:** `btn-add-modelo`, `modelo-nuevo-container`, `modelo_nuevo` (name `nuevo_modelo`).

Conclusión: US ES ya tiene fallback manual de marca y modelo. US EN no. Se puede reutilizar el patrón de US ES en US EN.

## VehiculoForm canónico
- **clean_marca:** Maneja string (nombre) vía `Marca.objects.get_or_create`. Acepta marcas manuales.
- **clean_modelo:** Solo maneja ID numérico. Si el valor es string (p. ej. "Camry" del catálogo), `int(val)` falla. Hay que ampliar para aceptar string y usar `Modelo.objects.get_or_create(marca=marca, nombre=val, country="US")` o guardar en `modelo_texto`.
- **clean():** Valida coherencia marca-modelo cuando ambos son instancias de Marca/Modelo. No contempla `marca_texto`/`modelo_texto`.
- **save():** No asigna `marca_texto` ni `modelo_texto`. Solo usa los FK. Para USA con catálogo string, conviene: cuando marca/modelo vienen como string, asignar a `marca_texto`/`modelo_texto` y dejar `marca`/`modelo` en None, O crear Marca/Modelo y usar FK. La opción más alineada con el modelo actual es crear Marca/Modelo con get_or_create.

## Ampliación de clean_modelo
Para USA con valor string (catálogo o manual):

```python
# En clean_modelo, antes de int(val):
if pais == "US" and isinstance(val, str) and not val.isdigit():
    marca = self.cleaned_data.get("marca")
    if marca and isinstance(marca, Marca):
        obj, _ = Modelo.objects.get_or_create(
            marca=marca, nombre=val.strip(), country="US",
            defaults={"nombre": val.strip()}
        )
        return obj
    raise forms.ValidationError("Seleccione marca primero")
```

## editar_vehiculo
- Usa el mismo `VehiculoForm` e `_configurar_valores_iniciales_usa`.
- Si el vehículo tiene `marca_texto`/`modelo_texto`, el form actual no los usa para initial. Hay que asegurar que, al editar, si `instance.marca_texto` existe, se ponga como valor inicial en el campo marca (o se añada como opción), e igual para `modelo_texto`.
- `_configurar_valores_iniciales_usa` asume `marca_id` y `modelo_id`. Para vehículos USA con solo `marca_texto`/`modelo_texto`, haría falta un分支 que establezca `marca.initial = instance.marca_texto` y `modelo.initial = instance.modelo_texto` cuando corresponda.

---

# Resumen técnico

- La implementación se hace sobre **CatalogoModeloAuto** y el flujo canónico actual.
- No se usan **MarcaVehiculo** ni **ModeloVehiculo**.
- Ventajas: una sola fuente de verdad, menos riesgo y menos duplicación de lógica.
