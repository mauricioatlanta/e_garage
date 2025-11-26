# 📘 Guía de Uso - locations.js

## 🎯 **Archivo JavaScript Reutilizable**

**Ubicación:** `taller/static/js/locations.js`

**Propósito:** Manejar la cascada Country → State → City en todos los formularios de manera uniforme.

---

## 📝 **EJEMPLO 1: Uso Básico en Template**

### **HTML (Formulario de Cliente):**

```html
{% load static %}

<div class="form-group">
  <label for="id_country">País</label>
  <select id="id_country" name="country" class="form-control">
    <option value="">Seleccione país...</option>
    <option value="CL">Chile</option>
    <option value="US">USA</option>
    <option value="BR">Brasil</option>
    <option value="PE">Perú</option>
    <option value="VE">Venezuela</option>
  </select>
</div>

<div class="form-group">
  <label for="id_state">Estado/Departamento</label>
  <select id="id_state" name="state" class="form-control" disabled>
    <option value="">--</option>
  </select>
</div>

<div class="form-group">
  <label for="id_city">Ciudad</label>
  <select id="id_city" name="city" class="form-control" disabled>
    <option value="">--</option>
  </select>
</div>

<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  
  // Bind automático - ¡solo 1 línea!
  bindCountryStateCity('#id_country', '#id_state', '#id_city');
</script>
```

---

## 📝 **EJEMPLO 2: Con Auto-detección de País desde URL**

```html
{% load static %}

<!-- Mismo HTML que arriba -->

<script type="module">
  import { bindCountryStateCity, autoSelectCountryFromPath } from "{% static 'js/locations.js' %}";
  
  // Auto-detectar país desde URL (/pe/, /br/, etc.)
  const detectedCountry = autoSelectCountryFromPath('#id_country');
  console.log('País detectado:', detectedCountry);
  
  // Bind cascada
  bindCountryStateCity('#id_country', '#id_state', '#id_city');
</script>
```

**Detecta automáticamente:**
- `/pe/clientes/crear/` → Selecciona "PE" automáticamente
- `/br/clientes/crear/` → Selecciona "BR" automáticamente
- `/ve/clientes/crear/` → Selecciona "VE" automáticamente

---

## 📝 **EJEMPLO 3: Con Opciones Personalizadas**

```html
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  
  // Con textos personalizados y debug
  bindCountryStateCity('#id_country', '#id_state', '#id_city', {
    loadingText: 'Cargando...',
    emptyText: 'Seleccione una opción',
    debug: true  // Ver logs en consola
  });
</script>
```

---

## 📝 **EJEMPLO 4: Usando IDs en lugar de Códigos**

Útil cuando trabajas con ForeignKeys directamente (Django forms):

```html
<script type="module">
  import { bindCountryStateCity_ByIds } from "{% static 'js/locations.js' %}";
  
  // Usa IDs de base de datos en lugar de códigos
  // Útil para formularios Django que esperan FK IDs
  bindCountryStateCity_ByIds('#id_country', '#id_estado_usa', '#id_ciudad_usa');
</script>
```

**Diferencia:**
- `bindCountryStateCity()` → Usa `state.code` como value (ej: "LIM", "SP")
- `bindCountryStateCity_ByIds()` → Usa `state.id` como value (ej: 25, 78)

---

## 📝 **EJEMPLO 5: Formulario de Empresa (ConfiguracionEmpresa)**

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
<form method="post">
  {% csrf_token %}
  
  <h3>Dirección Legal de la Empresa</h3>
  
  <div class="row">
    <div class="col-md-4">
      <label>País</label>
      <select id="id_legal_country" name="legal_country">
        <option value="">--</option>
        <option value="CL">Chile</option>
        <option value="US">USA</option>
        <option value="BR">Brasil</option>
        <option value="PE">Perú</option>
        <option value="VE">Venezuela</option>
      </select>
    </div>
    
    <div class="col-md-4">
      <label>Estado/Departamento</label>
      <select id="id_legal_state" name="legal_state" disabled>
        <option value="">--</option>
      </select>
    </div>
    
    <div class="col-md-4">
      <label>Ciudad</label>
      <select id="id_legal_city" name="legal_city" disabled>
        <option value="">--</option>
      </select>
    </div>
  </div>
  
  <button type="submit">Guardar</button>
</form>

<script type="module">
  import { bindCountryStateCity, autoSelectCountryFromPath } from "{% static 'js/locations.js' %}";
  
  // Auto-detectar y bind
  autoSelectCountryFromPath('#id_legal_country');
  bindCountryStateCity('#id_legal_country', '#id_legal_state', '#id_legal_city', {
    loadingText: 'Cargando...',
    emptyText: 'Seleccione...',
    debug: true
  });
