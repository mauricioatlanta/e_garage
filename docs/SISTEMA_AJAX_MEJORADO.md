# Sistema AJAX Mejorado - eGarage

## 🎯 Problema Solucionado

**Antes**: URLs hardcodeadas como `/cl/ajax/clientes/buscar/` causaban 404 porque no estaban enrutadas correctamente.

**Ahora**: Sistema unificado con endpoints dinámicos que funcionan en todos los países.

## 📁 Archivos Creados/Modificados

### 1. **`taller/ajax_urls.py`** - Rutas AJAX Unificadas
```python
app_name = "ajax"

urlpatterns = [
    # Rutas de clientes y vehículos (desde views_extra/ajax.py)
    path("clientes/buscar/", ajax.buscar_clientes, name="buscar_clientes"),
    path("vehiculos/por-cliente/", ajax.vehiculos_por_cliente, name="vehiculos_por_cliente"),
    path("ciudades-por-region/", ajax.ciudades_por_region, name="ciudades_por_region"),

    # Rutas de marcas, modelos, motores y cajas (desde ajax_views.py)
    path("marcas/", ajax_views.ajax_marcas, name="ajax_marcas"),
    path("modelos/", ajax_views.ajax_modelos, name="ajax_modelos"),
    path("motores/", ajax_views.ajax_motores, name="ajax_motores"),
    path("cajas/", ajax_views.ajax_cajas, name="ajax_cajas"),
]
```

### 2. **`taller/urls.py`** - Inclusión de Rutas AJAX
```python
# Antes:
path("vehiculos/ajax/", include("taller.ajax_urls")),

# Después:
path("ajax/", include("taller.ajax_urls")),
```

### 3. **`templates/taller/includes/ajax_endpoints.html`** - Endpoints Dinámicos
```html
<script>
window.AJAX_ENDPOINTS = {
  buscarClientes: "{% url 'taller:ajax:buscar_clientes' %}",
  vehiculosPorCliente: "{% url 'taller:ajax:vehiculos_por_cliente' %}",
  ciudadesPorRegion: "{% url 'taller:ajax:ciudades_por_region' %}",
  marcas: "{% url 'taller:ajax:ajax_marcas' %}",
  modelos: "{% url 'taller:ajax:ajax_modelos' %}",
  motores: "{% url 'taller:ajax:ajax_motores' %}",
  cajas: "{% url 'taller:ajax:ajax_cajas' %}",
};
</script>
```

### 4. **`static/js/ajax-helpers.js`** - Helpers JavaScript
```javascript
// Funciones helper para usar endpoints dinámicos
window.egarageAjax = {
  buscarClientes,
  vehiculosPorCliente,
  ciudadesPorRegion,
  debounce
};
```

## 🌐 URLs Disponibles

### Chile:
```
/cl/es/ajax/clientes/buscar/
/cl/es/ajax/vehiculos/por-cliente/
/cl/es/ajax/ciudades-por-region/
/cl/es/ajax/marcas/
/cl/es/ajax/modelos/
/cl/es/ajax/motores/
/cl/es/ajax/cajas/
```

### USA:
```
/us/ajax/clientes/buscar/
/us/ajax/vehiculos/por-cliente/
/us/ajax/ciudades-por-region/
/us/ajax/marcas/
/us/ajax/modelos/
/us/ajax/motores/
/us/ajax/cajas/
```

## 🔧 Cómo Usar

### 1. En Templates

#### Incluir endpoints dinámicos:
```html
{% block extra_head %}
  {% include 'taller/includes/ajax_endpoints.html' %}
  {{ block.super }}
{% endblock %}
```

#### Usar en JavaScript:
```javascript
// Antes (hardcodeado):
url: '/cl/ajax/clientes/buscar/'

// Después (dinámico):
url: window.AJAX_ENDPOINTS.buscarClientes
```

### 2. En JavaScript

