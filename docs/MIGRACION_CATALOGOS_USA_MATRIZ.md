# Matriz: Migración catálogos USA → capa operativa eGarage

**Causa raíz:** La capa USA (catálogos piezas/servicios) fue creada pero aún no reemplaza ni alimenta la capa operativa legacy.

**Objetivo:** Archivo por archivo: qué conservar, qué adaptar, qué eliminar.

---

## Prioridad de fases

| Fase | Descripción | Estado |
|------|-------------|--------|
| **1** | Integrar catálogo de piezas USA al flujo real de desarme (inventario automático hoy usa lógica vieja) | **Hecho** (adaptador en `catalogo_operativo.py`) |
| **2** | Definir modelo canónico de nombres/aliases para servicios y piezas (antes de seguir cargando datos) | **Hecho** |
| **3** | Migrar servicios USA reales al esquema i18n (en, es, aliases) | Pendiente |
| **4** | Actualizar APIs de búsqueda para slang y sinónimos | Pendiente |
| **5** | Eliminar duplicidad en módulo servicios (una sola implementación oficial) | **Hecho** |

---

## Fase 1 – Integrar catálogo piezas USA al desarme

| Archivo / componente | Acción | Notas |
|----------------------|--------|--------|
| `taller/catalogos/catalogo_piezas_desarme_usa.py` | **Conservar** | Fuente de verdad USA; ya existe |
| `taller/desarme/catalogo_piezas.py` | **Adaptar / Eliminar** | Hoy usa `CATALOGO_PIEZAS` (tuplas codigo, nombre, zona, precio_base); alimenta `generar_inventario_vehiculo`. Decidir: reemplazar por USA o unificar |
| `taller/desarme/services.py` | **Adaptar** | Importa `CATALOGO_PIEZAS`; `generar_inventario_vehiculo()` itera sobre él. Debe usar catálogo USA cuando contexto sea USA |
| `taller/desarme/views.py` | **Adaptar** | Llama `generar_inventario_vehiculo` al crear vehículo (L388) y en `generar_inventario_view` (L666). Usa `ZONAS_ORDEN` de catalogo_piezas (L710). Pasar contexto país/mercado |
| `taller/desarme/catalogo_operativo.py` | **Creado** | `get_catalogo_operativo_desarme(empresa)`, `get_zonas_orden_desarme(empresa)`, mapeo USA→zonas |
| `taller/desarme/forms.py` | Revisar | Si el formulario de pieza usa zonas/códigos del catálogo legacy, alinear a USA cuando aplique |
| Templates scanner/inventario que listen zonas o piezas | Revisar | Si hay dropdowns/opciones fijas, alimentar desde catálogo USA según locale |

---

## Fase 2 – Modelo canónico nombres/aliases (servicios y piezas)

| Archivo / componente | Acción | Estado |
|----------------------|--------|--------|
| **Servicios** (CategoriaServicioName, SubcategoriaServicioName, ServicioName) | **Conservar** | Ya canónico: language, label, aliases (JSONField), is_default |
| **PiezaDesarme** | **Adaptado** | Añadido `get_label(language)`; se mantiene `nombre` como fallback |
| **PiezaDesarmeName** (nuevo) | **Creado** | language, label, aliases, is_default; FK a PiezaDesarme, related_name='names' |
| Migración `0088_pieza_desarme_name_canonico_i18n.py` | **Creada** | CreateModel PiezaDesarmeName + UniqueConstraint(pieza_desarme, language, is_default) |
| `docs/MODELO_CANONICO_I18N_ALIASES_FASE2.md` | **Creado** | Diseño del esquema y mapeo catálogos USA → canónico |
| Catálogos USA (piezas/servicios) | Sin cambios en Fase 2 | En Fase 3 se mapean a *Name al persistir |

---

## Fase 3 – Servicios USA al esquema i18n (en, es, aliases)

| Archivo / componente | Acción | Notas |
|----------------------|--------|--------|
| `taller/catalogos/catalogo_servicios_usa.py` | Conservar / Adaptar | Ya tiene es/en/slang; falta modelo persistente i18n si aplica |
| Modelo Servicio / ServicioProduccion (o equivalente) | A definir | |
| Datos semilla o fixtures | A definir | Cargar servicios USA al esquema i18n |

---

## Fase 4 – APIs de búsqueda (slang y sinónimos)

| Archivo / componente | Acción | Notas |
|----------------------|--------|--------|
| APIs autocomplete/búsqueda piezas | Adaptar | Usar `buscar_piezas_usa` / catálogo USA |
| APIs autocomplete/búsqueda servicios | Adaptar | Usar `buscar_servicios_usa` y aliases |
| Endpoints que devuelven listas de servicios/piezas | A rellenar con tu guía | |

---

## Fase 5 – Eliminar duplicidad en módulo servicios

| Archivo / componente | Acción | Estado |
|----------------------|--------|--------|
| `taller/servicios/models.py`, `views.py`, `api_servicios_moderno.py`, `urls.py` | **Conservar** (oficial) | Implementación oficial única |
| `taller/documentos/api_servicios.py` | **Adaptado** | Wrapper que delega a `api_servicios_moderno.api_buscar_servicios` |
| `taller/documentos/api_otros_servicios.py` | **Eliminado** | “Otros servicios” operativos = ServicioExterno en servicios/ |
| `taller/servicios/urls_servicios.py` | **Eliminado** | Usar `taller.servicios.urls` (deploy: actualizar include) |
| `taller/servicios/servicios.py` | **Eliminado** | Lógica duplicada; CRUD en views.py + api_servicios_moderno |
| `taller/servicios/views_crear_servicio.py`, `views_crear_otro_servicio.py` | **Eliminados** | No referenciados; flujo en views.py (CBV) |
| `taller/servicios/form_servicios.py` | **Eliminado** | Solo usado por archivos eliminados |
| `cargar_servicios.py`, `cargar_servicios_directo.py`, `cargar_servicios_produccion.py`, `cargar_categorias_us.py` | **Deprecados** | Aviso: usar `cargar_catalogo_maestro` |
| `taller/management/commands/cargar_catalogo_maestro.py` | **Conservar** | Comando oficial único de carga |

---

## Siguiente comando (para guiarte)

Copia y pega uno de estos cuando quieras que avance:

1. **Rellenar Fase 1:**  
   *“Decido Fase 1: [conservar | reemplazar | unificar] el catálogo legacy en `desarme/catalogo_piezas.py`. Adapta `services.py` y `views.py` para que el inventario automático use el catálogo USA cuando el contexto sea USA.”*

2. **Solo matriz:**  
   *“Lista todos los archivos que tocan servicios (modelos, APIs, comandos, documentos) y actualiza la matriz Fase 5 con cada uno y si conservar/adaptar/eliminar.”*

3. **Implementar una fase:**  
   *“Implementa Fase [1|2|3|4|5] según la matriz y mis decisiones arriba.”*

---

## Cómo usar esta matriz

1. **Rellenar** cada celda "A rellenar con tu guía" / "A definir" con tu decisión (conservar / adaptar / eliminar y notas).
2. **Añadir filas** si faltan archivos por fase.
3. **Ejecutar** fase por fase según la prioridad 1→5.

Cuando tengas la guía archivo por archivo, dame el comando para la fase que quieras ejecutar primero (por ejemplo: *"Implementa Fase 1 según la matriz"*) y adapto el código en consecuencia.
