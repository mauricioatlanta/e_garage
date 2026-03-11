# Auditoría técnica: flujo de ingreso de vehículos eGarage

**Objetivo:** Implementar selección inteligente **año → marca → modelo** para mercado USA (1970–actualidad).

---

## 1. Modelos existentes (vehículos, marcas, modelos, años, catálogos)

| Modelo | Ruta | Responsabilidad | Año / trim |
|--------|------|-----------------|------------|
| **Vehiculo** | `taller/models/vehiculos.py` | Vehículo principal (tenant). Campos: marca, modelo, marca_texto, modelo_texto, anio, vin, motor, caja, etc. | `anio` (PositiveIntegerField). No trim. |
| **Marca** | `taller/models/marca.py` | Marca por país (CL/US/MX). `nombre`, `country`. | Sin año. |
| **Modelo** | `taller/models/modelo.py` | Modelo por marca y país. `nombre`, `marca` (FK), `country`. | Sin año, sin anio_desde/anio_hasta. |
| **CatalogoModeloAuto** | `taller/models/catalogo.py` | Catálogo global marca+modelo (strings). USA 1970–presente. | Sin año. Solo `marca`, `modelo` (CharField). |
| **MarcaVehiculo** / **ModeloVehiculo** | `taller/models/marcas_usa.py` | USA con **anio_inicio**, **anio_fin** por marca/modelo. | Tienen año; **no usados** por el flujo actual (VehiculoForm usa Marca/Modelo o CatalogoModeloAuto). |
| **MotorVehiculo** | `taller/models/extras_vehiculo.py` | Motor por país, M2M con Modelo. | Sin año. |
| **CajaVehiculo** | `taller/models/extras_vehiculo.py` | Transmisión por país, M2M con Modelo. | Sin año. |
| **ColorVehiculo** | `taller/models/extras_vehiculo.py` | Color por país. | — |
| **CostoVehiculoDesarme** | `taller/models/costo_vehiculo_desarme.py` | Costos desarme por vehículo. | — |

**Conclusión:** No hay modelo único que ya soporte “marcas/modelos por año” en el flujo canónico. `MarcaVehiculo`/`ModeloVehiculo` tienen año pero están huérfanos respecto a `Vehiculo` y al form en uso.

---

## 2. Campos en Vehiculo (año, marca, modelo, VIN, motor, transmisión)

- **Año:** `anio` (PositiveIntegerField, null=True, blank=True).
- **Marca:** `marca` (ForeignKey a `Marca`, null/blank) + `marca_texto` (CharField 100, null/blank, USA).
- **Modelo:** `modelo` (ForeignKey a `Modelo`, null/blank) + `modelo_texto` (CharField 150, null/blank, USA).
- **VIN:** `vin` (CharField 50, blank/null, db_index).
- **Motor:** `motor` (ForeignKey a `MotorVehiculo`, null/blank).
- **Transmisión:** `caja` (ForeignKey a `CajaVehiculo`, null/blank).
- **Combustible:** no existe en `Vehiculo`.
- **Trim:** no existe.

---

## 3. Marca y modelo: ForeignKey vs CharField

- **En el modelo Vehiculo:** mezcla.
  - `marca` / `modelo`: **ForeignKey** a `Marca` y `Modelo`.
  - `marca_texto` / `modelo_texto`: **CharField** (USA / catálogo global).
- **En el formulario USA:** marca y modelo se tratan como **valor de catálogo (string)** o **ID de Marca (numérico)** según fuente:
  - Si hay `CatalogoModeloAuto`: marca = ChoiceField con strings; modelo = CharField con Select poblado por JS (strings).
  - Si no hay catálogo: marca = ChoiceField con IDs de `Marca`; modelo = CharField con Select poblado por JS (IDs desde `modelos_por_marca_api`).
- **En el formulario CL/LATAM:** marca y modelo suelen ser **ModelChoiceField** (ForeignKey) a `Marca` y `Modelo`.

---

## 4. Formularios de vehículo y cuál es canónico