#### Usar helpers:
```javascript
// Buscar clientes
const clientes = await window.egarageAjax.buscarClientes('fer');

// Vehículos por cliente
const vehiculos = await window.egarageAjax.vehiculosPorCliente(123);

// Ciudades por región
const ciudades = await window.egarageAjax.ciudadesPorRegion('CL', 'Santiago');
```

#### Debounce para evitar llamadas excesivas:
```javascript
const debouncedSearch = window.egarageAjax.debounce(async (query) => {
  const results = await window.egarageAjax.buscarClientes(query);
  // Procesar resultados
}, 300);
```

## ✅ Checklist de Verificación

### 1. **Verificar Endpoints en Consola:**
```javascript
// En la consola del navegador:
console.log(window.AJAX_ENDPOINTS.buscarClientes);
// Debe mostrar: /cl/es/ajax/clientes/buscar/ (o /us/ajax/clientes/buscar/)
```

### 2. **Probar Búsqueda de Clientes:**
```javascript
// En la consola:
window.egarageAjax.buscarClientes('fer').then(console.log);
// Debe devolver array de clientes con formato {id, text, subtitle}
```

### 3. **Probar Vehículos por Cliente:**
```javascript
// En la consola (reemplazar 123 con ID real):
window.egarageAjax.vehiculosPorCliente(123).then(console.log);
// Debe devolver array de vehículos con formato {id, text}
```

### 4. **Verificar URLs en Network Tab:**
- Abrir DevTools → Network
- Realizar búsqueda
- Verificar que las URLs son correctas (con prefijo país/idioma)
- Verificar que devuelven 200 OK

## 🐛 Troubleshooting

### Problema: `AJAX_ENDPOINTS is undefined`
**Solución**: Asegúrate de incluir `ajax_endpoints.html` en tu template:
```html
{% include 'taller/includes/ajax_endpoints.html' %}
```

### Problema: 404 en endpoints
**Solución**: Verificar que `taller/ajax_urls.py` está incluido en `taller/urls.py`:
```python
path("ajax/", include("taller.ajax_urls")),
```

### Problema: URLs sin prefijo país
**Solución**: Verificar que estás usando `{% url %}` en lugar de URLs hardcodeadas:
```html
<!-- ❌ Malo -->
url: '/cl/ajax/clientes/buscar/'

<!-- ✅ Bueno -->
url: window.AJAX_ENDPOINTS.buscarClientes
```

### Problema: CORS o headers faltantes
**Solución**: Asegúrate de incluir headers XMLHttpRequest:
```javascript
const resp = await fetch(url, {
  headers: { "X-Requested-With": "XMLHttpRequest" }
});
```

## 🚀 Beneficios

1. **✅ Sin 404**: URLs dinámicas funcionan en todos los países
2. **✅ Mantenible**: Un solo lugar para cambiar endpoints
3. **✅ Flexible**: Fácil agregar nuevos endpoints
4. **✅ Debuggeable**: Logs claros en consola
5. **✅ Reutilizable**: Helpers disponibles globalmente
6. **✅ Performante**: Debounce incluido para optimizar llamadas

## 📋 Migración de Templates Existentes

### Para migrar un template existente:

1. **Agregar include de endpoints:**
```html
{% block extra_head %}
  {% include 'taller/includes/ajax_endpoints.html' %}
  {{ block.super }}
{% endblock %}
```

2. **Reemplazar URLs hardcodeadas:**
```javascript
// Buscar y reemplazar:
'/cl/ajax/clientes/buscar/' → window.AJAX_ENDPOINTS.buscarClientes
'/cl/ajax/vehiculos/por-cliente/' → window.AJAX_ENDPOINTS.vehiculosPorCliente
```

3. **Opcional: Usar helpers:**
```javascript
// En lugar de fetch manual:
const clientes = await window.egarageAjax.buscarClientes(query);
```

**¡El sistema AJAX está ahora completamente unificado y libre de URLs hardcodeadas!** 🎉
