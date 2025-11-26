# 🔍 Autocomplete de Repuestos - Implementación Completa

## 📋 Resumen

Implementación completa del autocomplete de repuestos con Alpine.js que:
- ✅ Busca por código (`part_number`) o nombre
- ✅ Filtra por empresa del usuario (multi-tenant seguro)
- ✅ Autocompleta código, nombre y precio automáticamente
- ✅ Muestra stock disponible
- ✅ Vincula con el inventario (permite descontar stock)
- ✅ Permite escribir manualmente si no encuentra el repuesto (híbrido)

## 🎯 Problema Resuelto

**Antes:**
- ❌ Usuario escribía "Filtro de Aceite" manualmente
- ❌ Errores de tipeo: "Filtro Aceite" vs "Filtro de Aceite"
- ❌ No se vinculaba con inventario → No se podía descontar stock
- ❌ Precio tenía que ingresarse manualmente

**Ahora:**
- ✅ Autocomplete inteligente busca en el inventario
- ✅ Precio se llena automáticamente
- ✅ Código se llena automáticamente
- ✅ Vinculación con inventario → Stock se puede descontar
- ✅ Permite escribir manualmente si no encuentra el repuesto

## 📁 Archivos Creados/Modificados

### 1. API Backend
**Archivo**: `taller/documentos/api_repuestos.py`

Vista ligera que devuelve JSON con resultados de búsqueda:

```python
@login_required
@require_GET
def buscar_repuestos_api(request):
    """
    Busca repuestos por código o nombre.
    Filtra por empresa del usuario (multi-tenant seguro).
    Devuelve array simple de resultados.
    """
    # ... implementación ...
```

**Endpoint**: `GET /taller/api/repuestos/buscar/?q=texto`

**Respuesta**:
```json
[
    {
        "id": 1,
        "codigo": "FIL-001",
        "nombre": "Filtro de Aceite",
        "precio": 12500.0,
        "stock": 5
    },
    ...
]
```

### 2. Componente Alpine.js
**Archivo**: `templates/taller/common/documentos/document_form_alpine_example.html`

Componente reutilizable `repuestoAutocomplete(item)` que se usa en cada fila:

```javascript
function repuestoAutocomplete(item) {
    return {
        query: item.nombre || '',
        results: [],
        isOpen: false,
        highlightedIndex: -1,
        
        search() { /* Debounce + fetch */ },
        select(result) { /* Actualiza item padre */ },
        // ...
    }
}
```

### 3. Vista de Guardado Actualizada
**Archivo**: `taller/documentos/views_alpine.py`

Actualizada para usar `repuesto_id` cuando viene del autocomplete:

```python
# Si viene repuesto_id, vincular con inventario
if repuesto_id:
    repuesto = Repuesto.objects.get(id=repuesto_id, empresa=empresa)
    linea.repuesto = repuesto  # ✅ Vinculación con inventario
```

## 🔧 Configuración

### 1. Agregar URL de la API

```python
# taller/documentos/urls.py

from taller.documentos.api_repuestos import buscar_repuestos_api

urlpatterns = [
    # ... otras URLs ...
    path('api/repuestos/buscar/', buscar_repuestos_api, name='api_buscar_repuestos'),
]
```

### 2. Template Actualizado

El template ya incluye:
- ✅ Input con autocomplete
- ✅ Dropdown de resultados
- ✅ Navegación con teclado (↑↓ Enter Escape)
- ✅ Visualización de stock
- ✅ Formato de precio

## 🎨 Características del Autocomplete

### 1. Búsqueda Inteligente
- Busca por código (`part_number`) O nombre
- Mínimo 2 caracteres para buscar
- Debounce de 300ms para no saturar el servidor
- Máximo 20 resultados

### 2. Interfaz Visual
- Dropdown que aparece debajo del input
- Resaltado del item seleccionado con teclado (↑↓)
- Muestra: Nombre, Código, Precio, Stock
- Indicador "Sin Stock" en rojo si stock <= 0