| Formulario | Ruta | Uso |
|------------|------|-----|
| **VehiculoForm** | `taller/vehiculos/forms.py` | **Canónico en producción.** Usado por `crear_vehiculo` y `editar_vehiculo` (views_fbv). Soporta CL/US/MX, tipo_uso, cliente opcional para desarme, DAL para cliente/motor/caja, marca/modelo según país. |
| VehiculoForm | `taller/forms.py` | Simple (exclude=["empresa"]), sin user. No usado por el flujo principal de crear/editar. |
| VehiculoForm | `taller/forms/vehiculo.py` | Referenciado por `taller.forms.__init__`. Imports incorrectos (CajaVehiculo, Modelo desde taller.models.vehiculos). **Legacy/roto.** |
| VehiculoFormDAL | `taller/forms/vehiculo_dal.py` | Variante DAL; no usado por crear/editar actual. |
| VehiculoFormSimple | `taller/forms/vehiculo_simple.py` | Simplificado; no usado en flujo principal. |
| VehiculoQuickCreateForm | `taller/forms/ops_ingreso.py` | Ingreso rápido; no es el formulario de alta canónica. |
| CierreVehiculoDesarmeForm | `taller/forms/cierre_vehiculo_desarme.py` | Solo para cierre de desarme. |

**Canónico en producción:** `taller.vehiculos.forms.VehiculoForm` (usado por `taller.vehiculos.views_fbv.crear_vehiculo` y `editar_vehiculo`).

---

## 5. Vistas y endpoints AJAX/JSON (marca/modelo)

| Endpoint | Vista | Params | Filtro año |
|----------|--------|--------|------------|
| `api/marcas/` | `api_marcas` | — | No. Devuelve todas las marcas del país. |
| `api/modelos-usa/` | `api_modelos_usa` | `marca` (string) | No. Usa `CatalogoModeloAuto.get_modelos_por_marca(marca)`. |
| `ajax/modelos-por-marca/` | `ajax_modelos_por_marca` | `marca_id` | No. Modelo por marca_id (tabla Modelo). |
| `ajax/modelos-por-marca-anio/` | `ajax_modelos_por_marca_anio` | `marca_id`, `anio` | Sí en código, pero **Modelo no tiene campo anio** → filtro por año no hace nada. |
| `api/modelos-por-marca/` | `modelos_por_marca_api` | `marca_id`, `anio` (opcional) | Intenta filtrar por año; `Modelo` no tiene `anio` ni `anio_desde`/`anio_hasta` → no efectivo. |

No existe endpoint que reciba **año** y devuelva **marcas disponibles para ese año**. No hay “marcas por año” en backend.

---

## 6. DAL, Select2 y widgets en marca/modelo

- **Cliente:** DAL ModelSelect2 (`autocomplete.ModelSelect2`), URL por país (us_en, chile, etc.).
- **Motor / caja:** DAL en `VehiculoForm` (autocomplete), URLs en form.media.
- **Marca (USA):** **ChoiceField** con Select estático (choices de `CatalogoModeloAuto.get_marcas_activas()` o `Marca.objects.filter(country="US")`). No DAL.
- **Modelo (USA):** **CharField** con **Select** vacío; se rellena por **JS** vía `cargarModelos()` usando `urlModelosPorMarcaApi` o `urlModelosUsa` (según si marca es ID o string).
- **Marca/Modelo (CL):** típicamente ModelChoiceField (no DAL en el código revisado para el listado estático).

No hay DAL/Select2 específico para “marca por año” ni “modelo por año” en el flujo actual.

---

## 7. Lógica “al seleccionar marca → filtrar modelos”

- **Sí existe:** en el template US EN `crear_vehiculo.html`, JS `cargarModelos(marcaId, anio, ...)`:
  - Si marca es numérico: llama `urlModelosPorMarcaApi?marca_id=...&anio=...`
  - Si marca es string (catálogo): llama `urlModelosUsa?marca=...`
- El backend `modelos_por_marca_api` y `ajax_modelos_por_marca_anio` aceptan `anio` pero **no filtran por año** porque el modelo `Modelo` no tiene campos de año.

---

## 8. Lógica “al seleccionar año → filtrar marcas”

- **No existe.** Las marcas se cargan todas (catálogo o `Marca.objects.filter(country="US")`). No hay endpoint “marcas por año” ni JS que filtre marcas por año.

---

## 9. Catálogo USA cargado

- **CatalogoModeloAuto:** pensado para USA 1970–presente; **sin año** (solo marca + modelo).
  - Comando: `python manage.py import_modelos_usa --csv /ruta/al/models_us_1970_present.csv`
  - Si el CSV no está cargado, el form USA usa fallback a `Marca.objects.filter(country="US")` (41 marcas con `cargar_marcas_usa`); modelos por marca vía `modelos_por_marca_api` requieren tener modelos en tabla `Modelo` con `country='US'`.
