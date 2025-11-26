# 🔗 Integración Alpine.js + Django: Guía Completa

## 📋 Resumen

Esta guía muestra cómo integrar el formulario de documentos con Alpine.js en el frontend y Django en el backend, siguiendo las reglas de negocio de eGarage.

## 🎯 Arquitectura

```
Frontend (Alpine.js)          Backend (Django)
┌─────────────────┐          ┌─────────────────┐
│  Formulario     │          │  DocumentoForm  │
│  - Cliente      │─────────>│  - Validación   │
│  - Vehículo     │          │  - Cabecera     │
│                 │          └─────────────────┘
│  Tabla          │          
│  - Repuestos    │─────────>│  Procesar JSON  │
│  - Servicios    │          │  - LineaRepuesto│
│                 │          │  - LineaServicio│
│  Totales        │          │                 │
│  (Reactivos)    │<─────────│  recompute_     │
└─────────────────┘          │  totals()       │
                             └─────────────────┘
```

## 📁 Archivos Creados

### 1. Template HTML
**Archivo**: `templates/taller/common/documentos/document_form_alpine_example.html`

- ✅ Extiende `base.html`
- ✅ Integra Alpine.js desde CDN
- ✅ Formulario Django para cabeceras
- ✅ Tablas reactivas para repuestos/servicios
- ✅ Cálculos automáticos (totales, impuestos)
- ✅ Sincronización Alpine.js → Django via inputs ocultos

### 2. Vistas Django
**Archivo**: `taller/documentos/views_alpine.py`

- ✅ `crear_documento_alpine()` - Crear nuevos documentos
- ✅ `editar_documento_alpine()` - Editar documentos existentes
- ✅ Procesa JSON de Alpine.js
- ✅ Multi-tenant seguro (filtro por empresa)
- ✅ Calcula totales automáticamente

## 🔧 Configuración

### 1. Agregar URLs

```python
# taller/documentos/urls.py

from django.urls import path
from taller.documentos.views_alpine import (
    crear_documento_alpine, 
    editar_documento_alpine
)

urlpatterns = [
    # ... otras URLs
    path('crear/alpine/', crear_documento_alpine, name='crear_alpine'),
    path('editar/<int:documento_id>/alpine/', editar_documento_alpine, name='editar_alpine'),
]
```

### 2. Agregar Alpine.js al Base Template

```html
<!-- templates/base.html -->

{% block extra_head %}
    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
{% endblock %}
```

### 3. Incluir Widget Tweaks (si no lo tienes)

```bash
pip install django-widget-tweaks
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'widget_tweaks',
]
```

## 🎨 Reglas de Negocio Implementadas

### 1. Impuestos por País

**Chile (CL):**
- ✅ IVA 19% solo sobre repuestos
- ✅ Sin impuesto sobre servicios
- ✅ 0 decimales en formato de moneda

**USA (US):**
- ✅ Impuesto sobre repuestos + servicios (si `apply_vat=True`)
- ✅ Tasa configurable (por defecto 0%)
- ✅ 2 decimales en formato de moneda

```javascript
// Frontend (Alpine.js)
get montoImpuesto() {
    let baseImponible = 0;
    
    if (this.country === 'CL') {
        // Chile: IVA solo sobre repuestos
        baseImponible = this.netoRepuestos; 
    } else {
        // USA: Impuesto sobre repuestos + servicios
        baseImponible = this.netoRepuestos + this.netoServicios; 
    }
    
    return baseImponible * (this.taxRate / 100);
}
```

```python
# Backend (Django)
def recompute_totals(self, persist=False):
    # ... cálculos ...
    if pais == "CL":
        tax_base = rep  # IVA solo a repuestos
    else:  # US
        if getattr(self, "apply_vat", True):
            tax_base = rep + srv  # Repuestos + servicios
        else:
            tax_base = Decimal("0")
```

### 2. Formato de Moneda

```javascript
// Frontend
formatMoney(value) {
    const currency = this.country === 'CL' ? 'CLP' : 'USD';
    const locale = this.country === 'CL' ? 'es-CL' : 'en-US';
    const decimals = this.country === 'CL' ? 0 : 2; // ✅ CL: 0 decimales, US: 2
    
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value || 0);
}
```

