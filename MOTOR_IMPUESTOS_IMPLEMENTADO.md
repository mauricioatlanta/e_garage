# ✅ Motor de Cálculo de Impuestos - IMPLEMENTADO

## 📊 **CONVENCIONES RESPETADAS**

✅ **Chile: IVA 19% solo a repuestos** - no servicios  
✅ **USA: sales tax por ubicación** - estado/ciudad  
✅ **Brasil: ICMS 18% repuestos** - ISS servicios  
✅ **Perú: IGV 18% ambos** - repuestos y servicios  
✅ **Venezuela: IVA 16% ambos** - repuestos y servicios  
✅ **KPIs: solo fecha_emision** - optimizado  

---

## 🏗️ **ARQUITECTURA**

```
┌─────────────────────────────────────────────────────────┐
│              MOTOR DE IMPUESTOS                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  resolve_tax_rate(empresa, ciudad, tipo)                │
│      ↓                                                   │
│  1. TaxPolicy (ciudad específica)    [Prioridad 1]      │
│  2. TaxPolicy (estado)               [Prioridad 2]      │
│  3. TaxPolicy (país)                 [Prioridad 3]      │
│  4. Address.city.sales_tax_total     [Prioridad 4]      │
│  5. Hardcoded por país               [Fallback]         │
│      ↓                                                   │
│  Return: (tasa, es_inclusivo)                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 **ARCHIVOS CREADOS**

### **1. Motor de Impuestos:**
```
✅ taller/impuestos/__init__.py
✅ taller/impuestos/engine.py
   - resolve_tax_rate(empresa, ciudad, tipo)
   - get_tax_info(empresa, ciudad, tipo)
```

### **2. Servicios de Documentos:**
```
✅ taller/documentos/services.py
   - calcular_totales(documento)
   - recalcular_y_guardar(documento)
   - preview_totales(documento)
   - calcular_totales_con_descuento_global(documento, descuento)
```

---

## 🔧 **FUNCIÓN: resolve_tax_rate()**

### **Signatura:**
```python
def resolve_tax_rate(
    empresa,
    ship_to_city: Optional[Ciudad] = None,
    applies_to: str = 'parts'
) -> Tuple[Decimal, bool]:
```

### **Parámetros:**
- `empresa`: Instancia de Empresa (para obtener país)
- `ship_to_city`: Ciudad de destino (opcional, para sales tax por ubicación)
- `applies_to`: `'parts'` o `'services'`

### **Retorna:**
- `Tuple[Decimal, bool]`: (tasa, es_inclusivo)
  - `tasa`: Decimal (0.19 para 19%)
  - `es_inclusivo`: Boolean (True si impuesto incluido en precio)

---

### **Lógica de Prioridad:**

#### **1️⃣ TaxPolicy por Ciudad (más específico):**
```python
# Buscar política específica para Lima, Perú
policy = TaxPolicy.objects.get(
    country='PE',
    state_code='LIM',
    city_name='Lima',
    applies_to='parts'
)
# Retorna policy.rate si existe
```

#### **2️⃣ TaxPolicy por Estado:**
```python
# Buscar política para California, USA
policy = TaxPolicy.objects.get(
    country='US',
    state_code='CA',
    city_name='',  # Sin ciudad específica
    applies_to='both'
)
# Retorna policy.rate si existe
```

#### **3️⃣ TaxPolicy General del País:**
```python
# Buscar política general de Chile
policy = TaxPolicy.objects.get(
    country='CL',
    state_code='',
    city_name='',
    applies_to='parts'
)
# Retorna policy.rate = 0.19 (IVA 19%)
```

#### **4️⃣ Sales Tax desde Ciudad:**
```python
# Usar sales_tax_total de la ciudad
if ship_to_city:
    sales_tax = ship_to_city.sales_tax_total  # Estado + ciudad
    
    # CONVENCIÓN: Chile no cobra IVA en servicios
    if pais == 'CL' and applies_to == 'services':
        return (Decimal('0.00'), False)
    
    return (sales_tax / 100, False)
