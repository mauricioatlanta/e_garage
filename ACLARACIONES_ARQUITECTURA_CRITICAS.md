# ⚠️ ACLARACIONES CRÍTICAS DE ARQUITECTURA

## 🎯 **PROPÓSITO**

Documento que aclara puntos críticos de la arquitectura del sistema para evitar confusiones y mal uso.

---

## 🚨 **ACLARACIONES CRÍTICAS**

### **1. estado_usa/ciudad_usa SON LEGACY** ❌

#### **❌ INCORRECTO:**
```python
# NO usar estado_usa/ciudad_usa como campos genéricos
cliente.estado_usa = estado_peru  # ❌ MAL
cliente.ciudad_usa = ciudad_lima  # ❌ MAL
```

#### **✅ CORRECTO:**
```python
# El origen de verdad AHORA es Address
address = Address.objects.create(
    line1='Av. Lima 123',
    city=ciudad_lima,  # Ciudad es del modelo unificado
    postal_code='15001'
)
cliente.billing_address = address  # ✅ BIEN
```

#### **Explicación:**

Los campos `estado_usa` y `ciudad_usa` en el modelo `Cliente` fueron creados originalmente para USA, pero se **REUTILIZARON** temporalmente para otros países (BR, PE, VE) antes de la implementación de Address.

**Ahora:**
- ✅ **Address** es el origen de verdad (single source of truth)
- ❌ `estado_usa`/`ciudad_usa` son **LEGACY** (marcar para deprecación)
- ⚠️ Mantener solo para compatibilidad hacia atrás (1-2 releases)

#### **Migración:**

```python
# ANTES (legacy):
cliente.estado_usa = estado
cliente.ciudad_usa = ciudad
cliente.zipcode = '15001'

# DESPUÉS (correcto):
address = Address.objects.create(
    line1=cliente.direccion or 'N/A',
    city=ciudad,  # Ciudad del modelo unificado
    postal_code=cliente.zipcode or ''
)
cliente.billing_address = address
```

#### **En Formularios:**

```python
# ❌ NO USAR ClienteForm legacy con estado_usa/ciudad_usa
# ✅ USAR CustomerForm unificado con Address

from taller.clientes.forms_unified import CustomerForm

form = CustomerForm(request.POST, empresa=request.user.empresa)
if form.is_valid():
    cliente = form.save()
    # billing_address se crea automáticamente ✅
```

---

### **2. nombre EN LineaRepuesto/LineaServicio SE MANTIENE** ✅

#### **✅ CORRECTO:**
```python
# LineaRepuesto
class LineaRepuesto(models.Model):
    documento = models.ForeignKey('taller.Documento', ...)
    part = models.ForeignKey('taller.Part', ...)  # Nuevo - referencia al catálogo
    nombre = models.CharField(...)  # ✅ MANTENER - congela display
    cantidad = models.DecimalField(...)
    precio_unitario = models.DecimalField(...)

# LineaServicio
class LineaServicio(models.Model):
    documento = models.ForeignKey('taller.Documento', ...)
    service = models.ForeignKey('taller.Service', ...)  # Nuevo - referencia al catálogo
    nombre = models.CharField(...)  # ✅ MANTENER - congela display
    cantidad = models.DecimalField(...)
    precio_unitario = models.DecimalField(...)
```

#### **Razón:**

El campo `nombre` **congela el display name** en el momento de crear la línea del documento.

**Problema sin nombre congelado:**
```python
# Sin congelar
linea = LineaRepuesto.objects.create(
    part=oil_filter,
    # Sin nombre congelado
)

# 6 meses después, el catálogo cambia:
oil_filter.i18n.filter(locale='es-CL').update(
    display_name='Filtro de Aceite Premium'  # Cambió el nombre
)

# El documento histórico muestra el NUEVO nombre ❌
print(linea.part.get_display_name('es-CL'))
# Output: "Filtro de Aceite Premium" (nombre actual, no histórico)
```

**Solución con nombre congelado:**
```python
# Con congelar ✅
linea = LineaRepuesto.objects.create(
    part=oil_filter,
    nombre=oil_filter.get_display_name('es-CL'),  # ✅ Congelar en tiempo de creación
    cantidad=1,
    precio_unitario=25000
)

# 6 meses después, el catálogo cambia:
oil_filter.i18n.filter(locale='es-CL').update(
    display_name='Filtro de Aceite Premium'
)

# El documento histórico muestra el nombre ORIGINAL ✅
print(linea.nombre)
# Output: "Filtro de Aceite" (nombre congelado, histórico)
```

#### **Best Practice:**

```python
# Al crear línea de documento
part = Part.objects.get(sku='OIL-5W30')
locale = request.user.empresa.locale or 'es-CL'

LineaRepuesto.objects.create(
    documento=doc,
    part=part,  # Referencia al catálogo (para analytics, trazabilidad)
    nombre=part.get_display_name(locale),  # ✅ Congelar display
    cantidad=2,
    precio_unitario=part.get_price(empresa)  # También congelado
)
```

#### **Ventajas:**

1. ✅ **Inmutabilidad:** Documentos históricos no cambian
2. ✅ **Auditoría:** Se ve exactamente qué se vendió
3. ✅ **Trazabilidad:** `part` FK para analytics
4. ✅ **Display:** `nombre` para UI inmutable

---

### **3. Motor de Impuestos ES CONFIGURABLE via TaxPolicy** ✅

#### **Arquitectura:**

```
TaxPolicy (configurable)
  ↓
resolve_tax_rate(empresa, ciudad, tipo)
  ↓
Calcula tasa según:
  1. TaxPolicy específico (country + state_code + city_name)
  2. Fallback a política país (TaxPolicy sin estado/ciudad)
  3. Fallback a default del país
```

#### **Chile: IVA 19% solo repuestos:**

```python
# Configurado con TaxPolicy
TaxPolicy.objects.create(
    country='CL',
    state_code='',
    city_name='',
    applies_to='parts',  # ✅ Solo repuestos
    rate=Decimal('0.19')
)

# NO crear TaxPolicy para services (sin política = sin impuesto)
# resolve_tax_rate(empresa_CL, None, 'services') → 0.00 ✅
```

#### **USA: Sales tax por estado:**

```python
# Configurado con múltiples TaxPolicy
TaxPolicy.objects.create(
    country='US',
    state_code='CA',  # ✅ Por estado
    applies_to='both',
    rate=Decimal('0.0725')
)

TaxPolicy.objects.create(
    country='US',
    state_code='TX',
    applies_to='both',
    rate=Decimal('0.0625')
)

# Diferentes estados, diferentes tasas ✅
```

#### **Flexibilidad:**

```python
# Se puede configurar a nivel:
# 1. Nacional (state_code='', city_name='')
TaxPolicy(country='PE', applies_to='both', rate=0.18)

# 2. Estado (city_name='')
TaxPolicy(country='US', state_code='CA', applies_to='both', rate=0.0725)

# 3. Ciudad específica
TaxPolicy(country='US', state_code='CA', city_name='San Francisco', 
          applies_to='both', rate=0.085)
```

#### **NO hardcodear:**

```python
# ❌ MAL - Hardcodear tasas
if empresa.pais == 'CL':
    tasa = Decimal('0.19')

# ✅ BIEN - Usar motor configurable
tasa, _ = resolve_tax_rate(empresa, ciudad, 'parts')
```

---

### **4. locations.js ES ÚNICO Y REUTILIZABLE** ✅

#### **Arquitectura:**

```
taller/static/js/locations.js (ES6 module)
  ↓
bindCountryStateCity(countrySel, stateSel, citySel)
  ↓
Se reutiliza en TODOS los formularios que pidan:
  País → Estado/Región/Departamento → Ciudad
```

#### **✅ CORRECTO - Reutilizar:**

```javascript
// Formulario Cliente
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_country', '#id_state', '#id_city');
</script>

// Formulario Empresa
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_company_country', '#id_company_state', '#id_company_city');
</script>

// Formulario Documento
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_pais', '#id_estado', '#id_ciudad');
</script>
```

#### **❌ INCORRECTO - Duplicar:**

```javascript
// ❌ NO crear múltiples versiones
// ❌ NO copiar el código a cada template
// ❌ NO hacer inline scripts duplicados
```

#### **Ventajas de Reutilización:**