</script>
{% endblock %}
```

---

## 📝 **EJEMPLO 6: Múltiples Direcciones en un Formulario**

```html
<h3>Dirección de Facturación</h3>
<select id="billing_country">...</select>
<select id="billing_state" disabled>...</select>
<select id="billing_city" disabled>...</select>

<h3>Dirección de Envío</h3>
<select id="shipping_country">...</select>
<select id="shipping_state" disabled>...</select>
<select id="shipping_city" disabled>...</select>

<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  
  // Bind dirección de facturación
  bindCountryStateCity('#billing_country', '#billing_state', '#billing_city');
  
  // Bind dirección de envío
  bindCountryStateCity('#shipping_country', '#shipping_state', '#shipping_city');
</script>
```

---

## 📝 **EJEMPLO 7: Con Django Forms (IDs reales)**

```html
{% load static %}

<form method="post">
  {% csrf_token %}
  
  {{ form.nombre }}
  {{ form.apellido }}
  
  <!-- Campos de ubicación -->
  <div id="location-fields">
    {% if form.pais in 'US,BR,VE,PE' %}
      <!-- Para países con modelo Estado/Ciudad unificado -->
      {{ form.estado_usa }}  <!-- id="id_estado_usa" -->
      {{ form.ciudad_usa }}  <!-- id="id_ciudad_usa" -->
      {{ form.zipcode }}
      
      <script type="module">
        import { bindCountryStateCity_ByIds } from "{% static 'js/locations.js' %}";
        
        // Crear select temporal para país (o usar valor fijo)
        const country = '{{ form.pais }}';
        
        // Si el país es fijo, simular selector
        const fakeCountrySelect = document.createElement('select');
        fakeCountrySelect.value = country;
        fakeCountrySelect.style.display = 'none';
        document.body.appendChild(fakeCountrySelect);
        
        // Bind usando IDs (para Django ForeignKey)
        bindCountryStateCity_ByIds(
          fakeCountrySelect,  // País fijo
          '#id_estado_usa',
          '#id_ciudad_usa',
          { debug: true }
        );
      </script>
    {% elif form.pais == 'CL' %}
      <!-- Para Chile (legacy) -->
      {{ form.region }}
      {{ form.ciudad }}
    {% endif %}
  </div>
  
  <button type="submit">Guardar</button>
</form>
```

---

## 📝 **EJEMPLO 8: Con Manejo de Errores**

```html
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  
  try {
    await bindCountryStateCity('#id_country', '#id_state', '#id_city', {
      debug: true
    });
    console.log('✅ Locations.js inicializado correctamente');
  } catch (error) {
    console.error('❌ Error inicializando locations.js:', error);
    
    // Mostrar mensaje al usuario
    alert('Error al cargar ubicaciones. Por favor recargue la página.');
  }
</script>
```

---

## 📝 **EJEMPLO 9: Obtener Sales Tax al Seleccionar Estado**

```html
<script type="module">
  import { bindCountryStateCity_ByIds } from "{% static 'js/locations.js' %}";
  
  // Bind normal
  bindCountryStateCity_ByIds('#id_country', '#id_state', '#id_city');
  
  // Listener adicional para sales tax
  const stateSelect = document.getElementById('id_state');
  stateSelect.addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    const salesTax = selectedOption.dataset.salesTax || 0;
    
    console.log('Sales tax del estado:', salesTax + '%');
    
    // Actualizar campo oculto o mostrar en UI
    document.getElementById('id_sales_tax').value = salesTax;
    document.getElementById('display_tax').textContent = `Tax: ${salesTax}%`;
  });
</script>
```

---

## 🔧 **TROUBLESHOOTING**

### **Error: "No se encontraron todos los selectores"**

```javascript
// Verificar que los IDs existan
console.log(document.querySelector('#id_country'));  // Debe existir
console.log(document.querySelector('#id_state'));    // Debe existir
console.log(document.querySelector('#id_city'));     // Debe existir
```

**Solución:** Verificar que los IDs en HTML coincidan con los selectores.

---

### **Error: "CORS" o "403 Forbidden"**

La API usa `credentials: 'same-origin'` para enviar cookies de sesión.

**Verificar:**
- ✅ Usuario autenticado
- ✅ CSRF token en formulario
- ✅ API en mismo dominio

---

### **Estados no cargan**

```javascript
// Activar debug
bindCountryStateCity('#id_country', '#id_state', '#id_city', {
  debug: true  // Ver logs en consola
});