- **Marca (tabla):** 41 marcas USA cargadas con `cargar_marcas_usa`.
- **Modelo (tabla):** `cargar_modelos_usa` carga modelos por marca en `Modelo`; no hay rango de años en ese modelo.

---

## 10. Management commands (importar/sincronizar catálogos)

| Comando | Ruta | Qué hace |
|---------|------|----------|
| **cargar_marcas_usa** | `taller/management/commands/cargar_marcas_usa.py` | Inserta marcas USA en `Marca` (country=US). Lista fija ~41 marcas. |
| **cargar_modelos_usa** | `taller/management/commands/cargar_modelos_usa.py` | Inserta modelos por marca en `Modelo` (country=US). Sin año. |
| **import_modelos_usa** | `taller/management/commands/import_modelos_usa.py` | Importa CSV Marca,Modelo a `CatalogoModeloAuto`. Opción `--csv`. Sin año en el modelo. |
| seed_marcas | `taller/management/commands/seed_marcas.py` | Seed de marcas (país no verificado en detalle). |
| cargar_marcas_modelos_por_pais | `taller/management/commands/cargar_marcas_modelos_por_pais.py` | Carga marcas/modelos por país. |
| cargar_catalogo_demo | `taller/management/commands/cargar_catalogo_demo.py` | Demo de catálogo. |

Ninguno carga “marca/modelo por año” (1970–hoy) de forma que el backend actual pueda filtrar por año.

---

## 11. Fuente de datos externa USA

- **CSV** para `CatalogoModeloAuto`: diseño para “scraper VehiclesAPI USA 1970–presente”; el comando es `import_modelos_usa` (sin año en el modelo).
- **api_catalogo_views.py** (`taller/api_catalogo_views.py`): APIs sobre `CatalogoModeloAuto` (marcas, modelos por marca), sin año.
- No hay integración directa con API externa (NHTSA, VehiclesAPI, etc.) en el flujo actual; solo importación desde CSV.

---

## 12. Templates en crear/editar vehículo

| Template | Uso |
|----------|-----|
| **us/en/vehiculos/crear_vehiculo.html** | **Producción US inglés.** Usado por `crear_vehiculo` cuando country=US y lang=en. Extiende `layouts/base_egarage_panel.html`. Incluye tipo_uso, cliente, patente, VIN, año, marca, modelo, motor, caja, color; endpoints en `#vehiculos-endpoints`; JS para cliente Select2, cargarModelos(marca, anio), motor/caja. |
| us/es/vehiculos/crear_vehiculo.html | Producción US español. |
| cl/es/vehiculos/crear.html | Chile. |
| taller/common/vehiculos/vehiculo_list.html | Lista común. |
| taller/common/vehiculos/_table.html | Tabla de vehículos (incluye botón Desarme si tipo_uso=desarme). |
| taller/common/vehiculos/vehiculo_form.html | Form común (patente, VIN, año, cliente, marca, modelo, etc.); incluye bloque tipo_uso si existe. |
| taller/vehiculos/crear_vehiculo.html | Fallback genérico (referenciado en código para “else” país). |
| taller/vehiculos/eliminar_vehiculo.html | Confirmación de borrado. |

El **alta canónica** para US EN es **templates/us/en/vehiculos/crear_vehiculo.html**.

---

## 13. JavaScript en el flujo crear vehículo

- **Dentro del template** `us/en/vehiculos/crear_vehiculo.html`:
  - Endpoints leídos de `#vehiculos-endpoints` (data-ep-modelos, data-ep-modelos-usa, data-ep-clientes, etc.).
  - Prefill de cliente (Select2/API).
  - **cargarModelos(marcaId, anio, modeloSeleccionado):** fetch a `urlModelosPorMarcaApi` (marca_id + anio) o `urlModelosUsa` (marca string).
  - Listeners: cambio de marca (y año) → cargar modelos; cambio de modelo → cargar motores/cajas.
  - Manejo de agregar motor/caja (modales, POST a ajax_agregar_motor / ajax_agregar_caja).
- **form.media.js:** DAL/Select2 para cliente, motor, caja (desde VehiculoForm).
- No hay JS externo específico de “vehiculos” en `static/js` para este flujo; la lógica está embebida en el template.

