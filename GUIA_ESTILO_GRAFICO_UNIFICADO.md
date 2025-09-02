# Guía de Estilo Gráfico Unificado 🎨

## Descripción

Esta guía explica cómo aplicar el estilo gráfico futurista de la página de servicios a todos los templates del sistema, manteniendo consistencia visual y efectos dinámicos.

## Archivos Base Creados

### 1. CSS Principal
**Archivo:** `static/css/dynamic_background.css`
- Contiene todos los estilos del fondo dinámico espacial
- Efectos de estrellas, partículas y nubes
- Estilos de tarjetas, botones y componentes futuristas
- Clases utilitarias para efectos visuales

### 2. JavaScript de Efectos
**Archivo:** `static/js/dynamic_effects.js`
- Efectos dinámicos de partículas y explosiones
- Funciones de búsqueda y filtrado
- Sistema de modales futuristas
- Funciones globales para templates

## Estructura Base para Templates

### 1. Head Section
```html
{% extends 'base.html' %}
{% load static %}

{% block extra_head %}
<link href="/static/css/dynamic_background.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
<script src="/static/js/dynamic_effects.js"></script>
{% endblock %}
```

### 2. Content Structure
```html
{% block content %}
<div class="dynamic-background">
  <!-- Fondo dinámico espacial -->
  <div class="space-background">
    <div class="stars"></div>
    <div class="twinkling"></div>
    <div class="clouds"></div>
  </div>
  
  <!-- Partículas flotantes -->
  <div id="particles" class="particles-container"></div>
  
  <div class="content-container max-w-7xl mx-auto">
    <!-- Contenido aquí -->
  </div>
</div>
{% endblock %}
```

### 3. Header Futurista
```html
<!-- Header Section with Glowing Effect -->
<div class="futuristic-header">
  <div class="glow-bg"></div>
  <div class="content">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-lg shadow-lg ring-2 ring-cyan-400/40">🔧</div>
        <div>
          <h1 class="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-cyan-300 via-lime-300 to-emerald-400">
            Título del Módulo
          </h1>
          <p class="text-gray-400 text-xs">Descripción del módulo</p>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2 text-xs text-cyan-300">
          <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span>Sistema activo</span>
        </div>
        <div class="relative group">
          <div class="absolute -inset-1 rounded-lg bg-gradient-to-r from-emerald-500 via-lime-500 to-green-500 opacity-30 blur group-hover:opacity-50 transition-opacity"></div>
          <a href="{% url 'crear_item' %}" 
             class="relative inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-600 via-lime-600 to-green-600 hover:from-emerald-500 hover:via-lime-500 hover:to-green-500 text-white font-bold text-sm shadow-lg shadow-emerald-800/40 transition-all duration-300 border border-emerald-400/40">
            <div class="w-4 h-4 rounded-md bg-white/20 flex items-center justify-center">
              <span class="text-sm">➕</span>
            </div>
            <span>Agregar Item</span>
          </a>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 4. Búsqueda Futurista
```html
<!-- Search Section -->
<div class="futuristic-search">
  <div class="glow-bg"></div>
  <div class="input-container">
    <div class="search-icon">🔍</div>
    <input type="search" id="searchInput" name="q" 
           placeholder="Buscar..." 
           class="w-full px-3 py-2 bg-transparent text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 text-sm">
    <button type="button" id="searchBtn" class="search-btn">
      ESCANEAR
    </button>
  </div>
</div>
```

### 5. Filtros Futuristas
```html
<!-- Filter Section -->
<div class="futuristic-filters">
  <select id="categoriaFilter" class="px-3 py-2 rounded-lg bg-black/40 border border-cyan-400/30 text-cyan-300 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50">
    <option value="">Todas las Categorías</option>
    {% for categoria in categorias %}
    <option value="{{ categoria.code }}">{{ categoria.get_label }}</option>
    {% endfor %}
  </select>