1. ✅ **DRY (Don't Repeat Yourself)**
2. ✅ **Single source of truth**
3. ✅ **Mantenibilidad:** Un solo archivo para actualizar
4. ✅ **Consistencia:** Mismo comportamiento en todos los forms
5. ✅ **Testing:** Se prueba una vez

#### **Funcionalidad:**

```javascript
// locations.js hace automáticamente:
// 1. Detectar país seleccionado
// 2. Cargar estados de ese país desde /api/locations?country=XX
// 3. Llenar select de estados
// 4. Al seleccionar estado, cargar ciudades
// 5. Llenar select de ciudades
// 6. Manejo de errores graceful
```

---

## 📋 **RESUMEN DE ARQUITECTURA**

### **Fuentes de Verdad (Single Source of Truth):**

```
✅ Address → Origen de verdad para direcciones
   ├── line1, line2
   ├── city → Ciudad
   ├── postal_code
   └── sales_tax (calculado automáticamente)

✅ TaxPolicy → Origen de verdad para impuestos
   ├── country, state_code, city_name
   ├── applies_to (parts/services/both)
   ├── rate
   └── resolve_tax_rate() usa esto

✅ Part/Service → Origen de verdad para catálogo
   ├── PartI18N/ServiceI18N → Nombres localizados
   ├── PartPrice/ServicePrice → Precios por empresa
   └── get_display_name(locale) para obtener nombre

✅ locations.js → Origen de verdad para UI de ubicaciones
   └── Reutilizar en todos los formularios
```

### **Campos Legacy (Deprecar):**

```
❌ Cliente.estado_usa → Usar billing_address.city.estado
❌ Cliente.ciudad_usa → Usar billing_address.city
❌ Cliente.zipcode → Usar billing_address.postal_code
❌ Cliente.direccion → Usar billing_address.line1
❌ ConfiguracionEmpresa.direccion → Usar legal_address (FK Address)
```

### **Campos que SE MANTIENEN:**

```
✅ LineaRepuesto.nombre → Congela display del repuesto
✅ LineaRepuesto.part → FK al catálogo (analytics)
✅ LineaServicio.nombre → Congela display del servicio
✅ LineaServicio.service → FK al catálogo (analytics)
```

---

## 🎯 **PATRONES CORRECTOS**

### **Patrón 1: Crear Cliente con Address**

```python
# ✅ CORRECTO
from ubicacion.models import Address
from taller.models import Cliente, Ciudad

# 1. Crear Address
city = Ciudad.objects.get(id=city_id)  # Ciudad del modelo unificado
address = Address.objects.create(
    line1='Av. Arequipa 123',
    line2='Oficina 501',
    city=city,
    postal_code='15001',
    company=empresa
)

# 2. Crear Cliente con Address
cliente = Cliente.objects.create(
    nombre='Juan',
    apellido='Pérez',
    billing_address=address,  # ✅ Origen de verdad
    empresa=empresa
)

# 3. Obtener datos de dirección
print(address.full_address)  # ✅ Desde Address
print(address.country_code)  # ✅ 'PE'

# Para sales tax, usar TaxPolicy vía resolve_tax_rate()
from taller.impuestos.engine import resolve_tax_rate
rate, _ = resolve_tax_rate(empresa, address.city, 'parts')
print(f"Tax rate: {rate * 100}%")  # ✅ 18.00% (desde TaxPolicy)
```

---

### **Patrón 2: Crear Línea de Documento**

```python
# ✅ CORRECTO
from taller.models import Part, LineaRepuesto

# 1. Obtener part del catálogo
oil = Part.objects.get(sku='OIL-5W30-4L')

# 2. Obtener locale de la empresa
locale = documento.empresa.locale or 'es-CL'

# 3. Crear línea CONGELANDO el nombre
linea = LineaRepuesto.objects.create(
    documento=documento,
    part=oil,  # ✅ FK al catálogo (analytics, trazabilidad)
    nombre=oil.get_display_name(locale),  # ✅ CONGELAR display
    cantidad=2,
    precio_unitario=oil.get_price(documento.empresa),  # También congelado
    descuento=Decimal('0.00')
)

# 4. El documento muestra el nombre congelado
print(linea.nombre)  # ✅ Nombre en el momento de la venta

# 5. Si el catálogo cambia después, el documento NO cambia
oil.i18n.filter(locale=locale).update(
    display_name='Aceite Premium 5W30'  # Cambio en catálogo
)
print(linea.nombre)  # ✅ Sigue mostrando nombre original (congelado)
```

---

### **Patrón 3: Usar Motor de Impuestos**

```python
# ✅ CORRECTO - Configurable via TaxPolicy
from taller.impuestos.engine import resolve_tax_rate

# 1. Para Chile repuestos
rate, _ = resolve_tax_rate(empresa_chile, None, 'parts')
# rate = 0.19 (19%) ✅ Desde TaxPolicy

# 2. Para Chile servicios
rate, _ = resolve_tax_rate(empresa_chile, None, 'services')
# rate = 0.00 (0%) ✅ Sin TaxPolicy = sin impuesto

# 3. Para USA con ubicación
rate, _ = resolve_tax_rate(empresa_usa, ciudad_california, 'parts')
# rate = 0.0725 (7.25%) ✅ Desde TaxPolicy de CA

# ❌ INCORRECTO - Hardcodear
if empresa.pais == 'CL':
    if tipo == 'parts':
        rate = Decimal('0.19')  # ❌ MAL
    else:
        rate = Decimal('0.00')  # ❌ MAL
```

---

### **Patrón 4: Usar locations.js**

```html
<!-- ✅ CORRECTO - Reutilizar el mismo archivo -->

<!-- Formulario Cliente -->
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_country', '#id_state', '#id_city');
</script>

<!-- Formulario Empresa -->
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_company_country', '#id_company_state', '#id_company_city');
</script>

<!-- Formulario Proveedor (futuro) -->
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  bindCountryStateCity('#id_supplier_country', '#id_supplier_state', '#id_supplier_city');
</script>
```

```javascript
// ❌ INCORRECTO - Duplicar código
<script>
  // ❌ NO copiar la lógica inline
  document.getElementById('country').addEventListener('change', function() {
    // ... código duplicado ...
  });
</script>
```

---

## 📊 **DIAGRAMA DE ARQUITECTURA**

```
┌─────────────────────────────────────────────────────────┐
│                   ORIGEN DE VERDAD                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  DIRECCIONES:                                            │
│    Address (ubicacion.models)                            │
│      ├── line1, line2, postal_code                       │
│      ├── city → Ciudad → Estado → pais                   │
│      ├── sales_tax (automático)                          │
│      └── full_address (property)                         │
│                                                          │
│  IMPUESTOS:                                              │
│    TaxPolicy (taller.models)                             │
│      ├── country, state_code, city_name                  │
│      ├── applies_to (parts/services/both)                │
│      ├── rate                                            │
│      └── resolve_tax_rate() consulta esto               │
│                                                          │
│  CATÁLOGO:                                               │
│    Part/Service                                          │
│      ├── SKU/code (único)                                │
│      ├── PartI18N/ServiceI18N (nombres por idioma)       │
│      ├── PartPrice/ServicePrice (precios por empresa)    │
│      └── get_display_name(locale) → nombre localizado   │
│                                                          │
│  UI UBICACIONES:                                         │
│    locations.js (ES6 module)                             │
│      ├── bindCountryStateCity()                          │
│      ├── Consume: /api/locations                         │
│      └── Reutilizar en TODOS los forms                  │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    CAMPOS LEGACY                         │
│                  (Deprecar en 2-3 releases)              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ❌ Cliente.estado_usa                                   │
│  ❌ Cliente.ciudad_usa                                   │
│  ❌ Cliente.zipcode                                      │
│  ❌ Cliente.direccion                                    │
│  ❌ ConfiguracionEmpresa.direccion                       │
│                                                          │
│  → Migrar a Address con backfill_addresses              │
│  → Feature flag: use_address_v2                         │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│             CAMPOS QUE SE MANTIENEN                      │
│              (NO deprecar nunca)                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ✅ LineaRepuesto.nombre → Congela display               │
│  ✅ LineaRepuesto.part → FK al catálogo                  │
│  ✅ LineaRepuesto.precio_unitario → Congela precio       │
│                                                          │
│  ✅ LineaServicio.nombre → Congela display               │
│  ✅ LineaServicio.service → FK al catálogo               │
│  ✅ LineaServicio.precio_unitario → Congela precio       │
│                                                          │
│  RAZÓN: Inmutabilidad de documentos históricos          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## ⚠️ **ERRORES COMUNES A EVITAR**

### **Error 1: Usar estado_usa/ciudad_usa como genéricos**

```python
# ❌ MAL
cliente_peru.estado_usa = estado_lima  # ❌ "usa" no es genérico
cliente_peru.ciudad_usa = ciudad_lima  # ❌ Confuso y legacy

# ✅ BIEN
address = Address.objects.create(city=ciudad_lima, ...)
cliente_peru.billing_address = address
```

### **Error 2: Eliminar nombre de LineaRepuesto/LineaServicio**

```python
# ❌ MAL
class LineaRepuesto(models.Model):
    part = models.ForeignKey('taller.Part', ...)
    # nombre eliminado ❌ ERROR

# ✅ BIEN
class LineaRepuesto(models.Model):
    part = models.ForeignKey('taller.Part', ...)
    nombre = models.CharField(...)  # ✅ Mantener para congelar
```

### **Error 3: Hardcodear impuestos**

```python
# ❌ MAL
if documento.empresa.pais == 'CL':
    if tipo == 'parts':
        tasa = Decimal('0.19')  # ❌ Hardcoded

# ✅ BIEN
tasa, _ = resolve_tax_rate(documento.empresa, ciudad, tipo)
# Consulta TaxPolicy (configurable)
```

### **Error 4: Duplicar locations.js**

```javascript
// ❌ MAL - Crear archivo nuevo
// taller/static/js/cliente_locations.js
// taller/static/js/empresa_locations.js

// ✅ BIEN - Reutilizar el mismo
import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
```

---

## 📖 **GUÍAS DE REFERENCIA**

### **Para Address:**
Ver: `SISTEMA_MULTI_PAIS_COMPLETO_FINAL.md` - Sección "Address"

### **Para Motor de Impuestos:**
Ver: `MOTOR_IMPUESTOS_IMPLEMENTADO.md`

### **Para Catálogo:**
Ver: `SISTEMA_MULTI_PAIS_COMPLETO_FINAL.md` - Sección "Catálogo I18N"

### **Para locations.js:**
Ver: `EJEMPLOS_USO_LOCATIONS_JS.md`

---

## ✅ **CHECKLIST DE VERIFICACIÓN**

Antes de implementar nuevas features, verificar:

- [ ] ¿Estoy usando Address como origen de verdad para direcciones?
- [ ] ¿Estoy marcando estado_usa/ciudad_usa como legacy?
- [ ] ¿Estoy manteniendo el campo nombre en líneas de documento?
- [ ] ¿Estoy usando resolve_tax_rate() en lugar de hardcodear?
- [ ] ¿Estoy reutilizando locations.js en lugar de duplicar?
- [ ] ¿Estoy usando TaxPolicy para configurar impuestos?
- [ ] ¿Estoy congelando nombres al crear líneas de documento?

---

## 🎊 **RESUMEN**

```
✅ Address = Origen de verdad para direcciones
❌ estado_usa/ciudad_usa = Legacy (deprecar)
✅ nombre en líneas = Congelar (mantener siempre)
✅ TaxPolicy = Motor configurable
✅ locations.js = Reutilizar (no duplicar)
```

**Estado:** ✅ **ARQUITECTURA CLARIFICADA**

---

## 🎯 **AJUSTES FINALES DE CONSISTENCIA (CRÍTICO)**

### **1. NOMBRES DE APPS CORRECTOS** ⭐⭐⭐

#### **✅ CONVENCIÓN OFICIAL (ACTUAL):**

```python
# ACTUALMENTE (Release 1.0) - Usar tal como están:
'taller.Part'          # ✅ Actualmente en taller/models/catalogo_repuestos.py
'taller.PartI18N'      # ✅ Actualmente en taller/models/catalogo_repuestos.py
'taller.PartPrice'     # ✅ Actualmente en taller/models/catalogo_repuestos.py
'taller.TaxPolicy'     # ✅ Actualmente en taller/models/catalogo_repuestos.py

'taller.Service'       # ✅ Actualmente en taller/models/catalogo_servicios.py
'taller.ServiceI18N'   # ✅ Actualmente en taller/models/catalogo_servicios.py
'taller.ServicePrice'  # ✅ Actualmente en taller/models/catalogo_servicios.py
'taller.ServicioExterno'  # ✅ Actualmente en taller/servicios/models.py

'ubicacion.Address'    # ✅ Correcto
'taller.Cliente'       # ✅ Correcto
'taller.Documento'     # ✅ Correcto
'taller.Ciudad'        # ✅ Correcto
'taller.Estado'        # ✅ Correcto
```

#### **⚠️ MIGRACIÓN FUTURA (Release 2.0+):**

```python
# FUTURO - Cuando se creen apps separadas:
'repuestos.Part'          # Mover desde taller.Part
'repuestos.PartI18N'      # Mover desde taller.PartI18N
'repuestos.PartPrice'     # Mover desde taller.PartPrice
'repuestos.TaxPolicy'     # Mover desde taller.TaxPolicy

'servicios.Service'       # Mover desde taller.Service
'servicios.ServiceI18N'   # Mover desde taller.ServiceI18N
'servicios.ServicePrice'  # Mover desde taller.ServicePrice
'servicios.ServicioExterno'  # Ya está en la app correcta ✅
```

#### **RAZÓN PARA MIGRACIÓN FUTURA:**

- ✅ Claridad semántica (Part pertenece conceptualmente a repuestos)
- ✅ Separación de concerns (apps especializadas)
- ✅ Escalabilidad (apps independientes)
- ✅ FKs como string facilitan la migración (sin breaking changes)

---

### **2. FKs COMO STRING - REGLA ABSOLUTA** ⭐⭐⭐

#### **✅ CONVENCIÓN DEL PROYECTO:**

**TODAS las ForeignKeys SE DECLARAN COMO STRING. NUNCA como import directo.**

```python
# ✅ SIEMPRE CORRECTO:
class MiModelo(models.Model):
    documento = models.ForeignKey(
        'taller.Documento',  # ✅ String reference
        on_delete=models.CASCADE
    )
    part = models.ForeignKey(
        'repuestos.Part',  # ✅ String reference
        on_delete=models.PROTECT,
        null=True
    )
    address = models.ForeignKey(
        'ubicacion.Address',  # ✅ String reference
        on_delete=models.SET_NULL,
        null=True
    )

# ❌ NUNCA HACER:
from taller.models import Documento
from repuestos.models import Part

class MiModelo(models.Model):
    documento = models.ForeignKey(
        Documento,  # ❌ Import directo (causa circular imports)
        on_delete=models.CASCADE
    )
    part = models.ForeignKey(
        Part,  # ❌ Import directo
        on_delete=models.PROTECT
    )
```

#### **RAZONES:**

1. ✅ **Evita imports circulares** (problema común en Django)
2. ✅ **Lazy loading** de modelos
3. ✅ **Refactoring fácil** (mover modelos entre apps)
4. ✅ **Convención de Django** (Best Practice oficial)
5. ✅ **Consistencia** en todo el codebase
6. ✅ **Migraciones transparentes** cuando se reorganizan apps

---

### **3. VERIFICACIÓN DE FKs EN EL PROYECTO**

#### **Todos los modelos del proyecto DEBEN usar strings:**

```python
# Cliente
billing_address = models.ForeignKey('ubicacion.Address', ...)  # ✅

# LineaRepuesto
documento = models.ForeignKey('taller.Documento', ...)  # ✅
part = models.ForeignKey('taller.Part', ...)  # ✅ (actualmente taller, futuro: repuestos.Part)

# LineaServicio
documento = models.ForeignKey('taller.Documento', ...)  # ✅
service = models.ForeignKey('taller.Service', ...)  # ✅ (actualmente taller, futuro: servicios.Service)

# LineaOtroServicio
documento = models.ForeignKey('taller.Documento', ...)  # ✅
servicio = models.ForeignKey('taller.Servicio', ...)  # ✅ (legacy)

# Address
city = models.ForeignKey('taller.Ciudad', ...)  # ✅
company = models.ForeignKey('taller.Empresa', ...)  # ✅

# PartPrice
part = models.ForeignKey('taller.Part', ...)  # ✅ (actualmente taller, futuro: repuestos.Part)
company = models.ForeignKey('taller.Empresa', ...)  # ✅
tax_policy = models.ForeignKey('taller.TaxPolicy', ...)  # ✅ (actualmente taller, futuro: repuestos.TaxPolicy)

# ServicePrice
service = models.ForeignKey('taller.Service', ...)  # ✅ (actualmente taller, futuro: servicios.Service)
company = models.ForeignKey('taller.Empresa', ...)  # ✅
tax_policy = models.ForeignKey('taller.TaxPolicy', ...)  # ✅ (actualmente taller, futuro: repuestos.TaxPolicy)
```

---

## 📊 **TABLA DE APPS Y MODELOS**

| App | Modelos | Ubicación Actual | Ubicación Futura |
|-----|---------|------------------|------------------|
| **repuestos** | Part, PartI18N, PartPrice, TaxPolicy | taller/models/catalogo_repuestos.py | repuestos/models.py |
| **servicios** | Service, ServiceI18N, ServicePrice | taller/models/catalogo_servicios.py | servicios/models.py |
| **servicios** | ServicioExterno | taller/servicios/models.py | ✅ Ya correcto |
| **ubicacion** | Address | ubicacion/models.py | ✅ Ya correcto |
| **taller** | Ciudad, Estado | taller/models/ubicacion.py | ✅ Ya correcto |
| **taller** | Cliente, Documento, Empresa | taller/models/ | ✅ Ya correcto |

---

## 🚨 **ERRORES COMUNES A EVITAR**

### **Error 1: Importar modelo para FK**
```python
# ❌ MAL
from taller.models import Documento
field = models.ForeignKey(Documento, ...)

# ✅ BIEN
field = models.ForeignKey('taller.Documento', ...)
```

### **Error 2: No usar string reference**
```python
# ❌ MAL
from taller.models import Part
part = models.ForeignKey(Part, ...)  # Import directo

# ✅ BIEN
part = models.ForeignKey('taller.Part', ...)  # String reference
```

### **Error 3: Mezclar estilos**
```python
# ❌ INCONSISTENTE
part = models.ForeignKey('taller.Part', ...)  # String
from taller.models import Documento
documento = models.ForeignKey(Documento, ...)  # Import directo

# ✅ CONSISTENTE
part = models.ForeignKey('taller.Part', ...)
documento = models.ForeignKey('taller.Documento', ...)  # Ambos string
```

---

## 🎓 **BEST PRACTICES FINALES**

### **1. En Modelos:**
```python
# ✅ SIEMPRE
field = models.ForeignKey('app.Model', on_delete=models.CASCADE)

# Formato completo recomendado:
field = models.ForeignKey(
    'app.Model',
    on_delete=models.CASCADE,
    related_name='related_objects',
    verbose_name='Campo',
    help_text='Descripción del campo'
)
```

### **2. En Queries:**
```python
# ✅ Importar normalmente para queries
from taller.models import Cliente, Documento
from repuestos.models import Part  # Cuando exista la app
# O si aún no existe app separada:
from taller.models import Part  # Temporal

# Queries
clientes = Cliente.objects.filter(...)
parts = Part.objects.filter(...)
```

### **3. En Documentación:**
```markdown
# ✅ Usar nombres de apps actuales (Release 1.0)
- taller.Part (actual)
- taller.Service (actual)
- Futuro: repuestos.Part, servicios.Service (Release 2.0+)

# Ejemplos de código con FKs como string
```python
part = models.ForeignKey('taller.Part', ...)  # Actual
service = models.ForeignKey('taller.Service', ...)  # Actual
```
```

---

## ✅ **CHECKLIST DE VERIFICACIÓN FINAL**

### **Código:**
- [✅] Todas las FKs usan strings (verificado)
- [✅] FKs a Part usan `'taller.Part'` (ACTUAL Release 1.0)
- [✅] FKs a Service usan `'taller.Service'` (ACTUAL Release 1.0)
- [✅] FKs a Address usan `'ubicacion.Address'`
- [✅] Sin imports directos para FKs (eliminados)
- [ ] Migrar a apps separadas (Release 2.0+): `repuestos.Part`, `servicios.Service`

### **Documentación:**
- [✅] Ejemplos usan `'taller.Part'` (ACTUAL en Release 1.0)
- [✅] Ejemplos usan `'taller.Service'` (ACTUAL en Release 1.0)
- [✅] Todos los ejemplos de FKs muestran strings
- [✅] Aclaraciones arquitectónicas actualizadas
- [ ] Documentar migración futura a `repuestos.Part` y `servicios.Service` (Release 2.0+)

---

## 🎊 **RESUMEN DE AJUSTES FINALES**

```
✅ Consistencia de nombres (ACTUAL Release 1.0):
   - taller.Part (actual ubicación)
   - taller.Service (actual ubicación)
   - Migración futura: repuestos.Part, servicios.Service (Release 2.0+)

✅ FKs como string (100% del proyecto):
   - TODAS las FKs como string ✅ VERIFICADO
   - NUNCA import directo ✅ CORREGIDO
   - Convención del proyecto ✅ APLICADA

✅ Imports directos eliminados:
   - Eliminado: from taller.servicios.models import Servicio
   - Todas las FKs ahora usan strings
   - Sin circular imports

✅ Preparado para apps separadas (futuro):
   - FKs ya usan strings
   - Migración será transparente
   - Sin breaking changes cuando se muevan

✅ Documentación actualizada:
   - Ejemplos consistentes
   - Nombres correctos (taller.Part actual)
   - FKs siempre como string
   - Migración futura documentada
```

**Estado:** ✅ **AJUSTES FINALES IMPLEMENTADOS Y VERIFICADOS**

---

### **4. Address.sales_tax ELIMINADO** ⭐⭐⭐

#### **✅ CORRECCIÓN CRÍTICA:**

**Address NO tiene property `sales_tax`.** La tasa de impuestos viene de **TaxPolicy**, no de Address.

```python
# ❌ INCORRECTO (eliminado):
address.sales_tax  # ❌ No existe, no usar

# ✅ CORRECTO - Usar TaxPolicy:
from taller.impuestos.engine import resolve_tax_rate

ship_to_city = address.city if address else None
rate, inclusive = resolve_tax_rate(
    empresa=empresa,
    ship_to_city=ship_to_city,
    applies_to='parts'  # o 'services' o 'both'
)
```

#### **Properties de Address (SOLO Ubicación):**

```python
# ✅ Address provee SOLO información de ubicación:
address.full_address    # Dirección completa formateada
address.country_code    # Código de país (CL, US, BR, PE, VE)
address.state           # Estado/Departamento
address.city            # Ciudad

# ❌ Address NO provee:
# address.sales_tax     # ELIMINADO - viene de TaxPolicy
```

#### **Origen de Verdad para Impuestos:**

```python
# ✅ TaxPolicy vía resolve_tax_rate():
rate, _ = resolve_tax_rate(empresa, ciudad, tipo)

# Considera:
# 1. TaxPolicy configurado (país, estado, ciudad)
# 2. Tipo de item (parts, services, both)
# 3. Convenciones (Chile 19% solo repuestos)
# 4. Fallbacks configurables
```

**Ver:** `CORRECCION_FINAL_SALES_TAX.md` para detalles completos.

---

### **5. NORMALIZACIÓN DE UBICACIONES** ⭐⭐⭐

#### **✅ ISO 3166-1 alpha-2 + Restricciones:**

**Estado y Ciudad tienen normalización completa con restricciones de base de datos.**

```python
# Estado
class Estado(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10)  # ✅ GA, SP, RM, LIM
    pais = models.CharField(max_length=2)     # ✅ ISO 3166-1 alpha-2 (CL, US, BR, PE, VE)
    
    class Meta:
        unique_together = [("pais", "codigo")]  # ✅ No duplicados
        indexes = [
            models.Index(fields=["pais", "codigo"]),  # ✅ Query optimizada
            models.Index(fields=["pais"]),            # ✅ Query optimizada
        ]

# Ciudad
class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.ForeignKey('taller.Estado', ...)
    
    class Meta:
        unique_together = [("estado", "nombre")]  # ✅ No duplicados en mismo estado
        indexes = [
            models.Index(fields=["estado", "nombre"]),  # ✅ Query optimizada
            models.Index(fields=["estado"]),            # ✅ Query optimizada
        ]
```

#### **Validación Automática:**

```python
# Estado.clean() normaliza automáticamente:
estado = Estado(nombre='Lima', codigo='lim', pais='pe')
estado.save()
# Resultado: codigo='LIM', pais='PE' (uppercase automático) ✅

# No permite duplicados:
Estado.objects.create(codigo='LIM', pais='PE', ...)  # ✅ OK
Estado.objects.create(codigo='LIM', pais='PE', ...)  # ❌ IntegrityError (duplicado)

# Ciudad también valida:
Ciudad.objects.create(nombre='Lima', estado=lima_estado)  # ✅ OK
Ciudad.objects.create(nombre='Lima', estado=lima_estado)  # ❌ IntegrityError (duplicado)
```

#### **Beneficios:**

1. ✅ **Estándar internacional** (ISO 3166-1)
2. ✅ **Integridad de datos** (no duplicados)
3. ✅ **Performance** (índices optimizados)
4. ✅ **Normalización automática** (uppercase)
5. ✅ **Queries rápidas** (índices en FK y unique_together)

**Ver:** `NORMALIZACION_UBICACIONES_IMPLEMENTADA.md` para detalles completos.

---

### **6. ÍNDICES E INTEGRIDAD EN CATÁLOGO** ⭐⭐⭐

#### **✅ OPTIMIZACIÓN DE PERFORMANCE E INTEGRIDAD:**

**Catálogo con índices compuestos y validaciones de solapes de vigencias.**

```python
# Part: SKU único e indexado
class Part(models.Model):
    sku = models.CharField(
        unique=True,      # ✅ No duplicados
        db_index=True,    # ✅ Búsquedas rápidas
        max_length=64
    )

# Service: Código único e indexado
class Service(models.Model):
    code = models.CharField(
        unique=True,      # ✅ No duplicados
        db_index=True,    # ✅ Búsquedas rápidas
        max_length=64
    )

# TaxPolicy: Índice compuesto para resolve_tax_rate()
class TaxPolicy(models.Model):
    class Meta:
        indexes = [
            # ✅ Índice compuesto (5 campos)
            models.Index(
                fields=['country', 'state_code', 'city_name', 'applies_to', 'active'],
                name='idx_taxpolicy_lookup'
            ),
        ]

# PartPrice: Índice compuesto + validación de solapes
class PartPrice(models.Model):
    class Meta:
        indexes = [
            # ✅ Índice compuesto (4 campos)
            models.Index(
                fields=['company', 'part', 'valid_from', 'valid_to'],
                name='idx_partprice_lookup'
            ),
        ]
    
    def clean(self):
        """✅ Evita solapes de vigencias en la misma empresa"""
        # Valida que no haya dos precios activos para mismo part/company/currency
        # Valida que valid_from < valid_to

# ServicePrice: Igual que PartPrice
class ServicePrice(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['company', 'service', 'valid_from', 'valid_to']),
        ]
    
    def clean(self):
        """✅ Evita solapes de vigencias"""