// Verificar en consola:
// [locations.js] Loading states for country: PE
// [locations.js] Loaded 25 states for PE
```

---

### **Ciudades no cargan**

**Verificar que el código de estado sea correcto:**

```javascript
// En consola del navegador
fetch('/api/locations?country=PE')
  .then(r => r.json())
  .then(data => console.log('Estados:', data.states));

// Verificar que los códigos coincidan
// [{id: 77, name: "Lima", code: "LIM"}, ...]
```

---

## 📚 **FUNCIONES DISPONIBLES**

### **1. bindCountryStateCity()**

**Uso principal:** Formularios donde state usa código (ej: "LIM", "SP")

```javascript
import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
bindCountryStateCity('#id_country', '#id_state', '#id_city');
```

**Retorna:** Promise<void>

---

### **2. bindCountryStateCity_ByIds()**

**Uso:** Formularios Django donde state usa ID de base de datos

```javascript
import { bindCountryStateCity_ByIds } from "{% static 'js/locations.js' %}";
bindCountryStateCity_ByIds('#id_country', '#id_estado_usa', '#id_ciudad_usa');
```

**Ventaja:** Incluye `data-sales-tax` en opciones de estado

---

### **3. detectCountryFromPath()**

**Uso:** Detectar país desde URL

```javascript
import { detectCountryFromPath } from "{% static 'js/locations.js' %}";

const country = detectCountryFromPath();
console.log(country);  // "PE" si estás en /pe/
```

**Retorna:** String ('CL', 'US', 'BR', 'PE', 'VE') o null

---

### **4. autoSelectCountryFromPath()**

**Uso:** Auto-seleccionar país en select según URL

```javascript
import { autoSelectCountryFromPath } from "{% static 'js/locations.js' %}";

const selectedCountry = autoSelectCountryFromPath('#id_country');
console.log('País seleccionado automáticamente:', selectedCountry);
```

**Retorna:** String del país seleccionado o null

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

### **En tu template:**

```html
{% load static %}

<!-- 1. Incluir selectores con IDs correctos -->
<select id="id_country">...</select>
<select id="id_state" disabled>...</select>
<select id="id_city" disabled>...</select>

<!-- 2. Incluir script al final del form -->
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_country', '#id_state', '#id_city');
</script>
```

### **Verificar:**
- [✅] `{% load static %}` al inicio del template
- [✅] `<script type="module">` (no olvidar type="module")
- [✅] IDs de selectores coinciden
- [✅] State y City empiezan con `disabled`
- [✅] API `/api/locations` funcionando

---

## 🎨 **INTEGRACIÓN CON DJANGO FORMS**

### **Opción A: País Fijo (desde empresa)**

```python
# views.py
def crear_cliente(request):
    empresa = request.user.empresa
    pais = empresa.pais
    
    return render(request, 'clientes/crear.html', {
        'pais': pais,
        'form': form
    })
```

```html
<!-- template -->
<script type="module">
  import { bindCountryStateCity_ByIds } from "{% static 'js/locations.js' %}";
  
  // País fijo desde Django
  const country = '{{ pais }}';
  
  // Crear select invisible
  const hiddenCountry = document.createElement('select');
  hiddenCountry.value = country;
  hiddenCountry.style.display = 'none';
  document.body.appendChild(hiddenCountry);
  
  // Bind
  bindCountryStateCity_ByIds(hiddenCountry, '#id_estado_usa', '#id_ciudad_usa');
</script>
```

---

### **Opción B: País Seleccionable (multi-empresa)**

```html
<script type="module">
  import { bindCountryStateCity_ByIds } from "{% static 'js/locations.js' %}";
  
  // Si el usuario puede cambiar de país
  bindCountryStateCity_ByIds('#id_pais_empresa', '#id_estado_usa', '#id_ciudad_usa');
