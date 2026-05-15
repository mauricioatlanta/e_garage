# eGarage Documentos Form Patch

## Descripción

Script JavaScript robusto para formularios de documentos con autocompletado, debounce, CSRF y preview de numeración.

## Características

### documentos_form_patch.js
- ✅ **Debounce** (250ms) para evitar spam de requests
- ✅ **AbortController** para cancelar búsquedas previas
- ✅ **CSRF seguro** para Django
- ✅ **Dropdowns renderizados** con click/teclas
- ✅ **Búsqueda de vehículos** ligada al cliente seleccionado
- ✅ **Logs claros** y silenciables con DEBUG
- ✅ **Fecha automática** (hoy) si está vacía

### documentos_form_numbers.js
- ✅ **Preview de número** de documento al cambiar tipo
- ✅ **Cache con TTL** (30s) para balance UX/consistencia
- ✅ **Debounce en change** (120ms) evita doble fetch
- ✅ **Auto-refresh** al enfocar tras edición con teclado
- ✅ **Detección de 401/302** a login (HTML sospechoso)
- ✅ **Endpoint relativo** resuelve automáticamente
- ✅ **Hook de invalidación** para refrescar tras guardar
- ✅ **Estados visuales** (loading, error, success)

## Archivos

- `documentos_form_patch.js` - Script principal
- `documentos_form_patch.css` - Estilos para dropdowns
- `documentos_form_numbers.js` - Script de numeración (complementario)
- `documentos_form_final.js` - Script base (complementario)

## Integración

### 1. HTML Template

```html
<!DOCTYPE html>
<html>
<head>
    <script src="{% static 'documentos/documentos_form_patch.js' %}" defer></script>
    <link rel="stylesheet" href="{% static 'documentos/documentos_form_patch.css' %}">
</head>
<body
    data-endpoint-clientes="{% country_url 'documentos:api_clientes' %}"
    data-endpoint-vehiculos-cliente="{% country_url 'documentos:api_vehiculos_cliente' %}"
    data-endpoint-repuestos="{% country_url 'documentos:api_repuestos' %}"
    data-endpoint-servicios="{% country_url 'documentos:api_servicios' %}"
    data-endpoint-otros="{% country_url 'documentos:api_otros' %}"
    data-endpoint-next-number="{% country_url 'documentos:api_next_number' %}"
    data-save-url="{% country_url 'documentos:api_save' %}"
>
    <!-- Campos de búsqueda -->
    <input id="client-search" autocomplete="off" />
    <div id="client-results" class="eg-dd-wrap"></div>

    <input id="vehicle-search" autocomplete="off" />
    <div id="vehicle-results" class="eg-dd-wrap"></div>

    <input id="quick-rep-search" autocomplete="off" />
    <div id="quick-rep-results" class="eg-dd-wrap"></div>

    <input id="quick-serv-search" autocomplete="off" />
    <div id="quick-serv-results" class="eg-dd-wrap"></div>

    <input id="quick-otros-search" autocomplete="off" />
    <div id="quick-otros-results" class="eg-dd-wrap"></div>

    <!-- Tipo y numeración -->
    <select id="id_tipo">
        <option value="">Seleccionar tipo...</option>
        <option value="FAC">Factura</option>
        <option value="PRES">Presupuesto</option>
        <option value="OT">Orden de Trabajo</option>
    </select>
    <span id="numero_preview">—</span>

    <!-- Fecha -->
    <input id="id_fecha_emision" type="date" />
</body>
</html>
```

### 2. Endpoints Backend

#### Clientes
```python
# URL: /api/clientes/search/
# Parámetros: ?q=texto
# Respuesta: {"results": [{"id": 1, "name": "Juan Pérez", "rut": "12.345.678-9"}]}
```

#### Vehículos
```python
# URL: /api/vehiculos/search/
# Parámetros: ?q=texto&cliente_id=123
# Respuesta: {"results": [{"id": 7, "display": "Toyota Corolla 2016", "patente": "ABCD11", "vin": "..."}]}
```

#### Repuestos
```python
# URL: /api/repuestos/search/
# Parámetros: ?q=texto
# Respuesta: {"results": [{"id": 3, "name": "Filtro de aceite", "part_number": "ABC-123"}]}
```