### 3. Cálculo de Líneas

```javascript
// Frontend: Calcula subtotal con descuento porcentual
calcularLinea(item) {
    const cantidad = parseFloat(item.cantidad) || 0;
    const precio = parseFloat(item.precio) || 0;
    const descuento = parseFloat(item.descuento) || 0;
    
    const subtotal = cantidad * precio;
    const descuentoValor = subtotal * (descuento / 100);
    return Math.max(0, subtotal - descuentoValor);
}
```

```python
# Backend: Misma lógica en ORM
def _sum_repuesto(self):
    expr = ExpressionWrapper(
        F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    total = qs.aggregate(s=Sum(expr)).get("s") or Decimal("0")
    return Decimal(total)
```

## 🔒 Seguridad Multi-Tenant

### Frontend (Alpine.js)
- ✅ País y tasa inyectados desde Django (no manipulables)
- ✅ Datos solo se envían al servidor (no lógica sensible)

### Backend (Django)
- ✅ Filtro obligatorio por `empresa=request.user.empresa`
- ✅ Asignación automática de empresa en `save(commit=False)`
- ✅ Validación en `clean()` asegura consistencia

```python
# Multi-tenant seguro
doc = form.save(commit=False)
doc.empresa = empresa  # 🔒 Siempre asignar empresa del usuario
doc.save()
```

## 📊 Flujo de Datos

### 1. Cargar Página (GET)

```
Usuario → Vista Django → Template → Alpine.js
                                    ↓
                            Cargar datos iniciales
                            (vacío para nuevo,
                             JSON para editar)
```

### 2. Agregar Líneas (Frontend)

```
Usuario escribe → Alpine.js detecta cambio
                    ↓
            Recalcula subtotales
                    ↓
            Actualiza UI automáticamente
```

### 3. Guardar Documento (POST)

```
Usuario envía formulario
        ↓
Alpine.js serializa datos:
- Cabeceras → Formulario Django
- Repuestos → JSON en input oculto
- Servicios → JSON en input oculto
        ↓
Django procesa:
1. Valida formulario
2. Guarda cabecera
3. Procesa JSON → Crea líneas
4. Calcula totales (recompute_totals)
5. Guarda documento completo
```

## ✅ Ventajas vs Formsets Tradicionales

| Aspecto | Formsets Django | Alpine.js + JSON |
|---------|----------------|------------------|
| **UX** | Recarga página al agregar líneas | Sin recarga, reactivo |
| **Código** | ~200 líneas | ~100 líneas |
| **Validación** | Compleja (TOTAL_FORMS, etc.) | Simple (JSON) |
| **Rendimiento** | Más lento (muchas consultas) | Más rápido (bulk_create) |
| **Mantenibilidad** | Media | Alta |
| **Multi-tenant** | Requiere cuidado manual | Integrado automáticamente |

## 🚀 Próximos Pasos

1. **Autocomplete de Repuestos**
   - Implementar búsqueda con HTMX o fetch
   - Cargar precio automáticamente

2. **Validación Avanzada**
   - Validar que hay al menos una línea
   - Validar precios > 0

3. **Edición Inline**
   - Permitir editar líneas sin recargar

4. **Guardado Automático**
   - Auto-guardar borradores cada X segundos

## 📝 Notas Importantes

1. **Alpine.js desde CDN**: Para producción, considera usar bundle local
2. **CSRF Token**: Ya incluido en el formulario
3. **Decimales**: CL usa 0, US usa 2 (implementado correctamente)
4. **Bulk Create**: Crea todas las líneas de una vez (más eficiente)

## ✅ Checklist de Implementación

- [x] Template HTML con Alpine.js
- [x] Vista para crear documentos
- [x] Vista para editar documentos
- [x] Procesamiento de JSON
- [x] Cálculo de totales
- [x] Multi-tenant seguro
- [x] Formato de moneda por país
- [x] Reglas de impuestos (CL/US)
- [ ] Autocomplete de repuestos
- [ ] Validación avanzada
- [ ] Pruebas unitarias

¡Listo para usar! 🎉