---

## 14. Validaciones y duplicados marca/modelo

- **Marca:** `unique_together = [("country", "nombre")]` en `Marca`.
- **Modelo:** `unique_together = [("country", "marca", "nombre")]` en `Modelo`.
- **CatalogoModeloAuto:** `unique_together = (("marca", "modelo"),)`.
- **MotorVehiculo:** UniqueConstraint (Lower("nombre"), "country").
- En el form: validaciones de coherencia marca/modelo y país en `VehiculoForm.clean` y `clean_modelo`; no hay validación “marca/modelo por año”.

---

## 15. Código duplicado o huérfano (resumen)

- **MarcaVehiculo / ModeloVehiculo** (`taller/models/marcas_usa.py`): tienen anio_inicio/anio_fin pero **no** los usa `Vehiculo` ni `VehiculoForm`; autocompletes en `views_autocomplete_marca_usa.py` y `views_autocomplete_modelo_usa.py` referencian estos modelos pero el flujo canónico usa `Marca`/`Modelo` o `CatalogoModeloAuto`.
- **Varias definiciones de VehiculoForm** (taller/forms.py, taller/forms/vehiculo.py, taller/vehiculos/forms.py): solo `taller.vehiculos.forms.VehiculoForm` es el canónico para crear/editar.
- **views_extra/views_dashboard.py:** `from .forms import VehiculoForm` — no existe `views_extra/forms.py`; este código fallaría si se invocara; `urls_dashboard` no está incluido en `gestion_taller/urls.py` en la revisión hecha → endpoint ajax/vehiculo puede estar sin usar o roto.
- **taller/forms/vehiculo.py:** imports incorrectos (CajaVehiculo, Modelo desde taller.models.vehiculos); legacy.
- **Autocompletes duplicados:** VehiculoAutocomplete, MarcaAutocomplete, ModeloAutocomplete en `taller/views_autocomplete.py`, `taller/vehiculos/dal_views.py`, `taller/autocomplete_legacy.py`, `taller/autocomplete.py`, etc.; el flujo de crear vehículo usa el form de vehiculos + endpoints en views_fbv, no necesariamente estos autocompletes.

---

# Bloques A–E

## A) Lo ya implementado y reutilizable

- **Modelo Vehiculo:** campos `anio`, `marca`, `modelo`, `marca_texto`, `modelo_texto`, `vin`, `motor`, `caja`; lógica `get_marca_display` / `get_modelo_display`.
- **Modelos Marca y Modelo:** por país; unique_together; usados para CL y como fallback USA.
- **CatalogoModeloAuto:** get_marcas_activas(), get_modelos_por_marca(marca); CSV import vía `import_modelos_usa`.
- **VehiculoForm canónico** (`taller/vehiculos/forms.py`): detección país (path), configuración USA vs LATAM, marca ChoiceField (catálogo o Marca), modelo CharField + Select dinámico, cliente opcional para desarme, tipo_uso, DAL cliente/motor/caja.
- **Vista crear_vehiculo** (`taller/vehiculos/views_fbv.py`): template por country/lang, contexto con URLs US (url_api_clientes, url_modelos_por_marca_api, url_api_modelos_usa, etc.).
- **Endpoints:** api_marcas, api_modelos_usa, modelos_por_marca_api, ajax_modelos_por_marca_anio (parcial: aceptan año pero Modelo no tiene año).
- **Template US EN** y JS: estructura año → marca → modelo (marca primero, luego modelos); `cargarModelos(marcaId, anio)` y listeners.
- **Comandos:** cargar_marcas_usa, import_modelos_usa (--csv), cargar_modelos_usa.
- **Admin:** CatalogoModeloAutoAdmin registrado.

---

## B) Lo parcialmente implementado

- **Filtro por año:** Backend acepta `anio` en modelos_por_marca_api y ajax_modelos_por_marca_anio pero `Modelo` no tiene `anio` ni anio_desde/anio_hasta → el filtro no hace nada.
- **Orden del flujo:** En el template actual el orden es año + marca + modelo; no “primero año, luego marcas para ese año”. Las marcas no se filtran por año.
- **Catálogo USA:** CatalogoModeloAuto no tiene año; no se puede “marcas/modelos para año X” solo con este modelo.
- **MarcaVehiculo/ModeloVehiculo:** Tienen anio_inicio/anio_fin pero no están integrados en Vehiculo ni en el form canónico.

