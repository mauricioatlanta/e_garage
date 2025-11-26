# 🚀 Guía de Implementación: Alpine.js + HTMX

## 📋 Plan de Migración Gradual

### Fase 1: Agregar Librerías (Sin Romper Nada)

**Paso 1.1:** Agregar Alpine.js y HTMX al `base.html`

```html
<!-- En templates/base.html o templates/common/base.html -->
<!-- ANTES de cerrar </body> -->

<!-- Alpine.js -->
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>

<!-- HTMX -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>

<!-- Configurar CSRF para HTMX -->
<script>
    document.body.addEventListener('htmx:configRequest', (event) => {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            event.detail.headers['X-CSRFToken'] = csrfToken.value;
        }
    });
</script>
```

**Paso 1.2:** Verificar que no rompe nada existente
- Alpine.js y HTMX son no-invasivos
- No afectan código jQuery existente
- Pueden coexistir perfectamente

---

### Fase 2: Migrar Cálculos Simples (Alpine.js)

**Paso 2.1:** Identificar cálculos simples

Ejemplos:
- Subtotal de una fila (precio × cantidad)
- Total de varios items
- Cálculo de impuesto

**Paso 2.2:** Convertir a Alpine.js

**ANTES:**
```javascript
function calcularSubtotal(precio, cantidad) {
    const subtotal = precio * cantidad;
    document.getElementById('subtotal').textContent = subtotal;
}

precioInput.addEventListener('input', () => {
    calcularSubtotal(
        parseFloat(precioInput.value),
        parseFloat(cantidadInput.value)
    );
});
```

**DESPUÉS:**
```html
<div x-data="{ precio: 0, cantidad: 1 }">
    <input type="number" x-model.number="precio">
    <input type="number" x-model.number="cantidad">
    <div x-text="precio * cantidad"></div>
</div>
```

---

### Fase 3: Migrar Formularios Complejos

**Paso 3.1:** Formulario de Documento (Ejemplo Completo)

Ver `ejemplos_alpine/documento_form_example.html`

**Características:**
- ✅ Autocompletado de clientes
- ✅ Tabla de repuestos dinámica
- ✅ Tabla de servicios dinámica
- ✅ Cálculo de totales en tiempo real
- ✅ Validación de formularios

---

### Fase 4: Migrar Interacciones AJAX (HTMX)

**Paso 4.1:** Agregar filas dinámicamente

**ANTES (Fetch):**
```javascript
async function agregarFila() {
    const response = await fetch('/api/agregar-fila/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    });
    const html = await response.text();
    document.getElementById('tbody').insertAdjacentHTML('beforeend', html);
}
```

**DESPUÉS (HTMX):**
```html
<button 
    hx-post="/api/agregar-fila/"
    hx-target="#tbody"
    hx-swap="beforeend">
    Agregar Fila
</button>
```

**Vista Django:**
```python
@require_POST
def agregar_fila(request):
    """Devuelve HTML de una fila vacía"""
    html = render_to_string(
        'partials/repuesto_row.html',
        {'form': RepuestoForm()},
        request=request
    )
    return HttpResponse(html)
```

**Paso 4.2:** Autocompletado

**ANTES (jQuery):**
```javascript
$('#buscar').on('input', function() {
    const query = $(this).val();
    $.ajax({
        url: '/api/buscar/',
        data: { q: query },
        success: function(data) {
            $('#resultados').html(data);
        }
    });
});
```

**DESPUÉS (HTMX):**
```html
<input 
    type="text"
    hx-get="/api/buscar/"
    hx-trigger="input changed delay:300ms"
    hx-target="#resultados"
    name="q">
<div id="resultados"></div>
```

---

## 🎯 Casos de Uso Específicos

### 1. Formulario de Documento Completo

**Ubicación:** `templates/taller/common/documentos/document_form.html`

**Componentes a migrar:**
- [ ] Cálculo de subtotales de filas
- [ ] Cálculo de totales generales
- [ ] Agregar/eliminar filas de repuestos
- [ ] Agregar/eliminar filas de servicios
- [ ] Autocompletado de clientes
- [ ] Autocompletado de repuestos
- [ ] Cálculo de impuestos

**Archivo ejemplo:** `ejemplos_alpine/documento_form_example.html`

---

### 2. Formulario de Vehículos

**Ubicación:** `templates/taller/us/en/vehiculos/crear_vehiculo.html`