```

#### **5️⃣ Fallback Hardcoded:**
```python
DEFAULT_RATES = {
    'CL': {'parts': 0.19, 'services': 0.00},  # IVA 19% solo repuestos
    'US': {'parts': 0.00, 'services': 0.00},  # Varía por ubicación
    'BR': {'parts': 0.18, 'services': 0.00},  # ICMS 18% repuestos
    'PE': {'parts': 0.18, 'services': 0.18},  # IGV 18% ambos
    'VE': {'parts': 0.16, 'services': 0.16},  # IVA 16% ambos
}
```

---

## 📝 **EJEMPLOS DE USO**

### **Ejemplo 1: Cliente en Chile (repuestos)**

```python
from taller.impuestos.engine import resolve_tax_rate

empresa_chile = Empresa.objects.get(pais='CL')
ciudad_santiago = Ciudad.objects.get(nombre='Santiago', estado__pais='CL')

rate, inclusive = resolve_tax_rate(empresa_chile, ciudad_santiago, 'parts')

print(rate)       # Decimal('0.19')  ← IVA 19%
print(inclusive)  # False  ← No incluido en precio
```

---

### **Ejemplo 2: Cliente en Chile (servicios)**

```python
rate, inclusive = resolve_tax_rate(empresa_chile, ciudad_santiago, 'services')

print(rate)       # Decimal('0.00')  ← Sin IVA en servicios ✅
print(inclusive)  # False
```

**CONVENCIÓN RESPETADA:** Chile no cobra IVA en servicios ✅

---

### **Ejemplo 3: Cliente en Perú**

```python
empresa_peru = Empresa.objects.get(pais='PE')
ciudad_lima = Ciudad.objects.get(nombre='Lima', estado__pais='PE')

# Repuestos
rate_parts, _ = resolve_tax_rate(empresa_peru, ciudad_lima, 'parts')
print(rate_parts)  # Decimal('0.18')  ← IGV 18%

# Servicios
rate_services, _ = resolve_tax_rate(empresa_peru, ciudad_lima, 'services')
print(rate_services)  # Decimal('0.18')  ← IGV 18% también en servicios
```

---

### **Ejemplo 4: Calcular Totales de Documento**

```python
from taller.documentos.services import calcular_totales

# Documento con líneas
documento = Documento.objects.get(pk=1)

# Líneas:
# - 1x Aceite 5W30: $20,000 (repuesto)
# - 1x Cambio de Aceite: $15,000 (servicio)

# Calcular (empresa Chile, cliente Santiago)
calcular_totales(documento)

print(documento.subtotal_repuestos)  # 20,000
print(documento.subtotal_servicios)  # 15,000
print(documento.iva_repuestos)       # 3,800 (20,000 * 0.19)
print(documento.iva_servicios)       # 0 (servicios sin IVA en Chile) ✅
print(documento.total)               # 38,800
```

**CONVENCIÓN RESPETADA:** IVA solo en repuestos ✅

---

### **Ejemplo 5: Preview sin Guardar**

```python
from taller.documentos.services import preview_totales

# Preview antes de emitir
totales = preview_totales(documento)

print(totales['subtotal_parts'])      # 20,000
print(totales['tax_parts'])           # 3,800
print(totales['total'])               # 38,800
print(totales['tax_info_parts'])      # {'name': 'IVA', 'rate_percentage': 19.0, ...}
```

---

### **Ejemplo 6: Recalcular y Guardar**

```python
from taller.documentos.services import recalcular_y_guardar

# Agregar nueva línea
LineaRepuesto.objects.create(
    documento=documento,
    nombre='Filtro de Aceite',
    cantidad=1,
    precio_unitario=5000
)

# Recalcular automáticamente
recalcular_y_guardar(documento)

print(documento.total)  # Total actualizado
```

---

### **Ejemplo 7: Descuento Global**

```python
from taller.documentos.services import calcular_totales_con_descuento_global

# Aplicar 10% de descuento global
calcular_totales_con_descuento_global(documento, Decimal('10.00'))

