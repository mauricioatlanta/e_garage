# Guía de Migración - Template document_form.html

## Paso 1: Agregar referencia al script modularizado

En el template `templates/taller/common/documentos/document_form.html`, en el bloque `{% block extra_js %}`:

```html
{% block extra_js %}
{{ block.super }}

{# NUEVO: Cargar módulos JavaScript modularizados #}
<script src="{% static 'js/document-form/index.js' %}"></script>

{% endblock extra_js %}
```

## Paso 2 (Opcional): Comentar código embebido gradualmente

El código embebido actual (~2000 líneas en `{% block extra_js %}` al final del template) se puede comentar gradualmente:

```html
{% block extra_js %}
{{ block.super }}

{# NUEVO: Cargar módulos JavaScript modularizados #}
<script src="{% static 'js/document-form/index.js' %}"></script>

{# CÓDIGO EMBEBIDO - Migrar gradualmente a módulos #}
<script>
// TODO: Eliminar después de migrar a document-form/index.js
(function(){
    'use strict';
    // ... código existente ...
})();
</script>

{% endblock extra_js %}
```

## Paso 3: Verificar que todo funciona

1. Verificar que los botones ADD funcionan
2. Verificar que la búsqueda de clientes funciona
3. Verificar que los totales se calculan
4. Verificar que el borrador se guarda

## Beneficios de la Migración

1. **Mantenibilidad**: Cada módulo tiene ~100-200 líneas vs ~2000 líneas
2. **Testabilidad**: Cada módulo se puede probar aisladamente
3. **Debugging**: Mejor trazabilidad de errores
4. **Reutilización**: Funciones como `EG.utils.egFetch` disponibles globalmente

## Rollback

Si algo falla, simplemente elimina la línea del script:

```html
{# Eliminar esta línea si hay problemas #}
<script src="{% static 'js/document-form/index.js' %}"></script>
```

El código embebido (sin comentar) seguirá funcionando como fallback.
