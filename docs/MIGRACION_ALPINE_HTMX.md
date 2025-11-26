# 🚀 Migración a Alpine.js + HTMX - eGarage

## 📋 Resumen

Este documento describe la migración del frontend de jQuery/JavaScript vanilla a **Alpine.js** (para reactividad) y **HTMX** (para interacciones servidor-cliente).

**Beneficios:**
- ✅ Código más limpio y mantenible
- ✅ Lógica directamente en HTML (sin archivos JS separados)
- ✅ Menos código JavaScript necesario
- ✅ Reactividad automática sin estado manual
- ✅ Interacciones AJAX sin escribir fetch/XMLHttpRequest

---

## 🎯 Alpine.js - Reactividad Ligera

### ¿Qué es Alpine.js?

Alpine.js es un framework JavaScript ligero (~15KB) que te permite agregar reactividad directamente en el HTML usando atributos `x-data`, `x-show`, `x-bind`, etc.

**Perfecto para:**
- ✅ Cálculos dinámicos (totales, subtotales)
- ✅ Mostrar/ocultar elementos
- ✅ Validaciones en tiempo real
- ✅ Formularios interactivos

### Instalación

```html
<!-- En base.html o template base -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

O vía CDN:
```html
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

---

## 📝 Ejemplos de Migración

### 1. Cálculo de Subtotal de Fila (Repuestos/Servicios)

#### ANTES (jQuery/JavaScript):

```javascript
// static/js/documento_form_futurista.js
function recalcTotals() {
  let sumRep = 0;
  document.querySelectorAll('.repuesto-line').forEach(l => {
    const price = parseFloat(l.querySelector('.part-price').value || 0);
    const qty = parseFloat(l.querySelector('.part-qty').value || 0);
    const subtotal = price * qty;
    sumRep += subtotal;
    l.querySelector('.subtotal').textContent = formatCurrency(subtotal);
  });
  // ... más código
}

// Event listeners
document.addEventListener('input', (e) => {
  if (e.target.classList.contains('part-price') || e.target.classList.contains('part-qty')) {
    recalcTotals();
  }
});
```

#### DESPUÉS (Alpine.js):

```html
<!-- En el template HTML directamente -->
<div x-data="{
  price: 0,
  qty: 1,
  get subtotal() {
    return this.price * this.qty;
  },
  get subtotalFormatted() {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0
    }).format(this.subtotal);
  }
}">
  <input 
    type="number" 
    x-model.number="price" 
    step="0.01"
    placeholder="Precio"
    class="form-input">
  
  <input 
    type="number" 
    x-model.number="qty" 
    min="1"
    placeholder="Cantidad"
    class="form-input">
  
  <div x-text="subtotalFormatted" class="font-bold"></div>
</div>
```

**Ventajas:**
- ✅ Cálculo automático cuando cambia `price` o `qty`
- ✅ Sin event listeners manuales
- ✅ Lógica visible directamente en el HTML
- ✅ Reactividad automática

---

### 2. Tabla de Repuestos con Totales Dinámicos

#### ANTES (jQuery):

```javascript
// Agregar fila
function agregarRepuesto() {
  const tbody = document.querySelector('#tabla-repuestos tbody');
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><input type="text" class="partnumber-input" placeholder="Partnumber"></td>
    <td><input type="number" class="precio-input" value="0"></td>
    <td><input type="number" class="cantidad-input" value="1"></td>
    <td class="subtotal">$0</td>
    <td><button onclick="this.closest('tr').remove(); actualizarTotalRepuestos();">✖</button></td>
  `;
  tbody.appendChild(tr);
  
  // Conectar eventos
  tr.querySelector('.precio-input').addEventListener('input', actualizarTotalRepuestos);
  tr.querySelector('.cantidad-input').addEventListener('input', actualizarTotalRepuestos);
}

function actualizarTotalRepuestos() {
  let total = 0;
  document.querySelectorAll('#tabla-repuestos tbody tr').forEach(tr => {
    const precio = parseFloat(tr.querySelector('.precio-input').value || 0);
    const cantidad = parseFloat(tr.querySelector('.cantidad-input').value || 0);
    const subtotal = precio * cantidad;
    tr.querySelector('.subtotal').textContent = '$' + subtotal.toLocaleString();
    total += subtotal;
  });
  document.getElementById('total-repuestos').textContent = '$' + total.toLocaleString();
}
```

#### DESPUÉS (Alpine.js):

```html
<div x-data="repuestosTable()">
  <table>
    <thead>
      <tr>
        <th>Partnumber</th>
        <th>Precio</th>
        <th>Cantidad</th>
        <th>Subtotal</th>
        <th>Acciones</th>
      </tr>
    </thead>
    <tbody>
      <template x-for="(item, index) in items" :key="index">
        <tr>
          <td>
            <input 
              type="text" 
              x-model="item.partnumber"
              placeholder="Partnumber"
              class="form-input">
          </td>
          <td>
            <input 
              type="number" 
              x-model.number="item.precio"
              step="0.01"
              min="0"
              class="form-input">
          </td>
          <td>
            <input 
              type="number" 
              x-model.number="item.cantidad"
              min="1"
              class="form-input">
          </td>
          <td x-text="formatCurrency(item.precio * item.cantidad)"></td>
          <td>
            <button 
              @click="removeItem(index)"
              class="text-red-600">
              ✖
            </button>
          </td>
        </tr>
      </template>
    </tbody>
    <tfoot>
      <tr>
        <td colspan="3" class="text-right font-bold">Total:</td>
        <td x-text="formatCurrency(total)"></td>
        <td></td>
      </tr>
    </tfoot>
  </table>
  
  <button @click="addItem()" class="btn-primary">
    + Agregar Repuesto
  </button>