# Subtotal original: 35,000
# Descuento 10%: -3,500
# Subtotal con descuento: 31,500
# IVA 19% sobre 31,500: 5,985
# Total: 37,485
```

---

## 📊 **TABLA DE IMPUESTOS POR PAÍS**

### **🇨🇱 Chile:**
| Tipo | Tasa | Nombre | Aplica a |
|------|------|--------|----------|
| Repuestos | 19% | IVA | ✅ Parts only |
| Servicios | 0% | -- | ❌ No aplica |

**Ejemplo:**
```
Repuesto: $20,000 + IVA 19% = $23,800
Servicio: $15,000 + IVA 0% = $15,000
Total: $38,800
```

---

### **🇺🇸 USA:**
| Tipo | Tasa | Nombre | Aplica a |
|------|------|--------|----------|
| Variable | 0-10% | Sales Tax | Estado/Ciudad |

**Ejemplo (California 7.25%):**
```
Repuesto: $100 + Sales Tax 7.25% = $107.25
Servicio: $80 + Sales Tax 7.25% = $85.80
Total: $193.05
```

---

### **🇧🇷 Brasil:**
| Tipo | Tasa | Nombre | Aplica a |
|------|------|--------|----------|
| Repuestos | 18% | ICMS | ✅ Parts |
| Servicios | 0%* | ISS | Simplificado |

*ISS puede configurarse por ciudad si se necesita

---

### **🇵🇪 Perú:**
| Tipo | Tasa | Nombre | Aplica a |
|------|------|--------|----------|
| Ambos | 18% | IGV | ✅ Parts + Services |

**Ejemplo:**
```
Repuesto: S/ 70 + IGV 18% = S/ 82.60
Servicio: S/ 50 + IGV 18% = S/ 59.00
Total: S/ 141.60
```

---

### **🇻🇪 Venezuela:**
| Tipo | Tasa | Nombre | Aplica a |
|------|------|--------|----------|
| Ambos | 16% | IVA | ✅ Parts + Services |

**Ejemplo:**
```
Repuesto: Bs. 730 + IVA 16% = Bs. 846.80
Servicio: Bs. 500 + IVA 16% = Bs. 580.00
Total: Bs. 1,426.80
```

---

## 🔄 **FLUJO DE CÁLCULO**

### **Paso a Paso:**

```
1. Crear Documento
   └── documento = Documento.objects.create(...)

2. Agregar Líneas
   ├── LineaRepuesto.objects.create(documento=doc, ...)
   └── LineaServicio.objects.create(documento=doc, ...)

3. Calcular Totales
   └── calcular_totales(documento)
       ├── Suma repuestos → subtotal_repuestos
       ├── Suma servicios → subtotal_servicios
       ├── Detecta ciudad → billing_address.city
       ├── Resuelve tax rate repuestos → 19% (Chile)
       ├── Resuelve tax rate servicios → 0% (Chile)
       ├── Calcula IVA repuestos → subtotal * 0.19
       ├── Calcula IVA servicios → subtotal * 0.00
       └── Total = subtotales + impuestos

4. Guardar
   └── documento.save()
```

---

## 📝 **INTEGRACIÓN EN VISTAS**

### **Vista de Creación de Documento:**

```python
from taller.documentos.services import calcular_totales

def crear_documento(request):
    if request.method == 'POST':
        # Crear documento
        documento = Documento.objects.create(
            empresa=request.user.empresa,
            cliente=cliente,
            tipo='ORDEN_TRABAJO',
            estado='DRAFT'
        )
        
        # Agregar líneas (desde formset o API)
        for linea_data in lineas_repuestos:
            LineaRepuesto.objects.create(
                documento=documento,
                **linea_data
            )
        
        # CALCULAR TOTALES CON IMPUESTOS
        calcular_totales(documento)
        documento.save()
        
        return redirect('documentos:detalle', pk=documento.pk)
```

---

### **Vista de Edición de Documento:**

```python
from taller.documentos.services import recalcular_y_guardar

def editar_documento(request, pk):
    documento = get_object_or_404(Documento, pk=pk, estado='DRAFT')
    
    if request.method == 'POST':
        # Actualizar líneas...
        
        # RECALCULAR Y GUARDAR
        recalcular_y_guardar(documento)
        
        return redirect('documentos:detalle', pk=pk)
```

---

### **API de Preview:**

```python
from taller.documentos.services import preview_totales
from rest_framework.decorators import api_view

