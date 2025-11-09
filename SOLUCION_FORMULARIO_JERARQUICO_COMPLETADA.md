# Solución: Formulario Jerárquico - Textos en Inglés y Dependencias Corregidas

## Problemas Identificados y Solucionados

### ✅ **1. Textos en Español en JavaScript**
**Problema**: Los campos motor y caja mostraban textos en español como "Agregar nuevo motor" y "Agregar nueva caja".

**Solución**: Traducidos todos los textos al inglés en `static/js/formulario_jerarquico.js`:

#### **Textos de Opciones Traducidos:**
- `'➕ Agregar nuevo motor...'` → `'➕ Add new engine...'`
- `'➕ Agregar nueva caja...'` → `'➕ Add new transmission...'`

#### **Placeholders Traducidos:**
- `'Seleccione...'` → `'Select...'`
- `'Seleccione marca/año primero'` → `'Select brand/year first'`
- `'Seleccione modelo primero'` → `'Select model first'`
- `'No hay opciones disponibles'` → `'No options available'`

#### **Comentarios Traducidos:**
- `// restaurar selección si sigue existiendo` → `// restore selection if it still exists`
- `// guarda selección previa por si relanzas` → `// save previous selection in case of reload`
- `// modo edición: si backend no precargó motores/cajas, pedirlos` → `// edit mode: if backend didn't preload engines/transmissions, request them`
- `// CAMPOS "NUEVO"` → `// "NEW" FIELDS`

### ✅ **2. Lógica de Dependencias Corregida**
**Problema**: Los campos motor y caja aparecían con opciones cuando no deberían, especialmente para modelos nuevos como "Corolla" que es el primero en la base de datos.

**Causa**: La lógica de inicialización estaba cargando automáticamente motores y cajas para cualquier modelo seleccionado, sin verificar si realmente existían datos para ese modelo.

**Solución**: Modificada la lógica de inicialización para ser más inteligente:

#### **Antes (Incorrecto):**
```javascript
if (modeloInicial) {
  // Siempre cargaba motores/cajas para cualquier modelo
  if (motorOptions <= 1) {
    $.get(`${base}/vehiculos/ajax/motores-por-modelo/`, { modelo_id: modeloInicial })
      .done(d => populateSelect('#id_motor', normalizeList(d, 'motores'), { addNew: true }))
  }
}
```

#### **Después (Correcto):**
```javascript
if (modeloInicial) {
  // Solo carga motores/cajas si fueron precargados por el backend
  // Esto indica que estamos editando un vehículo existente, no creando uno nuevo
  if (motorOptions > 1) {
    // Backend precargó motores, agregar opción "Add new" si no está presente
    if ($('#id_motor option[value="__nuevo__"]').length === 0) {
      $('#id_motor').append('<option value="__nuevo__">➕ Add new engine...</option>');
    }
  } else {
    // No hay motores precargados, limpiar y deshabilitar
    clearAndDisableSelect('#id_motor', 'Select model first');
  }
}
```

## Cambios Específicos Realizados

### ✅ **Archivo: `static/js/formulario_jerarquico.js`**

#### **1. Función `populateSelect()` - Línea 47:**
```javascript
// ANTES
const label = selectId === '#id_motor' ? '➕ Agregar nuevo motor...' : '➕ Agregar nueva caja...';

// DESPUÉS
const label = selectId === '#id_motor' ? '➕ Add new engine...' : '➕ Add new transmission...';
```

#### **2. Función `clearAndDisableSelect()` - Línea 25:**
```javascript
// ANTES
$s.empty().append(`<option value="">${placeholder || 'Seleccione...'}</option>`).prop('disabled', true);

// DESPUÉS
$s.empty().append(`<option value="">${placeholder || 'Select...'}</option>`).prop('disabled', true);
```

#### **3. Función `populateSelect()` - Línea 34:**
```javascript
// ANTES
$s.empty().append('<option value="">Seleccione...</option>');

// DESPUÉS
$s.empty().append('<option value="">Select...</option>');
```

#### **4. Función `populateSelect()` - Línea 43:**
```javascript
// ANTES
$s.append('<option value="">No hay opciones disponibles</option>');

// DESPUÉS
$s.append('<option value="">No options available</option>');
```

#### **5. Lógica de Inicialización - Líneas 207-233:**
```javascript
// ANTES: Cargaba automáticamente motores/cajas para cualquier modelo
if (modeloInicial) {
  if (motorOptions <= 1) {
    $.get(`${base}/vehiculos/ajax/motores-por-modelo/`, { modelo_id: modeloInicial })
      .done(d => populateSelect('#id_motor', normalizeList(d, 'motores'), { addNew: true }))
  }
}

// DESPUÉS: Solo carga si fueron precargados por el backend
if (modeloInicial) {
  if (motorOptions > 1) {
    // Backend preloaded engines, add "Add new" option if not present
    if ($('#id_motor option[value="__nuevo__"]').length === 0) {
      $('#id_motor').append('<option value="__nuevo__">➕ Add new engine...</option>');
    }
  } else {
    // No engines preloaded, clear and disable
    clearAndDisableSelect('#id_motor', 'Select model first');
  }
}
```

## Resultado Final

### ✅ **Problema 1 Resuelto: Textos en Inglés**
- ✅ Todos los textos de opciones están en inglés
- ✅ Todos los placeholders están en inglés
- ✅ Todos los comentarios están en inglés
- ✅ No hay texto en español en el JavaScript

### ✅ **Problema 2 Resuelto: Dependencias Correctas**
- ✅ Los campos motor y caja ahora respetan la dependencia del modelo
- ✅ Para modelos nuevos (como "Corolla" primero en BD), no aparecen opciones incorrectas
- ✅ Solo se cargan motores/cajas si fueron precargados por el backend (modo edición)
- ✅ En modo creación, los campos se mantienen deshabilitados hasta seleccionar modelo

### ✅ **Comportamiento Esperado Ahora:**
1. **Crear vehículo nuevo con modelo "Corolla":**
   - Campo Modelo: Muestra "Corolla" seleccionado
   - Campo Motor: Muestra "Select model first" (deshabilitado)
   - Campo Caja: Muestra "Select model first" (deshabilitado)

2. **Editar vehículo existente:**
   - Si el backend precargó motores/cajas, se muestran con opción "Add new"
   - Si no hay datos precargados, se mantienen deshabilitados

3. **Seleccionar modelo diferente:**
   - Los campos motor y caja se limpian y deshabilitan
   - Solo se cargan cuando se selecciona un modelo válido

El formulario jerárquico ahora funciona correctamente con todos los textos en inglés y respeta las dependencias entre modelo, motor y caja.
