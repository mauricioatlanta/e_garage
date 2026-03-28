# Fase 2: Modelo canónico de nombres/aliases (i18n)

Documento de diseño para una sola estructura de datos de nombres y sinónimos para **servicios** y **piezas**, compatible con los modelos actuales y con los catálogos USA.

---

## 1. Esquema canónico (patrón único)

Para cualquier entidad “nombrable” (servicio, pieza, categoría, subcategoría) se usa:

| Campo      | Tipo        | Uso |
|-----------|-------------|-----|
| `language`| CharField(2)| Código idioma: `es`, `en`, `pt`. |
| `label`   | CharField   | Nombre canónico en ese idioma (ej. “Engine Assembly”, “Motor completo”). |
| `aliases` | JSONField   | Lista de strings: sinónimos y slang para búsqueda (ej. `["engine", "motor"]`). |
| `is_default` | Boolean | Un solo registro por (entidad, language) con `is_default=True`; es el nombre principal. |

- **Entidad principal** conserva un campo legado `nombre` (o equivalente) para compatibilidad y como fallback si no hay filas en la tabla de nombres.
- **Búsqueda (Fase 4)** se hace sobre `label` + `aliases` por idioma.

---

## 2. Servicios (ya alineados)

Los modelos de servicios **ya siguen** este esquema. No hace falta cambiar estructura; solo usarla de forma consistente y documentarla.

| Modelo                   | Tabla de nombres           | Campos canónicos |
|--------------------------|----------------------------|------------------|
| CategoriaServicio        | CategoriaServicioName      | language, label, aliases, is_default |
| SubcategoriaServicio     | SubcategoriaServicioName   | language, label, aliases, is_default |
| Servicio                 | ServicioName               | language, label, aliases, is_default |

- **Servicio** tiene `nombre` (legacy); `get_label(language)` usa `ServicioName` y, si no hay, devuelve `nombre`.
- **Catálogos USA** (Fase 3): al migrar un ítem de `SERVICIOS_AUTOMOTRICES_USA` se crean:
  - `Servicio` (+ Categoria/Subcategoria si aplica),
  - `ServicioName(language='es', label=nombre_es, aliases=sinonimos_es, is_default=True)`,
  - `ServicioName(language='en', label=nombre_en_oficial, aliases=[nombre_en_slang] + sinonimos_en, is_default=True)`.

---

## 3. Piezas de desarme (nuevo: PiezaDesarmeName)

**Estado actual:** `PiezaDesarme` solo tiene `nombre` (CharField). No hay i18n ni aliases.

**Cambio (compatible):**

- Se **mantiene** `PiezaDesarme.nombre` sin cambios (legacy y fallback).
- Se añade el modelo **PiezaDesarmeName** (mismo patrón que ServicioName):

| Campo        | Tipo   | Descripción |
|-------------|--------|-------------|
| pieza_desarme | FK → PiezaDesarme | related_name='names' |
| language    | CharField(2) | es, en, pt |
| label       | CharField(255) | Nombre canónico en ese idioma |
| aliases     | JSONField(default=list) | Sinónimos/slang para búsqueda |
| is_default  | BooleanField(default=False) | Un solo True por (pieza_desarme, language) |

- Se añade en **PiezaDesarme** el método `get_label(self, language='es')`:
  - Si existe `names.get(language=language, is_default=True)` → devolver `label`.
  - Si no, cualquier `names.filter(language=language).first()` → su `label`.
  - Si no hay nombres para ese idioma → devolver `self.nombre`.

**Compatibilidad:**

- Código que use `pieza.nombre` sigue funcionando.
- Las piezas existentes sin filas en `PiezaDesarmeName` siguen mostrando `nombre`.
- El generador de inventario (Fase 1) puede seguir escribiendo solo `nombre`; en Fase 3 se puede rellenar también `PiezaDesarmeName` desde el catálogo USA.

**Catálogos USA (Fase 3):** al crear o vincular una pieza desde `CATALOGO_PIEZAS_DESARME_USA`:

- Crear `PiezaDesarmeName(language='es', label=nombre_es, aliases=sinonimos_es, is_default=True)`.
- Crear `PiezaDesarmeName(language='en', label=nombre_en_oficial, aliases=[nombre_en_slang] + sinonimos_en, is_default=True)`.

---

## 4. Modelos a tocar y migraciones

| Acción | Modelo / archivo | Detalle |
|--------|------------------|--------|
| Sin cambios | CategoriaServicioName, SubcategoriaServicioName, ServicioName | Ya tienen label + aliases. |
| Sin cambios | Servicio, CategoriaServicio, SubcategoriaServicio | Ya tienen get_label y FK a su *Name. |
| Añadir | PiezaDesarme | Método `get_label(language='es')`. |
| Crear | PiezaDesarmeName | Nueva tabla: pieza_desarme_id, language, label, aliases, is_default. |
| Migración | taller | Una migración: CreateModel PiezaDesarmeName + índice/unique si se desea (ej. unique por (pieza_desarme, language, is_default)). |

**Migración sugerida:** `0088_pieza_desarme_name_canonico_i18n.py` (o el siguiente número disponible en `taller/migrations/`).

---

## 5. Catálogos USA actuales (solo referencia)

- **catalogo_piezas_desarme_usa.py:** cada ítem tiene `nombre_es`, `nombre_en_oficial`, `nombre_en_slang`, `sinonimos_es`, `sinonimos_en`. Equivalencia al canónico:
  - `label_es` = `nombre_es`, `aliases_es` = `sinonimos_es`.
  - `label_en` = `nombre_en_oficial`, `aliases_en` = `[nombre_en_slang] + sinonimos_en`.
- **catalogo_servicios_usa.py:** mismo criterio.
- En Fase 3 se usarán estos campos para rellenar ServicioName / PiezaDesarmeName; los archivos de catálogo pueden seguir así hasta entonces.

---

## 6. Resumen

- **Servicios:** modelo canónico ya existe (Categoria/Subcategoria/Servicio + *Name con label y aliases). Solo documentado y uso consistente.
- **Piezas:** se añade PiezaDesarmeName y PiezaDesarme.get_label(); se mantiene `nombre` para compatibilidad.
- **Migraciones:** una nueva migración para PiezaDesarmeName.
- **Catálogos USA:** sin cambios de estructura en Fase 2; en Fase 3 se mapean al esquema canónico al persistir.

Con esto queda definido el modelo canónico i18n/aliases para Fase 2 y la base para Fase 3 (migración de servicios USA) y Fase 4 (búsqueda por slang/sinónimos).