@api_view(['POST'])
def preview_documento_totales(request):
    """
    API para calcular totales sin guardar (preview).
    
    POST /api/documentos/preview-totales/
    {
        "lineas_repuestos": [...],
        "lineas_servicios": [...],
        "cliente_id": 123
    }
    """
    # Crear documento temporal (no guardar)
    documento = Documento(
        empresa=request.user.empresa,
        cliente_id=request.data.get('cliente_id')
    )
    
    # Agregar líneas temporales...
    
    # Calcular sin guardar
    totales = preview_totales(documento)
    
    return Response({
        'subtotal': str(totales['subtotal']),
        'tax_total': str(totales['tax_total']),
        'total': str(totales['total']),
        'tax_info': totales['tax_info_parts']
    })
```

---

## 🎯 **CASOS DE USO POR PAÍS**

### **🇨🇱 Chile - IVA 19% Solo Repuestos:**

```python
# Documento en Chile
doc = Documento.objects.get(pk=1)
doc.empresa.pais  # 'CL'

# Líneas:
# - Aceite: $20,000 (repuesto)
# - Cambio de Aceite: $15,000 (servicio)

calcular_totales(doc)

# Resultados:
doc.subtotal_repuestos  # 20,000
doc.subtotal_servicios  # 15,000
doc.iva_repuestos       # 3,800 (20,000 * 0.19) ✅
doc.iva_servicios       # 0 (servicios sin IVA) ✅
doc.total               # 38,800
```

**✅ CONVENCIÓN RESPETADA:** IVA solo en repuestos

---

### **🇺🇸 USA - Sales Tax por Ubicación:**

```python
# Documento en USA, cliente en California
doc = Documento.objects.get(pk=2)
doc.empresa.pais  # 'US'
doc.cliente.billing_address.city.estado.codigo  # 'CA'

# TaxPolicy para California
# TaxPolicy.objects.get(country='US', state_code='CA', applies_to='both', rate=0.0725)

# Líneas:
# - Brake Pads: $100 (repuesto)
# - Brake Service: $80 (servicio)

calcular_totales(doc)

# Resultados:
doc.subtotal_repuestos  # 100
doc.subtotal_servicios  # 80
doc.iva_repuestos       # 7.25 (100 * 0.0725)
doc.iva_servicios       # 5.80 (80 * 0.0725)
doc.total               # 193.05
```

**✅ CONVENCIÓN RESPETADA:** Sales tax por ubicación

---

### **🇵🇪 Perú - IGV 18% Ambos:**

```python
# Documento en Perú
doc = Documento.objects.get(pk=3)
doc.empresa.pais  # 'PE'

# Líneas:
# - Aceite: S/ 70 (repuesto)
# - Cambio de Aceite: S/ 50 (servicio)

calcular_totales(doc)

# Resultados:
doc.subtotal_repuestos  # 70
doc.subtotal_servicios  # 50
doc.iva_repuestos       # 12.60 (70 * 0.18)
doc.iva_servicios       # 9.00 (50 * 0.18) ✅
doc.total               # 141.60
```

**✅ IGV aplicado a ambos**

---

## 🔍 **TESTING**

### **Test Unitario:**

```python
# tests/test_impuestos.py
from decimal import Decimal
from django.test import TestCase
from taller.impuestos.engine import resolve_tax_rate
from taller.models import Empresa, Estado, Ciudad

class TaxEngineTestCase(TestCase):
    def test_chile_iva_solo_repuestos(self):
        """Chile: IVA 19% solo en repuestos, 0% en servicios"""
        empresa = Empresa.objects.create(nombre='Test CL', pais='CL')
        
        # Repuestos
        rate, _ = resolve_tax_rate(empresa, None, 'parts')
        self.assertEqual(rate, Decimal('0.19'))
        
        # Servicios
        rate, _ = resolve_tax_rate(empresa, None, 'services')
        self.assertEqual(rate, Decimal('0.00'))  # ✅
    
    def test_peru_igv_ambos(self):
        """Perú: IGV 18% en repuestos y servicios"""
        empresa = Empresa.objects.create(nombre='Test PE', pais='PE')
        
        rate_parts, _ = resolve_tax_rate(empresa, None, 'parts')
        rate_services, _ = resolve_tax_rate(empresa, None, 'services')
        
        self.assertEqual(rate_parts, Decimal('0.18'))
        self.assertEqual(rate_services, Decimal('0.18'))  # ✅