**Componentes a migrar:**
- [ ] Carga dinámica de modelos según marca
- [ ] Carga dinámica de motores según modelo
- [ ] Carga dinámica de cajas según modelo

**Ejemplo con Alpine.js:**
```html
<select 
    x-model="marca"
    @change="loadModelos()">
    <option value="">Seleccione marca</option>
    <!-- opciones -->
</select>

<select 
    x-model="modelo"
    x-show="modelos.length > 0"
    @change="loadMotores()">
    <template x-for="m in modelos" :key="m.id">
        <option :value="m.id" x-text="m.nombre"></option>
    </template>
</select>

<script>
function vehiculoForm() {
    return {
        marca: '',
        modelo: '',
        modelos: [],
        motores: [],
        
        async loadModelos() {
            if (!this.marca) return;
            const response = await fetch(`/api/modelos/?marca=${this.marca}`);
            this.modelos = await response.json();
        },
        
        async loadMotores() {
            if (!this.modelo) return;
            const response = await fetch(`/api/motores/?modelo=${this.modelo}`);
            this.motores = await response.json();
        }
    };
}
</script>
```

**O con HTMX:**
```html
<select 
    name="marca"
    hx-get="/api/modelos/"
    hx-trigger="change"
    hx-target="#id_modelo"
    hx-include="this">
    <!-- opciones -->
</select>

<select 
    id="id_modelo"
    name="modelo"
    hx-get="/api/motores/"
    hx-trigger="change"
    hx-target="#id_motor">
    <!-- Se llena dinámicamente -->
</select>
```

---

### 3. Dashboard con Actualización en Tiempo Real

**Ejemplo con HTMX:**
```html
<!-- Actualizar métricas cada 30 segundos -->
<div 
    hx-get="/dashboard/metrics/"
    hx-trigger="every 30s"
    hx-swap="innerHTML">
    <!-- Métricas aquí -->
</div>

<!-- Cargar gráfico dinámicamente -->
<div 
    hx-get="/dashboard/chart/"
    hx-trigger="load"
    hx-swap="innerHTML">
    Cargando gráfico...
</div>
```

---

## 📚 Recursos Adicionales

### Documentación Oficial
- **Alpine.js**: https://alpinejs.dev/start-here
- **HTMX**: https://htmx.org/docs/
- **Django + HTMX**: https://django-htmx.readthedocs.io/

### Ejemplos en el Proyecto
- `ejemplos_alpine/documento_form_example.html` - Formulario completo
- `ejemplos_alpine/ejemplo_htmx_agregar_fila.html` - HTMX para filas

### Cheat Sheet

#### Alpine.js
```html
<!-- Reactividad básica -->
<div x-data="{ count: 0 }">
    <button @click="count++">+</button>
    <span x-text="count"></span>
</div>

<!-- Mostrar/ocultar -->
<div x-show="open">Contenido</div>

<!-- Enlaces -->
<a :href="'/page/' + id">Link</a>

<!-- Clases condicionales -->
<div :class="{ 'active': isActive }">Item</div>
```

#### HTMX
```html
<!-- GET request -->
<button hx-get="/api/data/" hx-target="#result">Cargar</button>

<!-- POST request -->
<button hx-post="/api/save/" hx-swap="outerHTML">Guardar</button>

<!-- Con parámetros -->
<input 
    hx-get="/api/search/"
    hx-trigger="input changed delay:300ms"
    hx-target="#results"
    name="q">

<!-- Actualizar cada X segundos -->
<div hx-get="/updates/" hx-trigger="every 5s"></div>
```

---

## ✅ Checklist de Implementación

### Preparación
- [ ] Agregar Alpine.js a `base.html`
- [ ] Agregar HTMX a `base.html`
- [ ] Configurar CSRF token para HTMX
- [ ] Verificar que no rompe código existente

### Migración de Cálculos
- [ ] Identificar funciones de cálculo
- [ ] Convertir a componentes Alpine.js
- [ ] Probar cálculos en tiempo real
- [ ] Remover código JavaScript obsoleto

### Migración de Interacciones
- [ ] Identificar llamadas AJAX
- [ ] Crear vistas parciales en Django
- [ ] Convertir a atributos HTMX
- [ ] Probar agregar/eliminar elementos

### Testing
- [ ] Probar en múltiples navegadores
- [ ] Verificar que cálculos son correctos
- [ ] Verificar que interacciones funcionan
- [ ] Verificar performance

---

**Fecha:** Noviembre 2025  
**Estado:** ✅ Listo para implementación gradual