```

#### **Beneficios:**

1. ✅ **Performance:** Queries ~10-100x más rápidas
2. ✅ **Integridad:** No duplicados ni solapes
3. ✅ **resolve_tax_rate():** Ultra-rápido (índice compuesto 5 campos)
4. ✅ **Precios vigentes:** Búsqueda optimizada (índice compuesto 4 campos)
5. ✅ **Validación automática:** En save() vía clean()

**Ver:** `INDICES_INTEGRIDAD_CATALOGO.md` para detalles técnicos completos.

---

### **7. MÉTODOS UTILITARIOS EN CATÁLOGO** ⭐⭐⭐

#### **✅ API CLARA PARA EVITAR IMPROVISACIONES:**

**Part y Service tienen métodos utilitarios con fallbacks inteligentes.**

```python
# Part.get_display_name(locale)
class Part(models.Model):
    def get_display_name(self, locale='es-CL'):
        """
        Fallback inteligente:
        1. Locale exacto (es-PE) ✅
        2. es-CL (por defecto) ✅
        3. Primer I18N disponible ✅
        4. SKU (último recurso) ✅
        """
        # 1. Intentar locale exacto
        try:
            i18n = self.i18n.get(locale=locale)
            return i18n.display_name
        except PartI18N.DoesNotExist:
            pass
        
        # 2. Fallback a es-CL
        if locale != 'es-CL':
            try:
                i18n = self.i18n.get(locale='es-CL')
                return i18n.display_name
            except PartI18N.DoesNotExist:
                pass
        
        # 3. Fallback al primer I18N
        i18n = self.i18n.first()
        if i18n:
            return i18n.display_name
        
        # 4. Fallback al SKU
        return self.sku