---

## C) Lo inexistente

- Modelo o tabla que relacione **marca/modelo con año** (o rango de años) y que use el flujo canónico.
- Endpoint **“marcas por año”** (GET ?anio=2020 → marcas disponibles ese año).
- Endpoint **“modelos por marca y año”** que realmente filtre por año (con datos que tengan año).
- Flujo **año → marcas → modelos** en backend y front (hoy es marca + año → modelos, y marcas no dependen de año).
- Campos **trim**, **combustible** en Vehiculo.
- Integración con API externa (NHTSA, etc.) en el código actual.
- views_extra.forms (views_dashboard lo importa y no existe).

---

## D) Riesgos técnicos y duplicidades

- **Varios VehiculoForm y autocompletes:** Riesgo de tocar el form o URL equivocados; cualquier cambio debe hacerse en `taller.vehiculos.forms.VehiculoForm` y en las vistas/URLs que lo usan.
- **MarcaVehiculo/ModeloVehiculo vs Marca/Modelo vs CatalogoModeloAuto:** Tres fuentes de verdad; decidir una estrategia (ej. un solo catálogo con año, o extender CatalogoModeloAuto con año) para no duplicar más.
- **views_dashboard.registrar_vehiculo** usa `.forms` que no existe en views_extra; si alguna URL incluye urls_dashboard, ese endpoint puede fallar.
- **Orden año → marca → modelo:** Cambiar a “primero año” implica nuevo endpoint y cambios en el form y en el JS del template sin romper CL ni otros países.

---

## E) Recomendación: punto de entrada para el nuevo flujo

- **Punto de entrada único:** mantener **una sola vista de alta** (la actual `crear_vehiculo` en `taller/vehiculos/views_fbv.py`) y **un solo form** (`taller/vehiculos/forms.VehiculoForm`).
- Para **USA año → marca → modelo**:
  1. **Datos:** Añadir **año** (o rango) al catálogo que se use para USA: ya sea ampliar `CatalogoModeloAuto` con un campo año (o anio_desde/anio_fin) y adaptar import/CSV, o reutilizar `MarcaVehiculo`/`ModeloVehiculo` y conectar ese flujo solo para USA en el mismo form/vista.
  2. **Backend:** Un endpoint **marcas por año** (p. ej. `api/marcas-por-anio/?anio=2020`) y que **modelos por marca+año** use una fuente que tenga año (CatalogoModeloAuto ampliado o MarcaVehiculo/ModeloVehiculo).
  3. **Form:** En USA, orden de campos: **año → marca → modelo**; marca se rellena por JS desde el nuevo endpoint cuando cambie el año.
  4. **Template/JS:** En `us/en/vehiculos/crear_vehiculo.html`, primero selector de año; al cambiar año, llamar al nuevo endpoint de marcas y rellenar el select de marca; al cambiar marca, mantener la lógica actual de modelos (adaptada a que el backend filtre por año si aplica).
  5. **Migración:** Definir si se rellenan años en CatalogoModeloAuto (o en MarcaVehiculo/ModeloVehiculo) desde el CSV o desde una API; no cambiar el modelo Vehiculo para el flujo básico año→marca→modelo, solo la fuente de opciones.

---

# Mapa de archivos del flujo crear/editar vehículo

## Models

| Ruta | Responsabilidad | Activo | ¿Tocar para año→marca→modelo? |
|------|------------------|--------|-------------------------------|
| taller/models/vehiculos.py | Vehiculo (marca, modelo, anio, vin, motor, caja) | Sí | No (ya tiene anio). |
| taller/models/marca.py | Marca (country, nombre) | Sí | No. |
| taller/models/modelo.py | Modelo (marca, country, nombre) | Sí | Opcional: añadir anio o rango si se filtra por año en esta tabla. |
| taller/models/catalogo.py | CatalogoModeloAuto (marca, modelo) | Sí | Sí: añadir año o rango para USA. |
| taller/models/marcas_usa.py | MarcaVehiculo, ModeloVehiculo (con anio) | Huérfano | Opcional: usarlos como fuente USA en lugar de ampliar CatalogoModeloAuto. |
| taller/models/extras_vehiculo.py | MotorVehiculo, CajaVehiculo, ColorVehiculo | Sí | No. |

## Forms