</div>
```

### 6. Grid de Tarjetas
```html
<!-- Items Grid - Futuristic Style -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3" id="itemsContainer">
  {% for item in items %}
  <div class="group relative futuristic-card transform hover:scale-105 transition-all duration-300" 
       data-name="{{ item.nombre|default:'' }}" 
       data-categoria="{{ item.categoria.get_label|default:'' }}"
       data-categoria-code="{{ item.categoria.code|default:'' }}">
    <!-- Glow effect -->
    <div class="glow-effect"></div>
    
    <!-- Main card -->
    <div class="relative rounded-lg border border-gray-700/50 bg-black/40 backdrop-blur-sm hover:border-cyan-400/30 transition-all duration-300 h-48 flex flex-col">
      <!-- Header with ID -->
      <div class="p-3 border-b border-gray-700/30 flex-shrink-0">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <div class="w-6 h-6 rounded-md bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-400/30 flex items-center justify-center">
              <span class="text-cyan-300 font-mono text-xs">🔧</span>
            </div>
            <div>
              <p class="text-cyan-300 font-mono font-bold text-sm">{{ item.nombre|truncatechars:12 }}</p>
              <p class="text-gray-500 text-xs">ID: #{{ item.pk }}</p>
            </div>
          </div>
          <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
        </div>
      </div>
      
      <!-- Content -->
      <div class="p-3 space-y-2 flex-1">
        <!-- Contenido específico del item -->
      </div>
      
      <!-- Actions -->
      <div class="p-3 border-t border-gray-700/30 flex-shrink-0">
        <div class="flex justify-between space-x-1">
          <a href="{% url 'ver_item' item.pk %}" 
             class="flex-1 group/btn relative px-2 py-1.5 rounded-md bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border border-cyan-400/40 text-cyan-300 hover:from-cyan-500/30 hover:to-blue-500/30 hover:text-cyan-200 transition-all duration-200 text-xs font-medium text-center">
            <span class="relative z-10 flex items-center justify-center space-x-1">
              <span>👁️</span>
              <span>Ver</span>
            </span>
            <div class="absolute inset-0 rounded-md bg-gradient-to-r from-cyan-600 to-blue-600 opacity-0 group-hover/btn:opacity-20 transition-opacity"></div>
          </a>
          <a href="{% url 'editar_item' item.pk %}" 
             class="flex-1 group/btn relative px-2 py-1.5 rounded-md bg-gradient-to-r from-emerald-600/20 to-green-600/20 border border-emerald-400/40 text-emerald-300 hover:from-emerald-500/30 hover:to-green-500/30 hover:text-emerald-200 transition-all duration-200 text-xs font-medium text-center">
            <span class="relative z-10 flex items-center justify-center space-x-1">
              <span>⚙️</span>
              <span>Editar</span>
            </span>
            <div class="absolute inset-0 rounded-md bg-gradient-to-r from-emerald-600 to-green-600 opacity-0 group-hover/btn:opacity-20 transition-opacity"></div>
          </a>
          <button onclick="confirmarEliminacion({{ item.pk }}, '{{ item.nombre|escapejs }}', '{% url 'eliminar_item' item.pk %}')" 
                  class="flex-1 group/btn relative px-2 py-1.5 rounded-md bg-gradient-to-r from-red-600/20 to-pink-600/20 border border-red-400/40 text-red-300 hover:from-red-500/30 hover:to-pink-500/30 hover:text-red-200 transition-all duration-200 text-xs font-medium text-center">
            <span class="relative z-10 flex items-center justify-center space-x-1">
              <span>🗑️</span>
              <span>Eliminar</span>
            </span>
            <div class="absolute inset-0 rounded-md bg-gradient-to-r from-red-600 to-pink-600 opacity-0 group-hover/btn:opacity-20 transition-opacity"></div>
          </button>
        </div>
      </div>
    </div>
  </div>
  {% empty %}
  <div class="col-span-full">
    <div class="relative">
      <div class="absolute -inset-1 rounded-xl bg-gradient-to-r from-gray-600 via-gray-500 to-gray-600 opacity-20 blur-xl"></div>
      <div class="relative rounded-xl border border-gray-600/30 bg-black/40 backdrop-blur-sm p-8 text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-gray-500/20 to-gray-600/20 border border-gray-400/30 flex items-center justify-center text-2xl">
          🔧
        </div>
        <h3 class="text-lg font-bold text-gray-300 mb-2">No hay items registrados</h3>
        <p class="text-gray-500 text-sm">Comienza agregando tu primer item al sistema</p>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
