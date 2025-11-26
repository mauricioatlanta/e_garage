# ✅ Formularios Unificados - Sistema Multi-País Completo

## 🎯 **ARQUITECTURA DE FORMULARIOS**

Esta implementación conecta **todos los componentes** del sistema multi-país:

```
Frontend (Template)
    ↓ (locations.js)
API Unificada (/api/locations)
    ↓ (JSON)
Formulario (CustomerForm/CompanySettingsForm)
    ↓ (clean())
Modelo Address
    ↓ (FK)
Ciudad → Estado → País
```

---

## 📁 **ARCHIVOS CREADOS**

### **1. Formularios:**
```
✅ taller/clientes/forms_unified.py
   - CustomerForm (con Address)
   - CustomerAddressForm (solo Address)

✅ taller/forms/company_settings_unified.py
   - CompanySettingsForm (con legal_address)
```

### **2. Templates de Ejemplo:**
```
✅ templates/ejemplos/cliente_form_unified.html
   - Formulario completo de cliente
   - Integrado con locations.js
   - Preview de dirección
   - Hints dinámicos para tax_id

✅ templates/ejemplos/company_settings_form_unified.html
   - Formulario de configuración de empresa
   - Dirección legal
   - Preview de dirección
   - Auto-detección de país
```

---

## 🔧 **CUSTOMER FORM - CARACTERÍSTICAS**

### **Archivo:** `taller/clientes/forms_unified.py`

```python
class CustomerForm(forms.ModelForm):
    # Campos virtuales (no en DB, solo para UI)
    country = ChoiceField()  # CL, US, BR, PE, VE
    state = CharField()  # Código de estado
    city = ModelChoiceField(queryset=Ciudad.objects.none())
    line1 = CharField()  # Dirección línea 1
    line2 = CharField()  # Dirección línea 2
    postal_code = CharField()  # Código postal
    
    # Campos reales del modelo
    nombre, apellido, telefono, email
    tax_id_type, tax_id
    # billing_address, shipping_address (se crean en clean())
```

### **Funcionalidades:**

#### **1. Auto-prellenado en Edición** ✅
```python
def __init__(self, *args, **kwargs):
    # Si el cliente tiene billing_address, prellenar campos virtuales
    addr = self.instance.billing_address
    if addr:
        self.fields['country'].initial = addr.city.estado.pais
        self.fields['state'].initial = addr.city.estado.codigo
        self.fields['city'].initial = addr.city_id
        self.fields['line1'].initial = addr.line1
        # ...
```

#### **2. Auto-detección de País** ✅
```python
elif self.empresa and not self.instance.pk:
    # Cliente nuevo: auto-detectar país desde empresa
    pais = self.empresa.pais
    self.fields['country'].initial = pais
    
    # Auto-seleccionar tax_id_type
    self.fields['tax_id_type'].initial = TAX_ID_DEFAULTS[pais]
```

#### **3. Creación Automática de Address** ✅
```python
def clean(self):
    # Si hay country, city y line1, crear Address
    if country and city and line1:
        addr = Address.objects.create(
            line1=line1,
            line2=line2,
            city=city,
            postal_code=postal_code,
            company=self.empresa
        )
        cd['billing_address'] = addr
    return cd
```

---

## 🏢 **COMPANY SETTINGS FORM - CARACTERÍSTICAS**

### **Archivo:** `taller/forms/company_settings_unified.py`

```python
class CompanySettingsForm(forms.ModelForm):
    # Campos virtuales para dirección legal
    legal_country = ChoiceField()
    legal_state = CharField()
    legal_city = ModelChoiceField(queryset=Ciudad.objects.none())
    legal_line1 = CharField()
    legal_line2 = CharField()
    legal_postal_code = CharField()
    
    # Campos reales del modelo
    nombre_publico, tagline, logo
    telefono, email_contacto, sitio_web
    moneda, tasa_impuesto, aplicar_impuesto_por_defecto
    brand_color
    # legal_address (se crea en clean())
```