| Ruta | Responsabilidad | Activo | ¿Tocar? |
|------|------------------|--------|---------|
| taller/vehiculos/forms.py | VehiculoForm canónico (CL/US, tipo_uso, cliente, marca, modelo, DAL) | Sí | Sí: orden año→marca→modelo USA; opcional campo “marca/modelo manual”. |
| taller/forms.py | VehiculoForm simple | Secundario | No. |
| taller/forms/vehiculo.py | VehiculoForm legacy (imports rotos) | No | No. |
| taller/forms/vehiculo_dal.py | VehiculoFormDAL | No flujo principal | No. |
| taller/forms/vehiculo_simple.py | VehiculoFormSimple | No | No. |
| taller/forms/cierre_vehiculo_desarme.py | CierreVehiculoDesarmeForm | Sí (desarme) | No. |

## Views

| Ruta | Responsabilidad | Activo | ¿Tocar? |
|------|------------------|--------|---------|
| taller/vehiculos/views_fbv.py | crear_vehiculo, editar_vehiculo, lista_vehiculos, api_marcas, api_modelos_usa, modelos_por_marca_api, ajax_modelos_por_marca_anio, etc. | Sí | Sí: nuevo endpoint marcas por año; opcional que modelos_por_marca filtre por año con datos nuevos. |
| taller/vehiculos/views_cbv.py | VehiculoCreateView, VehiculoUpdateView (form_class=VehiculoForm) | No usados por URLs canónicas (urls usan views_fbv) | No. |
| taller/vehiculos/views_usa.py | crear_vehiculo (alternativa USA) | No usado (gestion_taller monta taller.urls → vehiculos → views_fbv) | No. |
| taller/views_extra/vehiculos.py | crear_vehiculo (template crear_vehiculo.html) | Probablemente legacy | No. |
| taller/views_extra/views_dashboard.py | registrar_vehiculo (ajax) | Roto (import .forms inexistente); urls_dashboard no incluido en main urls | No. |

## URLs

| Ruta | Responsabilidad | Activo | ¿Tocar? |
|------|------------------|--------|---------|
| taller/urls.py | path("vehiculos/", include(taller.vehiculos.urls)) | Sí | No. |
| taller/vehiculos/urls.py | crear/, lista, editar, api/marcas, api/modelos-usa, api/modelos-por-marca, ajax/modelos-por-marca-anio, autocomplete cliente/motor/caja | Sí | Sí: añadir ruta para marcas por año (ej. api/marcas-por-anio/). |
| gestion_taller/urls.py | Incluye taller.urls bajo us/en/, us/es/, chile/, etc. | Sí | No. |

## Templates

| Ruta | Responsabilidad | Activo | ¿Tocar? |
|------|------------------|--------|---------|
| templates/us/en/vehiculos/crear_vehiculo.html | Formulario crear vehículo US inglés | Sí | Sí: orden año → marca → modelo; JS que llame marcas por año y modelos por marca+año. |
| templates/us/es/vehiculos/crear_vehiculo.html | Formulario crear vehículo US español | Sí | Mismo criterio que US EN si se unifica flujo. |
| templates/cl/es/vehiculos/crear.html | Chile crear | Sí | No (mantener flujo actual). |
| templates/taller/common/vehiculos/vehiculo_list.html | Lista común | Sí | No. |
| templates/taller/common/vehiculos/_table.html | Tabla con botón Desarme | Sí | No. |
| templates/taller/common/vehiculos/vehiculo_form.html | Form común | Sí | Solo si se unifica bloque tipo_uso / año→marca→modelo para todos. |

## JS

| Ubicación | Responsabilidad | Activo | ¿Tocar? |
|-----------|------------------|--------|---------|
| Inline en us/en/vehiculos/crear_vehiculo.html | cargarModelos(marcaId, anio), listeners marca/año, cliente Select2, motor/caja | Sí | Sí: selector año primero; al cambiar año → fetch marcas por año → rellenar marca; al cambiar marca → modelos por marca+año (reutilizar/adaptar cargarModelos). |
| form.media.js (DAL) | Select2 cliente, motor, caja | Sí | No. |

## Commands