```

---

### **Test de Integración:**

```python
def test_calcular_totales_documento_chile(self):
    """Test completo de cálculo de totales en Chile"""
    from taller.documentos.services import calcular_totales
    
    # Crear documento
    doc = Documento.objects.create(
        empresa=empresa_chile,
        cliente=cliente_chile
    )
    
    # Agregar líneas
    LineaRepuesto.objects.create(
        documento=doc,
        nombre='Aceite',
        cantidad=1,
        precio_unitario=20000
    )
    LineaServicio.objects.create(
        documento=doc,
        nombre='Cambio de Aceite',
        cantidad=1,
        precio_unitario=15000
    )
    
    # Calcular
    calcular_totales(doc)
    
    # Verificar
    self.assertEqual(doc.subtotal_repuestos, Decimal('20000'))
    self.assertEqual(doc.subtotal_servicios, Decimal('15000'))
    self.assertEqual(doc.iva_repuestos, Decimal('3800'))
    self.assertEqual(doc.iva_servicios, Decimal('0'))  # ✅
    self.assertEqual(doc.total, Decimal('38800'))
```

---

## 📋 **INTEGRACIÓN CON MODELO DOCUMENTO**

### **Campos Necesarios en Documento:**

```python
class Documento(models.Model):
    # ... campos existentes ...
    
    # Subtotales por tipo
    subtotal_repuestos = DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal_servicios = DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Impuestos por tipo
    iva_repuestos = DecimalField(max_digits=12, decimal_places=2, default=0)
    iva_servicios = DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Total final
    total = DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Campos opcionales
    subtotal = DecimalField(...)  # subtotal_repuestos + subtotal_servicios
    impuesto_total = DecimalField(...)  # iva_repuestos + iva_servicios
    tasa_impuesto_repuestos = DecimalField(...)  # Para referencia
    tasa_impuesto_servicios = DecimalField(...)  # Para referencia
```

---

### **Llamar calcular_totales() antes de Emitir:**

```python
# En view o API
def emitir_documento(request, pk):
    documento = get_object_or_404(Documento, pk=pk, estado='DRAFT')
    
    # 1. Validar que tenga líneas
    if not documento.lineas_repuesto.exists() and not documento.lineas_servicio.exists():
        messages.error(request, 'El documento debe tener al menos una línea')
        return redirect('documentos:editar', pk=pk)
    
    # 2. CALCULAR TOTALES CON IMPUESTOS
    calcular_totales(documento)
    
    # 3. Cambiar estado a emitido
    documento.estado = 'EMITIDO'
    documento.fecha_emision = timezone.now()
    
    # 4. Guardar
    documento.save()
    
    messages.success(request, f'Documento {documento.numero} emitido exitosamente')
    return redirect('documentos:detalle', pk=pk)
```

---

## 🎨 **DISPLAY EN TEMPLATES**

### **Mostrar Totales con Desglose:**

```html
{% load humanize %}

<div class="totales-documento">
  <h4>Totales</h4>
  
  <!-- Repuestos -->
  <div class="row">
    <div class="col-8">Subtotal Repuestos:</div>
    <div class="col-4 text-right">
      {{ documento.subtotal_repuestos|floatformat:2|intcomma }}
    </div>
  </div>
  
  {% if documento.iva_repuestos > 0 %}
  <div class="row">
    <div class="col-8">
      IVA Repuestos ({{ tasa_iva_repuestos }}%):
    </div>
    <div class="col-4 text-right">
      {{ documento.iva_repuestos|floatformat:2|intcomma }}
    </div>
  </div>
  {% endif %}
  
  <!-- Servicios -->
  <div class="row">
    <div class="col-8">Subtotal Servicios:</div>
    <div class="col-4 text-right">
      {{ documento.subtotal_servicios|floatformat:2|intcomma }}
    </div>
  </div>
  
  {% if documento.iva_servicios > 0 %}
  <div class="row">
    <div class="col-8">
      IVA Servicios ({{ tasa_iva_servicios }}%):
    </div>
    <div class="col-4 text-right">
      {{ documento.iva_servicios|floatformat:2|intcomma }}
    </div>
  </div>
  {% endif %}
  
  <!-- Total -->
  <div class="row total-final">
    <div class="col-8"><strong>TOTAL:</strong></div>
    <div class="col-4 text-right">
      <strong>{{ documento.total|floatformat:2|intcomma }}</strong>
    </div>
  </div>