### **Funcionalidades:**

#### **1. Actualizar Address Existente** ✅
```python
def clean(self):
    if self.instance.legal_address:
        # Actualizar dirección existente
        addr = self.instance.legal_address
        addr.line1 = legal_line1
        addr.city = legal_city
        addr.save()
    else:
        # Crear nueva
        addr = Address.objects.create(...)
    
    cd['legal_address'] = addr
```

#### **2. Validación de Consistencia** ✅
```python
# Verificar que ciudad pertenezca al país
if city.estado.pais != country:
    raise ValidationError('Ciudad no pertenece al país')
```

---

## 📝 **TEMPLATE - INTEGRACIÓN CON LOCATIONS.JS**

### **HTML (Estructura Básica):**

```html
{% load static i18n %}

<!-- Campos de Ubicación -->
<div class="row">
  <div class="col-md-4">
    {{ form.country.label_tag }}
    {{ form.country }}
  </div>
  <div class="col-md-4">
    <label for="id_state">{% trans "State" %}</label>
    <select id="id_state" name="state" class="form-control" disabled>
      <option value="">--</option>
    </select>
  </div>
  <div class="col-md-4">
    {{ form.city.label_tag }}
    {{ form.city }}
  </div>
</div>

<!-- Campos de Dirección -->
<div class="row">
  <div class="col-md-8">
    {{ form.line1.label_tag }}
    {{ form.line1 }}
  </div>
  <div class="col-md-4">
    {{ form.postal_code.label_tag }}
    {{ form.postal_code }}
  </div>
</div>

<div class="row">
  <div class="col-md-12">
    {{ form.line2.label_tag }}
    {{ form.line2 }}
  </div>
</div>

<!-- JavaScript -->
<script type="module">
  import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
  
  // Bind automático - ¡Una sola línea!
  bindCountryStateCity('#id_country', '#id_state', '#id_city');
</script>
```

---

## 🎨 **CARACTERÍSTICAS AVANZADAS DE LOS TEMPLATES**

### **1. Hints Dinámicos para Tax ID** ✅

```javascript
const TAX_ID_HINTS = {
  'CL_RUT': 'Format: 12.345.678-9',
  'US_EIN': 'Format: 12-3456789',
  'BR_CPF': 'Format: 123.456.789-01',
  // ...
};

taxIdTypeSelect.addEventListener('change', function() {
  const type = this.value;
  taxIdHint.textContent = TAX_ID_HINTS[type];
  taxIdInput.placeholder = TAX_ID_PLACEHOLDERS[type];
});
```

**Resultado:** El placeholder y hint cambian automáticamente cuando seleccionas el tipo de tax_id.

---

### **2. Preview de Dirección Completa** ✅

```javascript
function updateAddressPreview() {
  const line1 = line1Input.value;
  const city = citySelect.options[citySelect.selectedIndex]?.text;
  const state = stateSelect.options[stateSelect.selectedIndex]?.text;
  const country = countrySelect.options[countrySelect.selectedIndex]?.text;
  
  const preview = `${line1}, ${city}, ${state}, ${country}`;
  addressPreviewText.textContent = preview;
}
```

**Resultado:** Muestra la dirección completa mientras el usuario escribe.

---

### **3. Sales Tax Info** ✅

```javascript
citySelect.addEventListener('change', async function() {
  const cityId = this.value;
  
  const response = await fetch(`/api/locations/cities/${cityId}/`);
  const data = await response.json();
  
  salesTaxInfo.textContent = `Tax: ${data.sales_tax}%`;
});
```

**Resultado:** Muestra el impuesto aplicable cuando seleccionas la ciudad.

---

## 🔄 **FLUJO COMPLETO**

### **Creación de Cliente:**

