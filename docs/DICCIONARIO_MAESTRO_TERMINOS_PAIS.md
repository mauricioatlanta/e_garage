# 🌍 Diccionario Maestro de Términos por País

## Descripción

Sistema centralizado de etiquetas UI por país que respeta la terminología real de cada país en el rubro automotriz.

## Principios

- ✅ **NO se cambia el backend** (Documento)
- ✅ **Solo se cambian etiquetas de interfaz**
- ✅ **Cada país usa su terminología real** (como se habla en ese rubro)
- ✅ **Se respetan diferencias locales** (ej: folio, comprobante, OS)

## Países Soportados

| País | Código | Idioma | Ejemplo Término |
|------|--------|--------|-----------------|
| 🇺🇸 Estados Unidos | US | en | Invoice, Estimate, Work Order |
| 🇨🇱 Chile | CL | es | Documento, Presupuesto, Orden de Trabajo |
| 🇲🇽 México | MX | es | Documento, Cotización, Orden de Servicio, **Folio** |
| 🇵🇪 Perú | PE | es | **Comprobante**, Proforma, Orden de Servicio |
| 🇨🇴 Colombia | CO | es | Documento, Cotización, Orden de Trabajo |
| 🇦🇷 Argentina | AR | es | **Comprobante**, Presupuesto, Orden de Trabajo |
| 🇧🇷 Brasil | BR | pt | Documento, Orçamento, Ordem de Serviço, **Nota Fiscal** |
| 🇪🇨 Ecuador | EC | es | **Comprobante**, Proforma, Orden de Trabajo |
| 🇻🇪 Venezuela | VE | es | Documento, Presupuesto, Orden de Servicio, **N° Control** |
| 🇺🇾 Uruguay | UY | es | **Comprobante**, Presupuesto, Orden de Trabajo |

## Uso en Templates

### Acceso Directo a Variables

```django
<!-- Menú principal -->
{{ ui_documents_menu }}

<!-- Botón nuevo -->
{{ ui_new_document }}

<!-- Centro de documentos -->
{{ ui_document_center }}

<!-- Tipos de documento -->
{{ ui_document_type_invoice }}
{{ ui_document_type_estimate }}
{{ ui_document_type_work_order }}

<!-- Número de documento -->
{{ ui_document_number }}

<!-- Botones de acción -->
{{ ui_create_button }}
{{ ui_edit_button }}
```

### Acceso al Diccionario Completo

```django
<!-- Acceso directo al diccionario -->
{{ ui_labels.documents_menu }}
{{ ui_labels.document_number }}
{{ ui_labels.create_button }}
```

### Ejemplo Completo en Template

```django
<!-- Menú de navegación -->
<nav>
    <a href="{% url 'documentos:lista' %}">
        {{ ui_documents_menu }}
    </a>
</nav>

<!-- Botón crear nuevo documento -->
<a href="{% url 'documentos:crear' %}" class="btn btn-primary">
    {{ ui_new_document }}
</a>

<!-- Selector de tipo de documento -->
<select name="tipo">
    <option value="FAC">{{ ui_document_type_invoice }}</option>
    <option value="PRES">{{ ui_document_type_estimate }}</option>
    <option value="OT">{{ ui_document_type_work_order }}</option>
</select>

<!-- Label de número de documento -->
<label>{{ ui_document_number }}</label>
<input type="text" name="numero">

<!-- Botones de acción -->
<button type="submit">{{ ui_create_button }}</button>
<button type="button">{{ ui_edit_button }}</button>
```

## Uso en Python (Backend)

### Obtener Labels desde Código

```python
from taller.utils.ui_labels import get_ui_labels, get_label

# Obtener todas las labels para un país
labels = get_ui_labels('MX', 'es')
print(labels['documents_menu'])  # 'Documentos'
print(labels['document_number'])  # 'Folio'

# Obtener una label específica
folio_label = get_label('MX', 'es', 'document_number')
print(folio_label)  # 'Folio'

# Desde un request (en una vista)
def mi_vista(request):
    country_code = getattr(request, 'country', 'CL')
    language_code = getattr(request, 'LANGUAGE_CODE', 'es')
    labels = get_ui_labels(country_code, language_code)
    return render(request, 'template.html', {'labels': labels})
```

## Términos por País