```

### 7. Modal Futurista
```html
<!-- Modal de confirmación de eliminación -->
<div id="futuristicModal" class="futuristic-modal">
  <div class="modal-content">
    <div class="glow-bg"></div>
    <div class="content">
      <div class="text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-red-600/20 to-pink-600/20 border border-red-400/40 flex items-center justify-center">
          <span class="text-red-400 text-2xl">⚠️</span>
        </div>
        <h3 class="text-xl font-bold text-gray-200 mb-2 modal-title">Confirmar Eliminación</h3>
        <p class="text-gray-400 mb-6 modal-message">¿Está seguro de que desea eliminar <span class="item-name text-red-400 font-semibold"></span>?</p>
        <div class="flex space-x-3">
          <button onclick="cerrarModal()" 
                  class="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-gray-600/20 to-gray-700/20 border border-gray-500/40 text-gray-300 hover:from-gray-500/30 hover:to-gray-600/30 transition-all duration-200 text-sm font-medium">
            Cancelar
          </button>
          <button class="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-red-600/20 to-pink-600/20 border border-red-400/40 text-red-300 hover:from-red-500/30 hover:to-pink-500/30 transition-all duration-200 text-sm font-medium delete-btn">
            Eliminar
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 8. JavaScript de Inicialización
```html
<script>
document.addEventListener('DOMContentLoaded', function() {
  // Inicializar búsqueda y filtros
  if (window.searchAndFilter) {
    window.searchAndFilter.init({
      searchInput: '#searchInput',
      searchBtn: '#searchBtn',
      filters: '.futuristic-filters select',
      items: '.futuristic-card'
    });
  }
  
  // Código específico del módulo aquí
});
</script>
```

## Templates a Actualizar

### 1. ✅ Completado
- `templates/taller/servicios/servicios_menu.html` (referencia)
- `templates/taller/clientes/lista_clientes.html` (actualizado)

### 2. Pendientes
- `templates/taller/vehiculos/lista_vehiculos.html`
- `templates/taller/repuestos/lista_repuestos.html`
- `templates/taller/documentos/lista_documentos.html`
- `templates/taller/reportes/reportes_menu.html`

## Clases CSS Disponibles

### Fondo Dinámico
- `.dynamic-background` - Contenedor principal
- `.space-background` - Fondo espacial
- `.stars`, `.twinkling`, `.clouds` - Efectos de fondo
- `.particles-container` - Contenedor de partículas

### Componentes
- `.futuristic-header` - Header con efectos
- `.futuristic-search` - Búsqueda con efectos
- `.futuristic-filters` - Filtros con efectos
- `.futuristic-card` - Tarjetas con efectos
- `.futuristic-btn` - Botones con efectos
- `.futuristic-modal` - Modal con efectos

### Utilidades
- `.text-gradient` - Texto con gradiente
- `.glow-text` - Texto con brillo
- `.animate-float` - Animación flotante
- `.animate-pulse-slow` - Pulso lento

## Funciones JavaScript Disponibles

### Globales
- `confirmarEliminacion(id, nombre, url)` - Confirmar eliminación
- `cerrarModal()` - Cerrar modal

### Clases
- `DynamicEffects` - Efectos dinámicos
- `SearchAndFilter` - Búsqueda y filtrado
- `FuturisticModal` - Sistema de modales

## Beneficios del Sistema Unificado

1. **Consistencia Visual** - Todos los módulos tienen el mismo look & feel
2. **Mantenibilidad** - Cambios centralizados en archivos CSS/JS
3. **Performance** - Efectos optimizados y reutilizables
4. **UX Mejorada** - Interacciones fluidas y efectos visuales atractivos
5. **Escalabilidad** - Fácil agregar nuevos módulos con el mismo estilo

## Estado del Proyecto

- ✅ Sistema base creado
- ✅ Template de clientes actualizado
- ⏳ Templates restantes pendientes
- ⏳ Documentación completa

## Próximos Pasos

1. Actualizar template de vehículos
2. Actualizar template de repuestos
3. Actualizar template de documentos
4. Actualizar template de reportes
5. Testing y optimización
6. Documentación final
