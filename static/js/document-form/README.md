# Document Form JS Modules

Módulos JavaScript refactorizados del formulario de documentos de egarage.

## Estructura

```
static/js/document-form/
├── index.js          # Punto de entrada (carga todos los módulos)
├── config.js         # Configuración global (urls, país)
├── utils.js          # Utilidades (fetch, money, formatters)
├── i18n.js           # Traducciones
├── cliente.js        # Búsqueda y selección de clientes
├── vehiculo.js       # Gestión de vehículos
├── repuestos.js      # CRUD de repuestos
├── totales.js        # Cálculo de totales e impuestos
├── borrador.js       # Auto-guardado y restauración
└── ui.js            # Temas y modos de UI
```

## Uso

### Carga automática

El módulo se carga automáticamente cuando se incluye en el template:

```html
<script src="{% static 'js/document-form/index.js' %}"></script>
```

### Uso manual de funciones

```javascript
// Agregar fila de repuesto
window.addRepuestoRow();

// Recalcular totales
window.recalcTotales();

// Serializar filas
window.serializeRows();

// Guardar borrador
window.scheduleDocumentDraftSave();

// Seleccionar cliente
EG.cliente.seleccionarCliente({ id: '1', nombre: 'Test' });
```

## Módulos

### config.js
- Detecta país desde URL o formulario
- Carga endpoints desde data-* attributes
- Configuración de formato de moneda por país

### utils.js
- `EG.utils.egFetch()` - Fetch con CSRF
- `EG.utils.money()` - Formateo de moneda
- `EG.utils.filterPrefetchItems()` - Filtrado de prefetch
- `EG.utils.parseNumericInput()` - Parseo de números

### i18n.js
- Traducciones para CL, MX, PE, US, BR
- `EG.I18N.no_clients` etc.

### cliente.js
- Búsqueda de clientes (prefetch + AJAX)
- Selección de cliente
- Carga de vehículos al seleccionar

### vehiculo.js
- Carga de vehículos por cliente
- Preselección de vehículo
- Tarjeta de información

### repuestos.js
- `addRepuestoRow()` - Agregar fila
- `setupRepuestoRow()` - Configurar eventos
- Búsqueda por nombre y código

### totales.js
- `recalcTotales()` - Recalcula todos los totales
- `serializeRows()` - Serializa filas para envío
- Soporte para impuestos dinámicos

### borrador.js
- Auto-guardado en localStorage
- Restauración de borrador
- TTL de 7 días

### ui.js
- Temas por tipo de documento
- Modos de operación
- Badge de estado de pago

## Actualización del Template

Para usar los nuevos módulos, agregar en el template:

```html
{% block extra_js %}
{{ block.super }}
<script src="{% static 'js/document-form/index.js' %}"></script>
{% endblock extra_js %}
```

## Backward Compatibility

Las siguientes funciones están disponibles globalmente:

- `window.addRepuestoRow()`
- `window.recalcTotales()`
- `window.serializeRows()`
- `window.scheduleDocumentDraftSave()`
- `window.restoreDocumentDraftAfterHydrate()`
- `window.openUsedPartsModal()`
- `window.egEncodeDocumentFormNext()`

## Pruebas

Ver `tests/e2e/` para tests de Playwright del formulario.