</script>
```

---

## 🔍 **EJEMPLO COMPLETO: Formulario de Cliente USA**

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="container">
  <h2>Nuevo Cliente - USA</h2>
  
  <form method="post">
    {% csrf_token %}
    
    <!-- Datos básicos -->
    <div class="row">
      <div class="col-md-6">
        {{ form.nombre.label_tag }}
        {{ form.nombre }}
      </div>
      <div class="col-md-6">
        {{ form.apellido.label_tag }}
        {{ form.apellido }}
      </div>
    </div>
    
    <!-- Email y Tax ID -->
    <div class="row">
      <div class="col-md-6">
        {{ form.email.label_tag }}
        {{ form.email }}
      </div>
      <div class="col-md-3">
        <label>Tax ID Type</label>
        <select name="tax_id_type" class="form-control">
          <option value="US_EIN">EIN (Empresa)</option>
          <option value="US_SSN">SSN (Persona)</option>
        </select>
      </div>
      <div class="col-md-3">
        {{ form.tax_id.label_tag }}
        {{ form.tax_id }}
      </div>
    </div>
    
    <!-- Ubicación -->
    <h4>Dirección</h4>
    <div class="row">
      <div class="col-md-12">
        {{ form.direccion.label_tag }}
        {{ form.direccion }}
      </div>
    </div>
    
    <div class="row">
      <div class="col-md-4">
        <label for="id_estado_usa">State</label>
        {{ form.estado_usa }}
      </div>
      <div class="col-md-4">
        <label for="id_ciudad_usa">City</label>
        {{ form.ciudad_usa }}
      </div>
      <div class="col-md-4">
        {{ form.zipcode.label_tag }}
        {{ form.zipcode }}
      </div>
    </div>
    
    <button type="submit" class="btn btn-primary">Guardar Cliente</button>
  </form>
</div>

<script type="module">
  import { bindCountryStateCity_ByIds } from "{% static 'js/locations.js' %}";
  
  // País fijo para USA
  const countrySelect = document.createElement('select');
  countrySelect.value = 'US';
  document.body.appendChild(countrySelect);
  countrySelect.style.display = 'none';
  
  // Bind con IDs (para Django ForeignKeys)
  bindCountryStateCity_ByIds(
    countrySelect,
    '#id_estado_usa',
    '#id_ciudad_usa',
    {
      loadingText: 'Loading...',
      emptyText: 'Select...',
      debug: true
    }
  );
</script>
{% endblock %}
```

---

## 🎯 **VENTAJAS DE ESTE ENFOQUE**

### **1. DRY (Don't Repeat Yourself):**
- ✅ Un solo archivo JavaScript
- ✅ Reutilizable en todos los formularios
- ✅ Fácil de mantener

### **2. Consistencia:**
- ✅ Mismo comportamiento en todos los formularios
- ✅ Mismos textos (loading, empty)
- ✅ Mismo manejo de errores

### **3. Escalabilidad:**
- ✅ Agregar país: Solo actualizar API
- ✅ Cambiar comportamiento: Solo editar locations.js
- ✅ No tocar templates individuales

### **4. Testing:**
- ✅ Debug mode para desarrollo
- ✅ Logs claros en consola
- ✅ Manejo de errores robusto

### **5. Flexibilidad:**
- ✅ Soporta códigos o IDs
- ✅ Auto-detección de país
- ✅ Opciones configurables

---

## 📋 **CHECKLIST DE MIGRACIÓN DE FORMULARIOS EXISTENTES**

Para migrar un formulario existente a usar `locations.js`:

- [ ] 1. Identificar los selectores de país/estado/ciudad
- [ ] 2. Asegurar que tengan IDs únicos
- [ ] 3. Agregar `{% load static %}` al template
- [ ] 4. Agregar `<script type="module">` al final
- [ ] 5. Importar y llamar `bindCountryStateCity()`
- [ ] 6. Eliminar JavaScript duplicado viejo
- [ ] 7. Probar en navegador
- [ ] 8. Verificar que cargue estados
- [ ] 9. Verificar que cargue ciudades
- [ ] 10. Verificar que guarde correctamente

---

## 🚀 **PRÓXIMOS PASOS**

### **Formularios a Actualizar:**

1. ⚠️ `templates/taller/common/clientes/crear_cliente.html`
2. ⚠️ `templates/taller/clientes/cliente_form.html`
3. ⚠️ `templates/taller/clientes/editar_cliente.html`
4. ⚠️ `templates/taller/common/configuracion/empresa_settings.html`
5. ⚠️ Cualquier formulario que maneje ubicaciones

### **Patrón de migración:**

```diff
- <script>
-   // JavaScript inline duplicado
-   document.getElementById('id_state').addEventListener('change', ...)
-   fetch('/taller/ajax/ciudades/...')
- </script>

+ <script type="module">
+   import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
+   bindCountryStateCity('#id_country', '#id_state', '#id_city');
+ </script>
```

---

## 📖 **REFERENCIAS**

- **Archivo:** `taller/static/js/locations.js`
- **API:** `taller/ubicacion/api.py`
- **Documentación API:** `API_UBICACIONES_UNIFICADA.md`
- **Sistema completo:** `SISTEMA_COMPLETO_MULTI_PAIS_IMPLEMENTADO.md`

---

## ✅ **RESUMEN**

✅ **JavaScript reutilizable creado** (locations.js)  
✅ **4 funciones útiles** exportadas  
✅ **Ejemplos completos** para casos comunes  
✅ **Compatible con Django forms** (ForeignKeys)  
✅ **Debug mode** incluido  
✅ **Manejo de errores** robusto  
✅ **Auto-detección de país** desde URL  

**Siguiente paso:** Integrar en formularios existentes