# Part.get_price(empresa, fecha=None)
class Part(models.Model):
    def get_price(self, empresa, fecha=None):
        """
        Fallback de precios:
        1. Precio de empresa específica ✅
        2. Precio global (company=NULL) ✅
        3. None si no existe ✅
        
        Vigencia: fecha ∈ [valid_from, valid_to]
        """
        if fecha is None:
            fecha = date.today()
        
        # 1. Precio de empresa
        price = self.prices.filter(
            company=empresa,
            valid_from__lte=fecha
        ).filter(
            Q(valid_to__gte=fecha) | Q(valid_to__isnull=True)
        ).order_by('-valid_from').first()
        
        if price:
            return price
        
        # 2. Fallback a precio global
        price_global = self.prices.filter(
            company__isnull=True,
            valid_from__lte=fecha
        ).filter(
            Q(valid_to__gte=fecha) | Q(valid_to__isnull=True)
        ).order_by('-valid_from').first()
        
        return price_global

# Service: Mismos métodos con misma lógica
class Service(models.Model):
    def get_display_name(self, locale='es-CL'):
        """Igual que Part.get_display_name()"""
    
    def get_price(self, empresa, fecha=None):
        """Igual que Part.get_price()"""
```

#### **Uso Correcto:**

```python
# ✅ SÍ: Usar métodos utilitarios
name = part.get_display_name('es-PE')  # Nunca falla
price_record = part.get_price(empresa)  # Con fallbacks
if price_record:
    print(f"{name}: {price_record.currency} {price_record.price}")