</div>

<script>
function repuestosTable() {
  return {
    items: [],
    
    addItem() {
      this.items.push({
        partnumber: '',
        precio: 0,
        cantidad: 1
      });
    },
    
    removeItem(index) {
      this.items.splice(index, 1);
    },
    
    get total() {
      return this.items.reduce((sum, item) => {
        return sum + (item.precio * item.cantidad);
      }, 0);
    },
    
    formatCurrency(value) {
      return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0
      }).format(value);
    }
  };
}
</script>
```

**Ventajas:**
- ✅ Sin manipulación manual del DOM
- ✅ Agregar/eliminar filas es trivial
- ✅ Totales se calculan automáticamente
- ✅ Código mucho más simple

---

### 3. Formulario Completo de Documento

#### CON ALPINE.JS:

```html
<form 
  x-data="documentoForm()" 
  @submit.prevent="submitForm"
  method="post">
  
  <!-- Cliente -->
  <div>
    <label>Cliente</label>
    <input 
      type="text" 
      x-model="cliente"
      @input.debounce.300ms="searchCliente"
      class="form-input">
    
    <div x-show="clientes.length > 0" class="dropdown">
      <template x-for="c in clientes" :key="c.id">
        <div 
          @click="selectCliente(c)"
          class="dropdown-item"
          x-text="c.nombre">
        </div>
      </template>
    </div>
  </div>
  
  <!-- Repuestos -->
  <div x-data="{ items: [] }">
    <template x-for="(item, i) in items" :key="i">
      <div class="grid grid-cols-4 gap-2">
        <input type="text" x-model="item.codigo" placeholder="Código">
        <input type="number" x-model.number="item.precio" placeholder="Precio">
        <input type="number" x-model.number="item.cantidad" placeholder="Cantidad">
        <div x-text="formatCurrency(item.precio * item.cantidad)"></div>
      </div>
    </template>
    
    <button @click="items.push({ codigo: '', precio: 0, cantidad: 1 })">
      + Agregar
    </button>
  </div>
  
  <!-- Totales -->
  <div class="totals">
    <div>
      Subtotal: <span x-text="formatCurrency(subtotal)"></span>
    </div>
    <div>
      Impuesto: <span x-text="formatCurrency(impuesto)"></span>
    </div>
    <div class="font-bold">
      Total: <span x-text="formatCurrency(total)"></span>
    </div>
  </div>
  
  <button type="submit">Guardar</button>
</form>

<script>
function documentoForm() {
  return {
    cliente: '',
    clientes: [],
    repuestos: [],
    servicios: [],
    impuestoRate: 0.19,
    incluirImpuesto: false,
    
    async searchCliente() {
      if (this.cliente.length < 2) return;
      
      const response = await fetch(`/api/clientes/search/?q=${this.cliente}`);
      this.clientes = await response.json();
    },
    
    selectCliente(cliente) {
      this.cliente = cliente.nombre;
      this.clientes = [];
    },
    
    get subtotal() {
      const repuestosTotal = this.repuestos.reduce((sum, r) => 
        sum + (r.precio * r.cantidad), 0);
      const serviciosTotal = this.servicios.reduce((sum, s) => 
        sum + s.precio, 0);
      return repuestosTotal + serviciosTotal;
    },
    
    get impuesto() {
      if (!this.incluirImpuesto) return 0;
      return this.subtotal * this.impuestoRate;
    },
    
    get total() {
      return this.subtotal + this.impuesto;
    },
    
    formatCurrency(value) {
      return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0
      }).format(value);
    },
    
    submitForm() {
      // Enviar formulario
      this.$el.submit();
    }
  };
}
</script>
```

---

## 🔄 HTMX - Interacciones Servidor-Cliente

### ¿Qué es HTMX?

HTMX te permite agregar interacciones AJAX directamente en HTML usando atributos `hx-get`, `hx-post`, `hx-swap`, etc.

**Perfecto para:**
- ✅ Agregar filas dinámicas sin recargar
- ✅ Autocompletado
- ✅ Búsquedas en tiempo real
- ✅ Actualización parcial de páginas

### Instalación

```html
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
```

O vía CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/htmx.org@1.9.10/dist/htmx.min.js"></script>
```

---

### Ejemplo: Agregar Fila de Repuesto sin Recargar

#### ANTES (Fetch API):

```javascript
async function agregarRepuesto() {
  const response = await fetch('/documentos/api/agregar-repuesto/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({})
  });
  
  const html = await response.text();
  const tbody = document.querySelector('#tabla-repuestos tbody');
  tbody.insertAdjacentHTML('beforeend', html);
}
```