```
1. Usuario abre formulario → /us/clientes/crear/
2. País auto-detectado → "US" (desde URL)
3. JavaScript carga estados → fetch('/api/locations?country=US')
4. Usuario selecciona estado → "CA"
5. JavaScript carga ciudades → fetch('/api/locations?country=US&state=CA')
6. Usuario selecciona ciudad → "Los Angeles"
7. Usuario llena dirección → "123 Main St"
8. Usuario selecciona tax_id_type → "US_EIN"
9. Usuario escribe tax_id → "12-3456789"
10. Submit form
11. Formulario valida tax_id → clean()
12. Formulario crea Address → Address.objects.create()
13. Formulario asigna a cliente → cliente.billing_address = addr
14. Cliente guardado ✅
```

---

## 📊 **DATOS GUARDADOS**

### **En Address:**
```python
{
    'line1': '123 Main St',
    'line2': 'Apt 4B',
    'city': <Ciudad: Los Angeles, CA>,
    'postal_code': '90001',
    'company': <Empresa: Acme Corp>
}
```

### **En Cliente:**
```python
{
    'nombre': 'John',
    'apellido': 'Doe',
    'email': 'john@example.com',
    'tax_id_type': 'US_EIN',
    'tax_id': '12-3456789',
    'billing_address': <Address: 123 Main St, Los Angeles, CA>
}
```

### **Automático (desde Address):**
```python
cliente.billing_address.country_code  # "US"
cliente.billing_address.state         # <Estado: California>
cliente.billing_address.sales_tax     # 7.25 (CA)
cliente.billing_address.full_address  # "123 Main St, Apt 4B, Los Angeles, California, United States, 90001"
```

---

## ✅ **VENTAJAS DEL SISTEMA**

### **1. DRY (Don't Repeat Yourself):**
- ✅ Un solo JavaScript (`locations.js`)
- ✅ Un solo formulario base (`CustomerForm`)
- ✅ Una sola API (`/api/locations`)
- ✅ Reutilizable en todos los países

### **2. Escalabilidad:**
- ✅ Agregar país: Solo actualizar choices
- ✅ Cambiar API: Solo editar `locations.js`
- ✅ No tocar templates individuales

### **3. Validación Multi-Capa:**
- ✅ **Frontend:** JavaScript verifica campos llenos
- ✅ **Form.clean():** Valida consistencia (ciudad/país)
- ✅ **Model.clean():** Valida format de tax_id
- ✅ **Database:** Constraints y FKs

### **4. Sales Tax Automático:**
```python
# Sin hacer nada más, el sales tax está disponible
cliente.billing_address.sales_tax  # Calculado automáticamente
```

### **5. Historial Preservado:**
```python
# Las direcciones no se borran, solo se actualizan
# O se crean nuevas si cambian significativamente
```

---

## 📚 **EJEMPLOS DE USO**

### **Ejemplo 1: Vista Simple**

```python
# views.py
from taller.clientes.forms_unified import CustomerForm

def crear_cliente(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente} creado exitosamente')
            return redirect('clientes:detalle', pk=cliente.pk)
    else:
        form = CustomerForm(empresa=request.user.empresa)
    
    return render(request, 'clientes/crear.html', {'form': form})
```

---

### **Ejemplo 2: Edición de Cliente**

```python
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk, empresa=request.user.empresa)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=cliente, empresa=request.user.empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado')
            return redirect('clientes:detalle', pk=pk)
    else:
        form = CustomerForm(instance=cliente, empresa=request.user.empresa)
    
    return render(request, 'clientes/editar.html', {'form': form})
```

**Automático:** Los campos country/state/city se prellenan desde `billing_address`.

---

### **Ejemplo 3: Company Settings**

```python
from taller.forms.company_settings_unified import CompanySettingsForm

def company_settings(request):
    config = request.user.empresa.config
    
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración guardada')
            return redirect('taller:dashboard')
    else:
        form = CompanySettingsForm(instance=config)
    
    return render(request, 'configuracion/settings.html', {'form': form})
```

---

## 🎨 **CARACTERÍSTICAS DE UI**