### 🇺🇸 USA (Inglés)
- Menú: "Invoices"
- Nuevo: "New Invoice"
- Tipo Factura: "Invoice"
- Tipo Presupuesto: "Estimate"
- Tipo OT: "Work Order"
- Número: "Invoice Number"

### 🇨🇱 Chile (Español)
- Menú: "Documentos"
- Nuevo: "Nuevo Documento"
- Tipo Factura: "Factura"
- Tipo Presupuesto: "Presupuesto"
- Tipo OT: "Orden de Trabajo"
- Número: "N° Documento"

### 🇲🇽 México (Español)
- Menú: "Documentos"
- Nuevo: "Nuevo Documento"
- Tipo Factura: "Factura"
- Tipo Presupuesto: "Cotización"
- Tipo OT: "Orden de Servicio"
- Número: **"Folio"** ⭐

### 🇵🇪 Perú (Español)
- Menú: **"Comprobantes"** ⭐
- Nuevo: "Nuevo Comprobante"
- Tipo Factura: "Factura"
- Tipo Presupuesto: **"Proforma"** ⭐
- Tipo OT: "Orden de Servicio"
- Número: "N° Comprobante"

### 🇨🇴 Colombia (Español)
- Menú: "Documentos"
- Nuevo: "Nuevo Documento"
- Tipo Factura: "Factura"
- Tipo Presupuesto: "Cotización"
- Tipo OT: "Orden de Trabajo"
- Número: "N° Documento"

### 🇦🇷 Argentina (Español)
- Menú: **"Comprobantes"** ⭐
- Nuevo: "Nuevo Comprobante"
- Tipo Factura: "Factura"
- Tipo Presupuesto: "Presupuesto"
- Tipo OT: "Orden de Trabajo"
- Número: "N° Comprobante"

### 🇧🇷 Brasil (Portugués)
- Menú: "Documentos"
- Nuevo: "Novo Documento"
- Tipo Factura: **"Nota Fiscal"** ⭐
- Tipo Presupuesto: "Orçamento"
- Tipo OT: "Ordem de Serviço"
- Número: "Número do Documento"

### 🇪🇨 Ecuador (Español)
- Menú: **"Comprobantes"** ⭐
- Nuevo: "Nuevo Comprobante"
- Tipo Factura: "Factura"
- Tipo Presupuesto: **"Proforma"** ⭐
- Tipo OT: "Orden de Trabajo"
- Número: "N° Comprobante"

### 🇻🇪 Venezuela (Español)
- Menú: "Documentos"
- Nuevo: "Nuevo Documento"
- Tipo Factura: "Factura"
- Tipo Presupuesto: "Presupuesto"
- Tipo OT: "Orden de Servicio"
- Número: **"N° Control"** ⭐

### 🇺🇾 Uruguay (Español)
- Menú: **"Comprobantes"** ⭐
- Nuevo: "Nuevo Comprobante"
- Tipo Factura: "Factura"
- Tipo Presupuesto: "Presupuesto"
- Tipo OT: "Orden de Trabajo"
- Número: "N° Comprobante"

## Agregar Nuevos Términos

Para agregar nuevos términos al diccionario:

1. Editar `taller/utils/ui_labels.py`
2. Agregar la clave al diccionario de cada país
3. Actualizar el context processor si es necesario
4. Los cambios estarán disponibles automáticamente en todos los templates

Ejemplo:

```python
# En taller/utils/ui_labels.py
UI_LABELS_CL_ES = {
    # ... términos existentes ...
    "delete_button": "Eliminar Documento",  # Nuevo término
}

# En template
{{ ui_labels.delete_button }}
```

## Archivos Relacionados

- `taller/utils/ui_labels.py` - Diccionario maestro de términos
- `taller/context_processors/ui_labels.py` - Context processor para templates
- `taller/config/country_settings.py` - Configuración de países
- `taller/utils/country_config.py` - Utilidades de configuración por país

## Notas Técnicas

- El sistema detecta automáticamente el país desde el request (middleware)
- El idioma se detecta desde el request o desde la configuración del país
- Si no se encuentra un país/idioma específico, se usa Chile (español) como fallback
- Los labels están disponibles en todos los templates automáticamente
- No requiere cambios en el backend (modelos, vistas, etc.)