#### DESPUÉS (HTMX):

```html
<!-- Botón para agregar fila -->
<button 
  hx-post="/documentos/api/agregar-repuesto/"
  hx-target="#tabla-repuestos tbody"
  hx-swap="beforeend"
  hx-include="[name='csrfmiddlewaretoken']"
  class="btn-primary">
  + Agregar Repuesto
</button>

<!-- Tabla donde se insertarán las filas -->
<table id="tabla-repuestos">
  <tbody>
    <!-- Las filas se agregan aquí dinámicamente -->
  </tbody>
</table>
```

**Vista Django:**

```python
# taller/documentos/views.py
from django.template.loader import render_to_string
from django.http import HttpResponse

@require_POST
def agregar_repuesto_fila(request):
    """Devuelve HTML de una fila vacía de repuesto"""
    html = render_to_string(
        'documentos/partials/repuesto_row.html',
        {'form': RepuestoForm()},
        request=request
    )
    return HttpResponse(html)
```

**Template `repuesto_row.html`:**

```html
<tr>
  <td>
    <input type="text" name="repuestos-__prefix__-codigo">
  </td>
  <td>
    <input type="number" name="repuestos-__prefix__-precio" step="0.01">
  </td>
  <td>
    <input type="number" name="repuestos-__prefix__-cantidad" min="1" value="1">
  </td>
  <td>
    <button 
      hx-delete="/documentos/api/eliminar-fila/"
      hx-target="closest tr"
      hx-swap="outerHTML"
      type="button">
      ✖
    </button>
  </td>
</tr>
```

---

### Ejemplo: Autocompletado con HTMX

#### ANTES (jQuery AJAX):

```javascript
$('#cliente-search').on('input', function() {
  const query = $(this).val();
  if (query.length < 2) return;
  
  $.ajax({
    url: '/api/clientes/search/',
    data: { q: query },
    success: function(data) {
      const results = data.map(c => `<div>${c.nombre}</div>`).join('');
      $('#cliente-results').html(results);
    }
  });
});
```

#### DESPUÉS (HTMX):

```html
<!-- Input de búsqueda -->
<input 
  type="text"
  name="cliente"
  hx-get="/api/clientes/search/"
  hx-trigger="input changed delay:300ms"
  hx-target="#cliente-results"
  hx-swap="innerHTML"
  placeholder="Buscar cliente...">

<!-- Contenedor de resultados -->
<div id="cliente-results">
  <!-- Los resultados aparecen aquí -->
</div>
```

**Vista Django:**

```python
@require_GET
def search_clientes(request):
    query = request.GET.get('q', '')
    clientes = Cliente.objects.para_usuario(request.user).filter(
        nombre__icontains=query
    )[:10]
    
    html = render_to_string(
        'documentos/partials/cliente_results.html',
        {'clientes': clientes},
        request=request
    )
    return HttpResponse(html)
```

---

## 🎨 Combinando Alpine.js + HTMX

La combinación perfecta: **Alpine.js para reactividad** + **HTMX para servidor**.

```html
<div 
  x-data="documentoForm()"
  hx-get="/documentos/api/form-data/"
  hx-trigger="load"
  hx-swap="innerHTML"
  hx-target="this">
  
  <!-- Alpine maneja cálculos locales -->
  <div x-show="total > 0">
    Total: <span x-text="formatCurrency(total)"></span>
  </div>
  
  <!-- HTMX maneja carga desde servidor -->
  <button 
    hx-post="/documentos/api/agregar-servicio/"
    hx-target="#servicios-list"
    hx-swap="beforeend">
    Agregar Servicio
  </button>
  
  <div id="servicios-list">
    <!-- Filas se agregan aquí vía HTMX -->
  </div>
</div>
```

---

## 📋 Checklist de Migración

### Paso 1: Agregar Librerías

- [ ] Agregar Alpine.js al `base.html`
- [ ] Agregar HTMX al `base.html`
- [ ] Verificar que no hay conflictos con jQuery existente

### Paso 2: Migrar Cálculos

- [ ] Identificar funciones de cálculo (totales, subtotales)
- [ ] Convertir a `x-data` de Alpine.js
- [ ] Reemplazar `querySelector` por `x-model` y `x-text`

### Paso 3: Migrar Interacciones

- [ ] Identificar llamadas AJAX (agregar filas, búsquedas)
- [ ] Convertir a `hx-get`, `hx-post`, etc.
- [ ] Crear vistas parciales en Django

### Paso 4: Testing

- [ ] Probar cálculos en tiempo real
- [ ] Probar agregar/eliminar filas
- [ ] Probar autocompletados
- [ ] Verificar en múltiples navegadores

---

## 📚 Recursos

- **Alpine.js**: https://alpinejs.dev/
- **HTMX**: https://htmx.org/
- **Django + HTMX**: https://django-htmx.readthedocs.io/
- **Alpine.js Playground**: https://alpinejs.dev/playground

---

**Fecha:** Noviembre 2025  
**Estado:** ✅ Documentación lista para implementación