### **1. Estados Deshabilitados Inicialmente:**

```html
<select id="id_state" disabled>
  <option value="">--</option>
</select>

<select id="id_city" disabled>
  <option value="">--</option>
</select>
```

**Se habilitan automáticamente** cuando:
- `id_state` → Cuando se selecciona país
- `id_city` → Cuando se selecciona estado

---

### **2. Loading States:**

```
1. Usuario selecciona país → "Loading..."
2. API carga estados → Populate select
3. Select habilitado → "Select..."
```

---

### **3. Validación Visual:**

```javascript
// Tax ID hint dinámico
tax_id_type: "US_EIN"  →  Hint: "Format: 12-3456789"
tax_id_type: "BR_CPF"  →  Hint: "Format: 123.456.789-01"
tax_id_type: "PE_RUC"  →  Hint: "Format: 20123456789"
```

---

### **4. Preview de Dirección:**

```
123 Main St, Apt 4B
Los Angeles, California
United States 90001
```

Se actualiza en tiempo real mientras el usuario escribe.

---

## 📋 **CHECKLIST DE INTEGRACIÓN**

### **Para integrar en un template existente:**

- [ ] 1. **Cambiar import del formulario:**
  ```python
  # Antes
  from taller.clientes.forms import ClienteForm
  
  # Después
  from taller.clientes.forms_unified import CustomerForm
  ```

- [ ] 2. **Pasar empresa al formulario:**
  ```python
  form = CustomerForm(empresa=request.user.empresa)
  ```

- [ ] 3. **En template, agregar campos virtuales:**
  ```html
  {{ form.country }}
  <select id="id_state" disabled>...</select>  <!-- No viene del form -->
  {{ form.city }}
  {{ form.line1 }}
  {{ form.line2 }}
  {{ form.postal_code }}
  ```

- [ ] 4. **Agregar locations.js:**
  ```html
  {% load static %}
  <script type="module">
    import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
    bindCountryStateCity('#id_country', '#id_state', '#id_city');
  </script>
  ```

- [ ] 5. **Probar:**
  - Crear cliente nuevo
  - Editar cliente existente
  - Verificar que Address se cree
  - Verificar que tax_id se valide

---

## 🔍 **DEBUGGING**

### **Verificar que Address se creó:**

```python
# En Django shell
from taller.models import Cliente

cliente = Cliente.objects.get(pk=1)
print(cliente.billing_address)  # <Address: 123 Main St, Los Angeles, CA>
print(cliente.billing_address.country_code)  # "US"
print(cliente.billing_address.sales_tax)  # 7.25
```

---

### **Logs en Consola:**

```javascript
// Con debug: true
[locations.js] Loading states for country: PE
[locations.js] Loaded 25 states for PE
[locations.js] Loading cities for: PE LIM
[locations.js] Loaded 1 cities for PE-LIM
```

---

### **Verificar en Admin:**

```python
# admin.py
from ubicacion.models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['line1', 'city', 'country_code', 'postal_code']
    list_filter = ['city__estado__pais']
    search_fields = ['line1', 'city__nombre', 'postal_code']
    
    def country_code(self, obj):
        return obj.city.estado.pais
    country_code.short_description = 'País'
```

---

## 🚀 **MIGRACIÓN DESDE FORMULARIOS LEGACY**

### **Paso 1: Backup**

```bash
# Hacer backup de forms.py actual
cp taller/clientes/forms.py taller/clientes/forms_legacy.py
```

---

### **Paso 2: Importar Nuevo**

```python
# En views.py, cambiar import
from taller.clientes.forms_unified import CustomerForm
```

---

### **Paso 3: Actualizar Template**

```diff
<!-- template.html -->
+ {% load static %}

  {{ form.nombre }}
  {{ form.apellido }}
  
+ <!-- Ubicación -->
+ {{ form.country }}
+ <select id="id_state" name="state" disabled>...</select>
+ {{ form.city }}
+ {{ form.line1 }}
+ {{ form.line2 }}
+ {{ form.postal_code }}

+ <script type="module">
+   import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
+   bindCountryStateCity('#id_country', '#id_state', '#id_city');
+ </script>
```