</div>
```

---

## ⚙️ **CONFIGURACIÓN DE POLÍTICAS**

### **Crear Políticas Personalizadas:**

```python
from taller.models import TaxPolicy

# Política para ciudad específica (ej: San Francisco con tax más alto)
TaxPolicy.objects.create(
    country='US',
    state_code='CA',
    city_name='San Francisco',
    applies_to='both',
    rate=Decimal('0.0850'),  # 8.5%
    inclusive=False,
    active=True
)

# Política general para estado
TaxPolicy.objects.create(
    country='US',
    state_code='CA',
    city_name='',  # Aplica a todas las ciudades de CA
    applies_to='both',
    rate=Decimal('0.0725'),  # 7.25%
    inclusive=False,
    active=True
)
```

**Prioridad:** La política de San Francisco (más específica) tiene prioridad sobre la de California (general).

---

## 🔍 **DEBUGGING**

### **Verificar qué política se está usando:**

```python
from taller.impuestos.engine import get_tax_info

# Obtener info detallada
info = get_tax_info(empresa_chile, ciudad_santiago, 'parts')

print(info)
# {
#     'rate': Decimal('0.19'),
#     'rate_percentage': 19.0,
#     'inclusive': False,
#     'name': 'IVA',
#     'country': 'CL',
#     'state': 'Región Metropolitana',
#     'city': 'Santiago'
# }
```

---

### **Verificar cálculos paso a paso:**

```python
# En view con debug
from taller.documentos.services import preview_totales

totales = preview_totales(documento)

print("Subtotal repuestos:", totales['subtotal_parts'])
print("Subtotal servicios:", totales['subtotal_services'])
print("Tax repuestos:", totales['tax_parts'])
print("Tax servicios:", totales['tax_services'])
print("Total:", totales['total'])
print("Tax info parts:", totales['tax_info_parts'])
print("Tax info services:", totales['tax_info_services'])
```

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

### **Backend:**
- [✅] Motor de impuestos (`impuestos/engine.py`)
- [✅] Servicios de documentos (`documentos/services.py`)
- [✅] Función `resolve_tax_rate()`
- [✅] Función `get_tax_info()`
- [✅] Función `calcular_totales()`
- [✅] Función `preview_totales()`
- [✅] Función `calcular_totales_con_descuento_global()`

### **Lógica de Negocio:**
- [✅] Chile: IVA 19% solo repuestos ✅
- [✅] Chile: Servicios sin IVA (0%) ✅
- [✅] USA: Sales tax por ubicación
- [✅] Brasil: ICMS 18% repuestos
- [✅] Perú: IGV 18% ambos
- [✅] Venezuela: IVA 16% ambos

### **Prioridades:**
- [✅] TaxPolicy ciudad > estado > país
- [✅] Fallback a política país (TaxPolicy sin estado/ciudad)
- [✅] Fallback hardcoded por país

### **Integración:**
- [⚠️] Agregar campos al modelo Documento (si no existen)
- [⚠️] Llamar calcular_totales() antes de emitir
- [⚠️] Actualizar vistas de creación/edición
- [⚠️] Actualizar templates para mostrar desglose

---

## 📚 **REFERENCIAS**

- **Motor:** `taller/impuestos/engine.py`
- **Servicios:** `taller/documentos/services.py`
- **Políticas:** `taller/models/catalogo_repuestos.py` (TaxPolicy)
- **Address:** `ubicacion/models.py`

---

## 🎉 **RESUMEN**

✅ **Motor de impuestos implementado** con lógica multi-país  
✅ **Convenciones respetadas al 100%**  
✅ **Prioridades correctas** (ciudad > estado > país)  
✅ **3 funciones principales** (resolve, calcular, preview)  
✅ **Fallbacks robustos** (TaxPolicy → Address → Hardcoded)  
✅ **Ejemplos completos** por país  
✅ **Testing sugerido** incluido  

**Siguiente paso:** Integrar en vistas de documentos existentes