| Ruta | Responsabilidad | Activo | ¿Tocar? |
|------|------------------|--------|---------|
| taller/management/commands/cargar_marcas_usa.py | Carga marcas USA en Marca | Sí | No. |
| taller/management/commands/cargar_modelos_usa.py | Carga modelos USA en Modelo | Sí | Opcional: si se añade año a Modelo o a otro modelo. |
| taller/management/commands/import_modelos_usa.py | Import CSV a CatalogoModeloAuto | Sí | Sí si se añade columna año al CSV y campo en CatalogoModeloAuto. |

## Admin

| Ruta | Responsabilidad | Activo | ¿Tocar? |
|------|------------------|--------|---------|
| taller/admin.py | CatalogoModeloAutoAdmin, otros | Sí | Opcional: list_filter por año si se añade año al catálogo. |

---

# Duplicados funcionales (evidencia)

## Cuántos VehiculoForm existen

- **taller/vehiculos/forms.py** — clase `VehiculoForm` (la canónica).
- **taller/forms.py** — clase `VehiculoForm` (simple, exclude empresa).
- **taller/forms/vehiculo.py** — clase `VehiculoForm` (imports erróneos: `from taller.models.vehiculos import CajaVehiculo, Modelo`; en vehiculos están Vehiculo y VehiculoQuerySet, no CajaVehiculo ni Modelo).
- **taller/forms/vehiculo_dal.py** — clase `VehiculoFormDAL`.
- **taller/forms/vehiculo_simple.py** — clase `VehiculoFormSimple`.

**Conclusión:** 5 clases con nombre “VehiculoForm” en el proyecto; **solo la de `taller.vehiculos.forms`** es la que usa el flujo de crear/editar en producción (views_fbv importa `from taller.vehiculos.forms import VehiculoForm`).

## Cuántas vistas crear/editar vehículo existen

- **taller/vehiculos/views_fbv.py:** `crear_vehiculo`, `editar_vehiculo` — **estas son las usadas** (taller.vehiculos.urls usa `views_fbv as views` y path("crear/", views.crear_vehiculo)).
- **taller/vehiculos/views_cbv.py:** VehiculoCreateView, VehiculoUpdateView — no referenciadas en taller/vehiculos/urls.py.
- **taller/vehiculos/views_usa.py:** `crear_vehiculo` — no usada por el include actual (se usa taller.vehiculos.urls, no urls_usa).
- **taller/views_extra/vehiculos.py:** `crear_vehiculo` — devuelve "crear_vehiculo.html"; no es la ruta bajo /us/en/vehiculos/crear/.
- **taller/views_extra/views_vehiculo.py:** `crear_vehiculo` — similar.
- **deploy_atlantareciclajes/** y **_disabled_templates/** — legacy.

**Template que realmente renderiza el alta:** Para US EN, **templates/us/en/vehiculos/crear_vehiculo.html**, elegido en `views_fbv.crear_vehiculo` cuando `country == "US"` y `lang == "en"`.

## Archivos que parecen legacy y confunden el flujo

- **taller/forms/vehiculo.py** — VehiculoForm con imports incorrectos.
- **taller/views_extra/views_dashboard.py** — import `.forms` que no existe en views_extra.
- **taller/vehiculos/views_usa.py** — otra implementación de crear_vehiculo no enlazada por las URLs principales.
- **taller/models/marcas_usa.py** — MarcaVehiculo/ModeloVehiculo con año no usados por el form canónico.
- **taller/views_autocomplete.py**, **taller/autocomplete_legacy.py**, **taller/autocomplete.py** — varios autocompletes de vehículo/marca/modelo; el flujo principal usa endpoints en views_fbv y JS en el template, no necesariamente estos.

## Imports desde __init__.py que ocultan la versión real

- **taller/forms/__init__.py:** `from .vehiculo import VehiculoForm` — expone el VehiculoForm **roto** de forms/vehiculo.py. Quien haga `from taller.forms import VehiculoForm` obtiene ese, no el de vehiculos.forms. El flujo de crear/editar usa explícitamente `taller.vehiculos.forms.VehiculoForm`, por lo que no se ve afectado.

---

# Implementación mínima viable (año → marca → modelo USA)

## 1. Modelo de datos mínimo

- **Opción A (recomendada):** Ampliar **CatalogoModeloAuto** con un campo **anio** (PositiveIntegerField, null=True) o **anio_desde**/ **anio_fin** (rangos). Así una misma fila (marca, modelo) puede repetirse por año o por rango. Mantener unique_together o ajustar a (marca, modelo, anio) según diseño.
- **Opción B:** Usar **MarcaVehiculo** y **ModeloVehiculo** como fuente solo para USA y que el form canónico, cuando país=US, pida año y consulte esos modelos (ya tienen anio_inicio/anio_fin). Requiere conectar Vehiculo con MarcaVehiculo/ModeloVehiculo o seguir guardando en Vehiculo marca_texto/modelo_texto.