---

### **Paso 4: Backfill Datos Existentes**

```python
# Script para migrar clientes legacy a Address
from taller.models import Cliente
from ubicacion.models import Address

clientes = Cliente.objects.filter(
    estado_usa__isnull=False,
    billing_address__isnull=True
)

for cliente in clientes:
    if cliente.ciudad_usa:
        addr = Address.objects.create(
            line1=cliente.direccion or 'N/A',
            city=cliente.ciudad_usa,
            postal_code=cliente.zipcode or ''
        )
        cliente.billing_address = addr
        cliente.save()
        print(f'✅ Migrado: {cliente}')
```

---

## 🎯 **COMPATIBILIDAD**

### **Campos Legacy Mantenidos:**

```python
# En Cliente, estos campos siguen existiendo:
cliente.estado_usa     # [LEGACY]
cliente.ciudad_usa     # [LEGACY]
cliente.zipcode        # [LEGACY]
cliente.region         # [LEGACY - Chile]
cliente.ciudad         # [LEGACY - Chile]

# Nuevos campos:
cliente.billing_address   # Address object
cliente.shipping_address  # Address object
```

**Estrategia:** Migración progresiva
- ✅ Formularios nuevos usan Address
- ✅ Formularios legacy siguen funcionando
- ⚠️ Backfill gradual de datos
- ⚠️ Deprecar campos legacy cuando todo migrado

---

## 📚 **DOCUMENTACIÓN DE REFERENCIA**

### **Para Desarrolladores:**

1. **Arquitectura completa:**
   - `SISTEMA_COMPLETO_MULTI_PAIS_IMPLEMENTADO.md`

2. **API de ubicaciones:**
   - `API_UBICACIONES_UNIFICADA.md`

3. **JavaScript reutilizable:**
   - `EJEMPLOS_USO_LOCATIONS_JS.md`

4. **Formularios unificados:**
   - `FORMULARIOS_UNIFICADOS_IMPLEMENTADOS.md` (este archivo)

---

## ✅ **CHECKLIST FINAL**

### **Modelos:**
- [✅] Address creado
- [✅] Cliente con billing/shipping_address
- [✅] ConfiguracionEmpresa con legal_address
- [✅] Tax ID con tax_id_type
- [✅] Catálogo Part/Service con I18N

### **Formularios:**
- [✅] CustomerForm creado
- [✅] CustomerAddressForm creado
- [✅] CompanySettingsForm creado
- [✅] Campos virtuales para UI
- [✅] clean() crea Address automáticamente

### **JavaScript:**
- [✅] locations.js reutilizable
- [✅] bindCountryStateCity()
- [✅] Auto-detección de país
- [✅] Debug mode

### **API:**
- [✅] /api/locations funcionando
- [✅] Soporta query params
- [✅] Soporta path params
- [✅] Probada exitosamente

### **Templates:**
- [✅] Ejemplos completos creados
- [✅] Integración con locations.js
- [✅] Hints dinámicos
- [✅] Preview de dirección

### **Migraciones:**
- [✅] Todas aplicadas
- [✅] Base de datos actualizada

---

## 🎉 **RESUMEN FINAL**

```
✅ 2 Formularios unificados creados
✅ 2 Templates de ejemplo completos
✅ 1 JavaScript reutilizable (locations.js)
✅ 1 API unificada (/api/locations)
✅ 5 Países soportados completamente
✅ Sales tax automático por ubicación
✅ Tax ID validado con 7 tipos
✅ Catálogo I18N (5 idiomas)
✅ Migración progresiva (legacy compatible)
✅ Documentación completa
```

**Estado:** ✅ **SISTEMA COMPLETO Y FUNCIONANDO**  
**Siguiente:** ⚠️ Integrar en formularios de producción