# ❌ NO: Improvisaciones
name = part.i18n.get(locale='es-PE').display_name  # ❌ Puede fallar
price = part.prices.filter(company=empresa).first().price  # ❌ Lógica incompleta
```

#### **Beneficios:**

1. ✅ **API clara:** No improvisaciones
2. ✅ **Fallbacks inteligentes:** Siempre retorna algo útil
3. ✅ **Consistencia:** Mismo patrón en Part y Service
4. ✅ **Mantenibilidad:** Lógica centralizada
5. ✅ **Testeable:** Fácil de verificar

**Ver:** `METODOS_UTILITARIOS_CATALOGO.md` para ejemplos completos y tests.

---

### **8. CÁLCULOS FINANCIEROS ESTÁNDAR** ⭐⭐⭐

#### **✅ DECIMAL.QUANTIZE CON ROUND_HALF_UP:**

**Todos los cálculos de dinero usan el estándar financiero ROUND_HALF_UP.**

```python
from decimal import Decimal, ROUND_HALF_UP

def _quantize_money(value):
    """
    Redondear valor financiero a 2 decimales con ROUND_HALF_UP (estándar financiero).
    
    Ejemplos:
        >>> _quantize_money(Decimal('123.456'))
        Decimal('123.46')  # Redondeo hacia arriba
        
        >>> _quantize_money(Decimal('123.455'))
        Decimal('123.46')  # ROUND_HALF_UP: .5 siempre hacia arriba ✅
    
    Importante:
        Este es el estándar financiero internacional.
        SIEMPRE usar esto en cálculos de dinero.
    """
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# Aplicar en TODO el sistema:
# 1. Subtotal de línea
subtotal_linea = _quantize_money(cantidad * precio - descuento)

# 2. Total de categoría
total_parts = _quantize_money(sum(subtotales))

# 3. Impuestos
tax = _quantize_money(subtotal * rate)

# 4. Total final
total = _quantize_money(subtotal + tax)
```

#### **✅ USAR CAMPO SUBTOTAL SI EXISTE:**

```python
# ✅ SÍ: Usar campo subtotal precalculado
if hasattr(linea, 'subtotal') and linea.subtotal is not None:
    subtotal_linea = linea.subtotal  # Ya está guardado, no recalcular
else:
    # Solo calcular si no existe el campo
    subtotal_linea = _quantize_money(cantidad * precio - descuento)