No es estrictamente necesario cambiar el modelo **Vehiculo** para la MVP.

## 2. Archivos exactos a modificar

- **Models:** `taller/models/catalogo.py` (añadir anio o anio_desde/anio_fin) y migración.
- **Vistas:** `taller/vehiculos/views_fbv.py` — nuevo endpoint `api_marcas_por_anio` (o similar) que, dado `anio`, devuelva marcas disponibles; opcionalmente que `modelos_por_marca_api` / `api_modelos_usa` filtren por año usando el nuevo campo.
- **URLs:** `taller/vehiculos/urls.py` — registrar la ruta del nuevo endpoint.
- **Form:** `taller/vehiculos/forms.py` — en _configurar_campos_usa: no rellenar choices de marca al inicio; dejar el select de marca vacío o “Seleccione año primero” hasta que JS lo rellene (o mantener lista estática si se prefiere compatibilidad sin JS). Asegurar que el valor de año esté disponible para el front (ej. en el widget de anio).
- **Template:** `templates/us/en/vehiculos/crear_vehiculo.html` — orden: año → marca → modelo; data-ep para el nuevo endpoint de marcas por año.
- **JS (inline en ese template):** Al cambiar año → fetch marcas para ese año → rellenar select marca; al cambiar marca → cargar modelos (ya existente, añadir anio al request si el backend lo soporta).

## 3. Endpoints nuevos necesarios

- **GET** algo como **`api/marcas-por-anio/?anio=2020`** (o `api/marcas/?anio=2020`): devuelve lista de marcas disponibles para ese año (desde CatalogoModeloAuto con año o desde MarcaVehiculo/ModeloVehiculo según la opción elegida).

## 4. Cambios en el form

- USA: no pre-rellenar choices de marca con todas las marcas (o hacerlo opcional “mostrar todas”); en la MVP se puede dejar que el select de marca se rellene solo por JS cuando haya año seleccionado.
- Asegurar que el campo `anio` exista y se renderice antes que marca/modelo para US.

## 5. Cambios en el template

- Orden de campos: **Año** → **Marca** → **Modelo** (y resto igual).
- Añadir en `#vehiculos-endpoints` un `data-ep-marcas-por-anio` con la URL del nuevo endpoint.
- En JS: listener en el select de año; al cambiar, llamar al endpoint y rellenar el select de marca; al cambiar marca, llamar a modelos (con año en query si el backend lo usa).

## 6. Cambios en JS

- Función `cargarMarcasPorAnio(anio)` que haga fetch al nuevo endpoint y rellene `#id_marca`.
- En el init o al cambiar año, llamar a `cargarMarcasPorAnio(anio)`.
- Mantener `cargarModelos(marcaId, anio, ...)` y asegurar que el backend de modelos use el año si el modelo de datos lo tiene.

## 7. Estrategia de migración de datos

- Si se añade **anio** a **CatalogoModeloAuto:** nueva migración; backfill con un valor por defecto (ej. null = “todos los años” o año 2000) y luego re-importar CSV si el CSV tiene columna año, o script que asigne un rango (ej. 1970–actual) a registros existentes.
- Si se usa **MarcaVehiculo/ModeloVehiculo:** ya tienen años; no migración de Vehiculo; solo usar esos modelos como fuente de lectura para el form USA.

## 8. Estrategia USA 1970–1980 vs 1981+

- Si el catálogo o la fuente solo tiene datos a partir de 1981, se puede:
  - Mostrar en el selector de año solo desde 1981 hasta actualidad, o
  - Incluir 1970–1980 pero aceptar que “marcas por año” devuelva vacío o lista limitada para esos años hasta que se carguen datos.
- No es obligatorio tener lógica distinta en backend para 1970–1980 vs 1981+; basta con que el endpoint “marcas por año” devuelva lo que haya en la tabla para ese año (o rango que lo contenga).

---

*Documento generado por auditoría del código; conviene revisar en el repo las rutas exactas y nombres de vistas/URLs antes de implementar.*