#### Servicios
```python
# URL: /api/servicios/search/
# Parámetros: ?q=texto
# Respuesta: {"results": [{"id": 9, "name": "Alineación y balanceo", "categoria": "Neumáticos"}]}
```

#### Otros Servicios
```python
# URL: /api/otros-servicios/search/
# Parámetros: ?q=texto
# Respuesta: {"results": [{"id": 2, "name": "Rectificado de discos", "empresa_externa": "RectiMax"}]}
```

#### Next Number
```python
# URL: /api/documentos/next_number/
# Parámetros: ?tipo=FAC
# Respuesta: {"numero": "EST-001"}
```

## Configuración

### Debug Mode

```javascript
// En el script, cambiar:
const DEBUG = true; // true para desarrollo, false para producción
```

### Personalización de Campos

```javascript
// En el script, ajustar los itemShape según tu JSON:
itemShape: { label: "name", sublabel: "rut" }, // para clientes
itemShape: { label: "display", sublabel: "patente" }, // para vehículos
itemShape: { label: "name", sublabel: "part_number" }, // para repuestos
```

## Funcionalidades

### 1. Búsqueda de Clientes
- Debounce de 250ms
- Muestra nombre y RUT
- Al seleccionar, guarda ID y limpia vehículo

### 2. Búsqueda de Vehículos
- Filtra por cliente seleccionado
- Muestra display y patente
- Se limpia al cambiar cliente

### 3. Búsqueda de Repuestos/Servicios/Otros
- Búsqueda independiente
- Limpia input al seleccionar
- TODO: Integrar con funciones de inserción

### 4. Preview de Numeración
- Se actualiza al cambiar tipo
- Muestra número siguiente
- Maneja errores gracefully
- Cache con TTL de 30 segundos
- Debounce de 120ms en change
- Auto-refresh al enfocar

### 5. Fecha Automática
- Setea fecha de hoy si está vacía
- Solo al cargar la página

### 6. Hook de Invalidación
- `window.egNumero.invalidate()` - Limpia todo el cache
- `window.egNumero.invalidate(tipo)` - Limpia cache de tipo específico
- Útil después de guardar documento para refrescar correlativo

## CSS Classes

```css
.eg-dd-wrap          /* Contenedor del dropdown */
.eg-dd               /* Lista de resultados */
.eg-dd-item          /* Item individual */
.eg-dd-title         /* Título principal */
.eg-dd-sub           /* Subtítulo */
.eg-dd-open          /* Estado abierto */
.eg-dd-loading       /* Estado de carga */
.eg-dd-error         /* Estado de error */
.eg-dd-empty         /* Estado vacío */
```

## Troubleshooting

### 1. No aparecen resultados
- Verificar que los endpoints devuelvan JSON válido
- Revisar console.log para errores
- Verificar que los IDs de elementos existan

### 2. CSRF errors
- Verificar que `csrftoken` esté en cookies
- Asegurar que Django tenga CSRF middleware activo

### 3. Dropdowns no se ven
- Verificar que `documentos_form_patch.css` esté cargado
- Revisar z-index y posicionamiento

### 4. Next number no funciona
- Verificar endpoint `data-endpoint-next-number`
- Revisar que el select `#id_tipo` exista
- Verificar que `#numero_preview` exista

## Uso del Hook de Invalidación

### Después de guardar documento
```javascript
// Tras POST exitoso de guardar documento:
window.egNumero?.invalidate(); // Limpia todo el cache y refresca

// O para un tipo específico:
window.egNumero?.invalidate('FAC'); // Solo limpia cache de facturas
```

### En tu función de guardar
```javascript
async function guardarDocumento() {
  try {
    const response = await fetch('/api/documentos/save/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    if (response.ok) {
      // Documento guardado exitosamente
      window.egNumero?.invalidate(); // Refrescar correlativo
      console.log('Documento guardado y correlativo actualizado');
    }
  } catch (error) {
    console.error('Error al guardar:', error);
  }
}
```

## Ejemplo de Uso Completo

Ver `templates_canonical/documentos/ejemplo_integracion.html` para un ejemplo completo de integración.