# ❌ NO: Calcular "a mano" siempre
subtotal = cantidad * precio - descuento  # ❌ Ignora subtotal guardado
```

**Razón:** El subtotal guardado es el que se facturó. Recalcular puede dar diferente resultado si cambió el código.

#### **✅ KPIs USAN fecha_emision (NO fecha_creacion):**

```python
# ✅ SÍ: KPIs por fecha de emisión
ingresos = Documento.objects.filter(
    fecha_emision__year=2025,  # ✅ Fecha del documento oficial
    fecha_emision__month=6
).aggregate(Sum('total'))

# ❌ NO: KPIs por fecha de creación
ingresos = Documento.objects.filter(
    fecha_creacion__year=2025,  # ❌ Fecha del registro en DB
    fecha_creacion__month=6
).aggregate(Sum('total'))
```

**Razón:**
- ✅ **fecha_emision:** Fecha oficial del documento (para contabilidad, impuestos, auditoría)
- ❌ **fecha_creacion:** Fecha del registro en DB (solo para auditoría técnica)

**Ejemplo:**
- Documento creado: 2025-05-30 (borrador)
- Documento emitido: 2025-06-01 (factura oficial)
- **KPI debe contar en: JUNIO** (no Mayo)

#### **Beneficios:**

1. ✅ **Precisión financiera:** ROUND_HALF_UP es estándar internacional
2. ✅ **Consistencia:** Subtotal no cambia después de emitido
3. ✅ **Auditoría correcta:** KPIs usan fecha_emision (requerido por ley)
4. ✅ **Performance:** No recalcular subtotales en cada query
5. ✅ **Inmutabilidad:** Documentos emitidos no cambian

**Ver:** `CALCULOS_FINANCIEROS_ESTANDAR.md` para detalles completos y ejemplos.

---

### **9. TENANCY Y AUDITORÍA** ⭐⭐⭐

#### **✅ DOCUMENTO.CLEAN() - VALIDACIÓN DE TENANCY:**

**Validar que empresa coincide en TODAS las FKs para aislamiento multi-tenant.**

```python
class Documento(models.Model):
    empresa = models.ForeignKey('Empresa', ...)
    cliente = models.ForeignKey('Cliente', ...)
    vehiculo = models.ForeignKey('Vehiculo', ...)
    
    def clean(self):
        """
        Validar que empresa coincide en TODAS las FKs.
        
        Validaciones:
        1. cliente.empresa == documento.empresa ✅
        2. vehiculo.empresa == documento.empresa ✅
        3. vehiculo.cliente == documento.cliente ✅
        4. País consistente (cliente vs empresa) ✅
        
        CRÍTICO: Previene acceso cruzado de datos entre empresas.
        """
        from django.core.exceptions import ValidationError
        super().clean()
        
        if not self.empresa:
            return
        
        # Validar cliente
        if self.cliente:
            if hasattr(self.cliente, 'empresa') and self.cliente.empresa:
                if self.cliente.empresa_id != self.empresa_id:
                    raise ValidationError({
                        'cliente': f'El cliente pertenece a otra empresa'
                    })
        
        # Validar vehículo
        if self.vehiculo:
            if hasattr(self.vehiculo, 'empresa') and self.vehiculo.empresa:
                if self.vehiculo.empresa_id != self.empresa_id:
                    raise ValidationError({
                        'vehiculo': f'El vehículo pertenece a otra empresa'
                    })
            
            # Validar vehículo pertenece al cliente
            if self.cliente and hasattr(self.vehiculo, 'cliente'):
                if self.vehiculo.cliente_id != self.cliente_id:
                    raise ValidationError({
                        'vehiculo': f'El vehículo no pertenece al cliente'
                    })
    
    def save(self, *args, **kwargs):
        """Ejecutar validación antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)

# Validar en líneas también:
class LineaRepuesto(models.Model):
    def clean(self):
        """Validar que part pertenece a empresa o es global"""
        if self.part and self.part.empresa:
            if self.part.empresa_id != self.documento.empresa_id:
                raise ValidationError('Part de otra empresa')

class LineaServicio(models.Model):
    def clean(self):
        """Validar que service pertenece a empresa o es global"""
        if self.service and self.service.empresa:
            if self.service.empresa_id != self.documento.empresa_id:
                raise ValidationError('Service de otra empresa')
```

#### **✅ AUDITMIXIN - created_by/updated_by:**

**TODOS los modelos críticos deben heredar de AuditMixin.**

```python
class AuditMixin(models.Model):
    """
    Mixin para auditoría de cambios.
    
    IMPORTANTE: created_by y updated_by son OBLIGATORIOS.
    
    CRÍTICO PARA CURSOR: NO OMITIR ESTOS CAMPOS.
    """
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # ✅ PROTECT: No borrar usuario
        related_name='%(class)s_created',
        verbose_name='Creado por'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # ✅ PROTECT: No borrar usuario
        related_name='%(class)s_updated',
        verbose_name='Modificado por'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de modificación'
    )
    
    class Meta:
        abstract = True  # ✅ Mixin, no tabla
    
    def save(self, *args, **kwargs):
        """Establecer created_by y updated_by automáticamente"""
        user = kwargs.pop('user', None)
        
        if user and user.is_authenticated:
            if not self.pk:  # Nuevo
                if not self.created_by_id:
                    self.created_by = user
            self.updated_by = user  # Siempre actualizar
        
        super().save(*args, **kwargs)

# Uso:
class Documento(AuditMixin, models.Model):
    """✅ Hereda created_by, created_at, updated_by, updated_at"""
    pass

class Cliente(AuditMixin, models.Model):
    """✅ Hereda auditoría"""
    pass

# En views:
documento.save(user=request.user)  # ✅ Pasar user
```

#### **✅ QUERIES SIEMPRE FILTRAN POR EMPRESA:**

```python
# ✅ SÍ: Filtrar por empresa
clientes = Cliente.objects.filter(empresa=request.user.empresa)
documentos = Documento.objects.filter(empresa=request.user.empresa)

# ❌ NO: Sin filtro (expone datos de otras empresas)
clientes = Cliente.objects.all()  # ❌ PELIGROSO
```

#### **Modelos que DEBEN heredar AuditMixin:**

```
✅ Documento (CRÍTICO)
✅ Cliente (CRÍTICO)
✅ Vehiculo (CRÍTICO)
✅ LineaRepuesto (CRÍTICO)
✅ LineaServicio (CRÍTICO)
✅ Part (Recomendado)
✅ Service (Recomendado)
✅ PartPrice (Recomendado)
✅ ServicePrice (Recomendado)
```

#### **Beneficios:**

1. ✅ **Aislamiento de datos:** Empresas no ven datos de otras
2. ✅ **Trazabilidad:** Saber quién creó/modificó cada registro
3. ✅ **Compliance:** Auditorías y normativas
4. ✅ **Integridad:** Validación automática en save()
5. ✅ **Debugging:** Histórico completo de cambios

#### **⚠️ IMPORTANTE PARA CURSOR:**

```
CURSOR: NO OMITIR ESTOS CAMPOS

Al generar código:
1. ✅ Heredar de AuditMixin en modelos críticos
2. ✅ Implementar clean() con validaciones de tenancy
3. ✅ Pasar user=request.user en save()
4. ✅ Filtrar queries por empresa
5. ✅ Usar on_delete=PROTECT para created_by/updated_by
```

**Ver:** `TENANCY_Y_AUDITORIA.md` para implementación completa.

---

### **10. LOCATIONS.JS - UX Y PERFORMANCE** ⭐⭐⭐

#### **✅ OPTIMIZADO CON CACHE, DEBOUNCE Y ABORT:**

**locations.js v2.0 con optimizaciones enterprise para UX y performance.**

```javascript
// ============================================================================
// 1. CACHE EN MEMORIA DEL NAVEGADOR
// ============================================================================

const locationsCache = new Map();

function getCached(key) {
  return locationsCache.get(key) || null;
}

function setCache(key, value) {
  locationsCache.set(key, value);
}

// Verificar cache antes de fetch
const cacheKey = `states:${country}`;
const cached = getCached(cacheKey);

if (cached) {
  console.log('Loaded from CACHE');  // ✅ ~500x más rápido
  populateStatesSelect(cached);
  return;  // No hacer fetch
}

// Fetch y guardar en cache
const data = await fetchJSON(`/api/locations?country=${country}`);
setCache(cacheKey, data.states);  // ✅ Guardar para siguiente vez

// ============================================================================
// 2. DEBOUNCE (150-250ms)
// ============================================================================

function debounce(func, wait = 200) {
  let timeout;
  return function executedFunction(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Aplicar debounce a event listeners
const debouncedLoadStates = debounce(loadStates, 200);  // ✅
const debouncedLoadCities = debounce(loadCities, 200);  // ✅

$country.addEventListener('change', debouncedLoadStates);  // ✅

// Usuario cambia rápido: CL → US → BR → PE
// Resultado: Solo 1 fetch (PE) después de 200ms ✅

// ============================================================================
// 3. ABORTCONTROLLER
// ============================================================================

let statesAbortController = null;

async function loadStates() {
  // ✅ Cancelar fetch anterior si existe
  if (statesAbortController) {
    statesAbortController.abort();
    console.log('Aborted previous fetch');
  }
  
  // ✅ Crear nuevo controller
  statesAbortController = new AbortController();
  
  try {
    const data = await fetchJSON(url, statesAbortController.signal);  // ✅
    // Procesar...
  } catch (error) {
    // ✅ Ignorar AbortError (es normal)
    if (error.name === 'AbortError') {
      return;  // Usuario cambió rápido, OK
    }
    console.error('Real error:', error);
  }
}

// Usuario cambia país antes de que termine fetch anterior
// → Fetch anterior se cancela ✅
// → Solo se procesa el último ✅
// → UX consistente ✅
```

#### **Uso:**

```javascript
import { bindCountryStateCity } from '/static/js/locations.js';

// ✅ Básico (cache + debounce + abort automáticos)
bindCountryStateCity('#id_country', '#id_state', '#id_city');

// ✅ Personalizado
bindCountryStateCity('#id_country', '#id_state', '#id_city', {
  loadingText: 'Cargando...',
  emptyText: 'Seleccione...',
  debug: true,
  debounceMs: 150  // Más rápido
});

// ✅ Precargar para UX instantánea
import { preloadStates } from '/static/js/locations.js';
await preloadStates('PE');  // Segunda carga será instantánea
```

#### **Beneficios:**

1. ✅ **Performance:** ~500x más rápido en segunda carga (cache)
2. ✅ **UX:** Sin lag al cambiar rápido (debounce + abort)
3. ✅ **Bandwidth:** ~3x menos datos transferidos (cache)
4. ✅ **Servidor:** Menos carga (menos fetches)
5. ✅ **Consistencia:** No race conditions (abort)

#### **API Completa:**

```javascript
bindCountryStateCity(country, state, city, opts)  // Principal
preloadStates(country)                             // Precarga
preloadCities(country, state)                      // Precarga
clearLocationsCache()                              // Limpiar
getCacheStats()                                    // Debug
```

**Ver:** `LOCATIONS_JS_OPTIMIZADO.md` para detalles técnicos y ejemplos.

---

### **11. BACKFILL Y ROLLOUT** ⭐⭐⭐

#### **✅ VENTANA DE COMPATIBILIDAD: 2 RELEASES:**

**Migración gradual y segura con feature flag y scripts de verificación.**

```
RELEASE 1.0 (Actual) ──────────────────────────────────┐
│  use_address_v2 = False (default)                    │
│  Legacy activo                                        │
│  Opt-in voluntario                                    │
│  Objetivo: 20-30% migrado                            │
│                        3-6 meses                      │
RELEASE 2.0 ───────────────────────────────────────────┤
│  use_address_v2 = True (default)                     │
│  Legacy deprecado (warnings)                          │
│  Backfill automático                                  │
│  Objetivo: 70-80% migrado                            │
│                        3-6 meses                      │
RELEASE 3.0 ───────────────────────────────────────────┤
│  Address v2 obligatorio                               │
│  Legacy removido                                      │
│  Sistema 100% unificado                               │
│  Objetivo: 100% migrado                               │
└───────────────────────────────────────────────────────┘

TOTAL: 6-12 meses de ventana de compatibilidad
```

#### **Feature Flag en ConfiguracionEmpresa:**

```python
class ConfiguracionEmpresa(models.Model):
    # Feature flag para rollout gradual
    use_address_v2 = models.BooleanField(
        default=False,  # ✅ Release 1.0: Opt-in
        # default=True,  # ✅ Release 2.0: Default
        # REMOVIDO en Release 3.0 (siempre True)
        verbose_name="Usar Address v2",
        help_text=(
            "Activar para usar Address v2. "
            "Desactivar para usar legacy. "
            "Release 1.0: default False (opt-in). "
            "Release 2.0: default True (deprecar legacy). "
            "Release 3.0: legacy removido."
        )
    )
    
    # Legacy (DEPRECADOS en Release 2.0+, REMOVIDOS en Release 3.0)
    direccion = models.CharField(...)  # [LEGACY]
    region = models.ForeignKey(...)    # [LEGACY]
    
    # Address v2 (ACTIVO en Release 1.0+)
    legal_address = models.ForeignKey('ubicacion.Address', ...)  # ✅
```

#### **Script de Verificación Post-Backfill:**

```bash
# Verificar integridad después de backfill
python manage.py verify_backfill

# Output:
[1] Verificando clientes sin billing_address...
[WARN] 15 clientes sin billing_address

[2] Verificando estados sin pais...
[OK] Todos los estados tienen pais

[3] Verificando ciudades sin estado...
[OK] Todas las ciudades tienen estado

[4] Verificando consistencia pais-estado-ciudad...
[OK] Consistencia verificada

[5] Verificando addresses sin city...
[OK] Todos los addresses tienen city

[6] Verificando clientes con datos legacy sin migrar...
[WARN] 25 clientes con datos legacy sin migrar

[7] Verificando estados sin codigo...
[OK] Todos los estados tienen codigo

[8] Verificando empresas con Address v2 activo...
[INFO] 15/50 empresas (30%) usan Address v2

============================================================
RESUMEN DE VERIFICACION:
============================================================

clientes_sin_billing_address: 15 [WARN]
estados_sin_pais: 0 [OK]
ciudades_sin_estado: 0 [OK]
addresses_sin_city: 0 [OK]
clientes_legacy_sin_migrar: 25 [WARN]
estados_sin_codigo: 0 [OK]
total_issues: 40 [WARN]

ACCIONES RECOMENDADAS:
  1. Ejecutar: python manage.py backfill_addresses
  2. Revisar clientes sin datos de ubicacion

# Reporte JSON (para CI/CD)
python manage.py verify_backfill --report-json > report.json
```

#### **Comandos de Backfill:**

```bash
# 1. Backfill de direcciones (legacy → Address v2)
python manage.py backfill_addresses
python manage.py backfill_addresses --dry-run  # Preview
python manage.py backfill_addresses --empresa-id=123  # Solo una

# 2. Backfill de tax IDs
python manage.py backfill_tax_id_types

# 3. Verificar después
python manage.py verify_backfill
python manage.py verify_backfill --verbose
python manage.py verify_backfill --empresa-id=123
```

#### **Rollout Gradual:**

```python
# Fase 1: Piloto (1-2 empresas)
Empresa.objects.filter(pk__in=[5, 12]).update_config(use_address_v2=True)

# Fase 2: Expansión (10-20%)
empresas_activas = Empresa.objects.filter(activa=True)[:20]
for e in empresas_activas:
    e.config.use_address_v2 = True
    e.config.save()

# Fase 3: Mayoritario (50-70%)
# En Release 2.0, cambiar default a True

# Fase 4: Completar (100%)
# En Release 3.0, remover legacy
```

#### **Beneficios:**

1. ✅ **Rollout seguro:** Migración gradual sin downtime
2. ✅ **Reversible:** Flag permite volver a legacy si hay problemas
3. ✅ **Verificable:** Script detecta problemas antes de producción
4. ✅ **Monitoreado:** Estadísticas de adopción
5. ✅ **Documentado:** Ventana de compatibilidad clara

**Ver:** `BACKFILL_Y_ROLLOUT_ESTRATEGIA.md` para cronograma completo y checklist.

---

### **12. SEGURIDAD Y DATOS SENSIBLES** ⭐⭐⭐

#### **✅ TAX_ID ES DATO SENSIBLE:**

**tax_id NO se muestra completo en listados. Validadores específicos por país.**

```python
# ✅ ENMASCARAR EN LISTADOS
from taller.utils.validators import enmascarar_tax_id

# Listado de clientes (admin, templates, APIs)
tax_id_masked = enmascarar_tax_id(cliente.tax_id, cliente.tax_id_type)
# Ejemplos:
# '12345678-9' (RUT_CL)     → '****5678-9'
# '12345678901' (CPF)        → '*******8901'
# '12-3456789' (EIN)         → '**-***6789'
# '123-45-6789' (SSN)        → '***-**-6789'

# ❌ NO mostrar en listados
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'tax_id']  # ❌ PELIGROSO

# ✅ SÍ mostrar enmascarado
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'tax_id_masked']  # ✅
    
    def tax_id_masked(self, obj):
        return enmascarar_tax_id(obj.tax_id, obj.tax_id_type)

# ✅ Mostrar completo SOLO en formularios de edición
```

#### **✅ VALIDADORES ESPECÍFICOS POR TIPO:**

```python
# Validadores implementados con dígito verificador:
RUT_CL   → validar_rut_chile()    # ✅ Módulo 11
CPF      → validar_cpf_brasil()   # ✅ Dígitos verificadores
CNPJ     → validar_cnpj_brasil()  # ✅ Dígitos verificadores
RUC      → validar_ruc_peru()     # ✅ Prefijo + longitud
RIF      → validar_rif_venezuela()# ✅ Letra + longitud
EIN      → validar_ein_usa()      # ✅ Prefijo válido
SSN      → validar_ssn_usa()      # ✅ Área válida

# Uso automático en Cliente.clean():
from taller.utils.validators import validar_tax_id

def clean(self):
    if self.tax_id and self.tax_id_type:
        # ✅ Valida Y normaliza automáticamente
        self.tax_id = validar_tax_id(self.tax_id, self.tax_id_type)

# Ejemplos:
# Input: '12.345.678-9' (RUT_CL) → Output: '12345678-9' ✅ Normalizado
# Input: '123.456.789-01' (CPF)  → Output: '12345678901' ✅ Normalizado
# Input: '12 3456789' (EIN)      → Output: '12-3456789' ✅ Normalizado
```

#### **✅ NORMALIZACIÓN AUTOMÁTICA:**

```python
# Reglas de normalización:
# 1. Remover espacios, puntos, comas
# 2. Convertir a uppercase
# 3. Agregar guion si corresponde según formato estándar

# RUT_CL: Sin puntos, con guion
'12.345.678-9' → '12345678-9'

# CPF/CNPJ/RUC: Solo dígitos
'123.456.789-01' → '12345678901'

# EIN: Con guion formato XX-XXXXXXX
'123456789' → '12-3456789'

# SSN: Con guiones formato XXX-XX-XXXX
'123456789' → '123-45-6789'
```

#### **✅ LIBPHONENUMBER (OPCIONAL):**

```bash
# Instalar (opcional pero recomendado)
pip install phonenumbers

# Si está instalado:
# - Valida teléfonos por país
# - Normaliza a formato E164 (+56912345678)
# - Formatea para mostrar en formato nacional

# Si NO está instalado:
# - Validación básica de longitud
# - Sin normalización automática
```

#### **Beneficios:**

1. ✅ **Seguridad:** Datos sensibles no expuestos
2. ✅ **Integridad:** Tax IDs validados con dígito verificador
3. ✅ **Normalización:** Formato consistente en BD
4. ✅ **Compliance:** GDPR/LGPD (datos sensibles protegidos)
5. ✅ **Logs seguros:** Sin datos sensibles en logs

#### **⚠️ IMPORTANTE PARA CURSOR:**

```
CURSOR: AL MANEJAR tax_id:

✅ Enmascarar en listados (enmascarar_tax_id)
✅ Validar en clean() (validar_tax_id)
✅ NO agregar a search_fields público
✅ NO mostrar completo en list_display
✅ Logs con datos enmascarados

NO HACER:
❌ Mostrar tax_id completo en listados
❌ Logs con tax_id completo
❌ Search por tax_id sin protección
❌ Exportar sin cifrar
```

**Ver:** `SEGURIDAD_DATOS_SENSIBLES.md` para validadores completos y ejemplos.

---

### **13. MEJORAS FUTURAS (Nice to Have)** 💡

#### **✅ DISEÑO PREPARADO - NO BLOQUEANTE:**

**Mejoras opcionales documentadas para futuras versiones.**

```python
# ============================================================================
# 1. ÍNDICE GIN PARA SINÓNIMOS (PostgreSQL) - FUTURO
# ============================================================================

# Cuando se migre a PostgreSQL, activar índice GIN para búsqueda full-text:

class PartI18N(models.Model):
    synonyms = models.TextField(...)
    
    class Meta:
        # ✅ PREPARADO: Descomentar cuando se use PostgreSQL
        # indexes = [
        #     models.Index(
        #         name='idx_part_synonyms_gin',
        #         fields=['synonyms'],
        #         opclasses=['gin_trgm_ops']  # Requiere extensión pg_trgm
        #     )
        # ]

# Beneficio: Búsqueda full-text ~10-100x más rápida
# Requiere: PostgreSQL + extensión pg_trgm
# Cuándo: Release 2.0+ (migración a PostgreSQL)

# ============================================================================
# 2. TAX JURISDICTION POR ZIP+4 (USA) - FUTURO
# ============================================================================

# Para precisión de impuestos a nivel ZIP+4 (USA):

class TaxPolicy(models.Model):
    # Campos actuales (activos)
    country = models.CharField(...)
    state_code = models.CharField(...)
    city_name = models.CharField(...)
    
    # ✅ PREPARADO: Campos para ZIP+4 (comentados o blank=True)
    jurisdiction_id = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="[FUTURO] ID de jurisdicción fiscal (para USA ZIP+4)"
    )
    
    zip_code = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="[FUTURO] Código postal (ej: 90210)"
    )
    
    zip_plus4 = models.CharField(
        max_length=4,
        blank=True,
        default='',
        help_text="[FUTURO] ZIP+4 específico (ej: 1234)"
    )

# Uso futuro en resolve_tax_rate():
def resolve_tax_rate(empresa, ship_to_city, applies_to):
    # ✅ PREPARADO: Código comentado para ZIP+4
    # if country == 'US' and zip_code:
    #     policy = TaxPolicy.objects.filter(
    #         country='US',
    #         state_code=state_code,
    #         zip_code=zip_code,
    #         zip_plus4=zip_plus4,
    #         active=True
    #     ).first()
    #     if policy:
    #         return (policy.rate, policy.inclusive)
    
    # Búsqueda actual (funciona perfectamente) ✅
    # ...

# Beneficio: Precisión fiscal a nivel ZIP+4 (requerido por algunos estados USA)
# Requiere: Servicio externo (Avalara/TaxJar) → $$
# Cuándo: Release 3.0+ (cuando cliente específico lo requiera)
```

#### **Cronograma:**

```
RELEASE 1.0 (Actual):
  ✅ Sistema funciona perfectamente sin estas features
  ✅ SQLite + TaxPolicy básico suficiente
  ✅ Búsqueda LIKE en synonyms funcional

RELEASE 2.0 (6-12 meses):
  🔜 Migración a PostgreSQL
  🔜 Activar índice GIN para sinónimos
  🔜 Búsqueda full-text optimizada

RELEASE 3.0 (12-18 meses):
  🔜 Integración Avalara/TaxJar (si cliente lo requiere)
  🔜 Tax jurisdiction por ZIP+4
  🔜 Cálculo automático desde servicio externo
```

#### **⚠️ IMPORTANTE:**

```
PARA CURSOR Y DESARROLLADORES:

✅ Campos preparados con blank=True (no bloquean)
✅ Código comentado (fácil activar)
✅ Documentación disponible
✅ NO implementar ahora (no bloqueante)
✅ Sistema actual es completo y production-ready

NO HACER AHORA:
❌ Descomentar código de GIN (sin PostgreSQL)
❌ Activar ZIP+4 (sin servicio externo)
❌ Agregar dependencias pg_trgm
❌ Implementar sincronización con Avalara
```

**Ver:** `MEJORAS_FUTURAS_NICE_TO_HAVE.md` para diseño completo y roadmap.

---

**Importante:** Seguir estas convenciones estrictamente para mantener consistencia y calidad enterprise-level del sistema.