### 3. Navegación con Teclado
- `↑` / `↓`: Navegar resultados
- `Enter`: Seleccionar resultado resaltado
- `Escape`: Cerrar dropdown
- `Click`: Seleccionar resultado

### 4. Comportamiento Híbrido
- ✅ Si selecciona del autocomplete → Llena código, nombre, precio + vincula con inventario
- ✅ Si escribe manualmente → Permite crear línea sin vincular con inventario

## 📊 Flujo de Datos

### 1. Usuario Escribe en el Input

```
Usuario escribe "Filtro" 
    ↓
Alpine.js detecta cambio (@input)
    ↓
Debounce 300ms
    ↓
Fetch a API: GET /taller/api/repuestos/buscar/?q=Filtro
    ↓
Backend busca en Repuesto.objects.filter(empresa=user.empresa)
    ↓
Devuelve JSON con resultados
    ↓
Dropdown muestra resultados
```

### 2. Usuario Selecciona un Repuesto

```
Usuario selecciona "Filtro de Aceite"
    ↓
select(result) actualiza:
    - item.repuesto_id = 1  ✅ Vinculación
    - item.codigo = "FIL-001"
    - item.nombre = "Filtro de Aceite"
    - item.precio = 12500.0
    ↓
Alpine.js recalcula totales automáticamente
    ↓
UI se actualiza reactivamente
```

### 3. Guardar Documento

```
Usuario envía formulario
    ↓
Django procesa JSON:
    {
        "repuesto_id": 1,  ✅ Si viene, vincula con inventario
        "codigo": "FIL-001",
        "nombre": "Filtro de Aceite",
        "precio": 12500.0,
        ...
    }
    ↓
Crea LineaRepuesto con repuesto FK
    ↓
Permite descontar stock automáticamente
```

## 🔒 Seguridad Multi-Tenant

### Backend (API)
```python
# ✅ Filtro obligatorio por empresa
empresa = request.user.empresa
qs = Repuesto.objects.filter(empresa=empresa).filter(...)
```

### Backend (Guardado)
```python
# ✅ Validación al vincular repuesto
if repuesto_id:
    repuesto = Repuesto.objects.get(id=repuesto_id, empresa=empresa)
    linea.repuesto = repuesto
```

## ✅ Ventajas vs Escritura Manual

| Aspecto | Escritura Manual | Autocomplete |
|---------|-----------------|--------------|
| **Errores de tipeo** | Frecuentes | Eliminados |
| **Vinculación Inventario** | No | Sí (con repuesto_id) |
| **Precio** | Manual | Automático |
| **Código** | Manual | Automático |
| **Stock visible** | No | Sí |
| **Flexibilidad** | Solo manual | Híbrido (manual + autocomplete) |

## 🚀 Próximos Pasos Opcionales

1. **Descontar Stock Automáticamente**
   - Crear señal Django que descontar stock cuando se crea `LineaRepuesto` con `repuesto` FK

2. **Autocomplete de Servicios**
   - Implementar mismo patrón para servicios

3. **Búsqueda Avanzada**
   - Filtrar por categoría
   - Filtrar solo con stock disponible

4. **Crear Repuesto desde el Autocomplete**
   - Botón "+ Crear nuevo" si no encuentra resultados

## 📝 Notas Importantes

1. **Debounce**: 300ms para no saturar el servidor con requests
2. **Límite de resultados**: 20 para mantener velocidad
3. **Híbrido**: Permite escribir manualmente si no encuentra el repuesto
4. **Multi-tenant**: Filtro por empresa en backend (seguridad)

## ✅ Checklist de Implementación

- [x] API de búsqueda de repuestos
- [x] Componente Alpine.js de autocomplete
- [x] Integración en template
- [x] Navegación con teclado
- [x] Visualización de stock
- [x] Vinculación con inventario (repuesto_id)
- [x] Guardado de repuesto_id en backend
- [x] Seguridad multi-tenant
- [ ] Descontar stock automáticamente (opcional)
- [ ] Autocomplete de servicios (futuro)

¡Autocomplete listo para usar! 🎉

