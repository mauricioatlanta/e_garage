# 🛠️ MÉTODOS UTILITARIOS EN CATÁLOGO - Implementación Completa

## 🎯 **OBJETIVO**

Implementar métodos utilitarios claros y consistentes en `Part` y `Service` para evitar improvisaciones en el código y garantizar una API uniforme.

---

## ✅ **MÉTODOS IMPLEMENTADOS**

### **1. Part.get_display_name(locale)** ✅
### **2. Part.get_price(empresa, fecha)** ✅
### **3. Service.get_display_name(locale)** ✅
### **4. Service.get_price(empresa, fecha)** ✅

---

## 📚 **1. get_display_name(locale)**

### **Propósito:**
Obtener el nombre localizado de un repuesto o servicio con fallback inteligente.

### **Estrategia de Fallback:**
```
1. Locale exacto (ej: es-PE) → Si existe, usar
2. es-CL (idioma por defecto) → Fallback principal
3. Primer I18N disponible → Cualquier idioma
4. SKU/code → Último recurso
```

---

### **Implementación en Part:**

```python
class Part(models.Model):
    def get_display_name(self, locale='es-CL'):
        """
        Obtener nombre localizado del repuesto con fallback inteligente.
        
        Estrategia de fallback:
        1. Buscar locale exacto (ej: es-PE)
        2. Fallback a es-CL (idioma por defecto del sistema)
        3. Fallback al primer I18N disponible
        4. Fallback al SKU si no hay I18N
        
        Args:
            locale (str): Código de locale (ej: 'es-CL', 'en-US', 'pt-BR')
        
        Returns:
            str: Nombre localizado o SKU como fallback
        """
        # 1. Intentar locale exacto
        try:
            i18n = self.i18n.get(locale=locale)
            return i18n.display_name
        except PartI18N.DoesNotExist:
            pass
        
        # 2. Fallback a es-CL (idioma por defecto)
        if locale != 'es-CL':
            try:
                i18n = self.i18n.get(locale='es-CL')
                return i18n.display_name
            except PartI18N.DoesNotExist:
                pass
        
        # 3. Fallback al primer I18N disponible
        i18n = self.i18n.first()
        if i18n:
            return i18n.display_name
        
        # 4. Fallback al SKU
        return self.sku
```

---

### **Ejemplos de Uso:**

```python
# Ejemplo 1: Locale exacto existe
part = Part.objects.get(sku='OIL-5W30-4L')
name = part.get_display_name('es-CL')
print(name)  # "Aceite de Motor 5W30 4 Litros"

# Ejemplo 2: Locale no existe, fallback a es-CL
name = part.get_display_name('es-PE')
print(name)  # "Aceite de Motor 5W30 4 Litros" (de es-CL)

# Ejemplo 3: es-CL no existe, usa primer disponible
# Supongamos que solo existe en-US
name = part.get_display_name('fr-FR')
print(name)  # "Engine Oil 5W30 4 Liters" (primer disponible)

# Ejemplo 4: Sin I18N, fallback a SKU
part_new = Part.objects.create(sku='NEW-PART-123', ...)
name = part_new.get_display_name('es-CL')
print(name)  # "NEW-PART-123" (SKU)
```

---

### **Casos de Uso en Templates:**

```django
<!-- Document line -->
<tr>
    <td>{{ linea.part.sku }}</td>
    <td>{{ linea.part.get_display_name|default:linea.nombre }}</td>
    <td>{{ linea.cantidad }}</td>
    <td>{{ linea.precio_unitario }}</td>
</tr>

<!-- Invoice PDF -->
<h3>{{ part.get_display_name:request.LANGUAGE_CODE }}</h3>
```

---

## 💰 **2. get_price(empresa, fecha=None)**

### **Propósito:**
Obtener el precio vigente de un repuesto o servicio para una empresa en una fecha específica.

### **Estrategia de Búsqueda:**
```
1. Precio de empresa específica vigente → Prioridad
2. Precio global (company=NULL) → Fallback
3. None → Si no existe precio
```

### **Lógica de Vigencia:**
```
Precio vigente si:
  fecha >= valid_from  AND  (fecha <= valid_to  OR  valid_to IS NULL)
```

---

### **Implementación en Part:**

```python
class Part(models.Model):
    def get_price(self, empresa, fecha=None):
        """
        Obtener precio vigente para una empresa en una fecha específica.
        
        Estrategia de búsqueda:
        1. Buscar precio de la empresa específica vigente en la fecha
        2. Fallback a precio global (company=NULL) si está permitido
        
        Args:
            empresa (Empresa): Empresa para la cual obtener el precio
            fecha (date, optional): Fecha de vigencia. Por defecto: hoy
        
        Returns:
            PartPrice or None: Registro de precio vigente, o None si no existe
        """
        from datetime import date
        
        if fecha is None:
            fecha = date.today()
        
        # 1. Buscar precio de la empresa específica
        price = self.prices.filter(
            company=empresa,
            valid_from__lte=fecha
        ).filter(
            models.Q(valid_to__gte=fecha) | models.Q(valid_to__isnull=True)
        ).order_by('-valid_from').first()
        
        if price:
            return price
        
        # 2. Fallback a precio global (company=NULL) si existe
        price_global = self.prices.filter(
            company__isnull=True,
            valid_from__lte=fecha
        ).filter(
            models.Q(valid_to__gte=fecha) | models.Q(valid_to__isnull=True)
        ).order_by('-valid_from').first()
        
        return price_global
```

---

### **Ejemplos de Uso:**

```python
from datetime import date

# Ejemplo 1: Obtener precio actual (hoy)
part = Part.objects.get(sku='OIL-5W30-4L')
price_record = part.get_price(empresa)

if price_record:
    print(f"{price_record.currency} {price_record.price}")
    # "CLP 25000"
else:
    print("Sin precio configurado")

# Ejemplo 2: Obtener precio en fecha específica
price_record = part.get_price(empresa, date(2025, 6, 15))
if price_record:
    print(f"Precio en junio 2025: {price_record.price}")

# Ejemplo 3: Usar en documento
for linea in documento.lineas_repuesto.all():
    price_record = linea.part.get_price(documento.empresa)
    if price_record:
        linea.precio_unitario = price_record.price
        linea.save()

# Ejemplo 4: Comparar precio actual vs precio de empresa
price_company = part.get_price(empresa)
price_global = part.prices.filter(company__isnull=True).first()

if price_company and price_global:
    print(f"Precio empresa: {price_company.price}")
    print(f"Precio catálogo: {price_global.price}")
    print(f"Descuento: {price_global.price - price_company.price}")
```

---

### **Casos de Uso en Views:**

```python
# View: Crear línea de repuesto
def agregar_repuesto_a_documento(request, documento_id, part_id):
    documento = Documento.objects.get(pk=documento_id)
    part = Part.objects.get(pk=part_id)
    
    # Obtener precio vigente automáticamente
    price_record = part.get_price(documento.empresa)
    
    if not price_record:
        return JsonResponse({
            'error': f'No hay precio configurado para {part.sku}'
        }, status=400)
    
    # Crear línea con precio vigente
    linea = LineaRepuesto.objects.create(
        documento=documento,
        part=part,
        nombre=part.get_display_name(request.LANGUAGE_CODE),  # ✅ Congelar nombre
        cantidad=1,
        precio_unitario=price_record.price
    )
    
    return JsonResponse({'success': True, 'linea_id': linea.id})
```

---

## 🔄 **Service: Misma Implementación**

### **Service.get_display_name(locale):**

```python
class Service(models.Model):
    def get_display_name(self, locale='es-CL'):
        """Igual que Part.get_display_name()"""
        # 1. Locale exacto
        try:
            i18n = self.i18n_catalog.get(locale=locale)
            return i18n.display_name
        except ServiceI18N.DoesNotExist:
            pass
        
        # 2. Fallback a es-CL
        if locale != 'es-CL':
            try:
                i18n = self.i18n_catalog.get(locale='es-CL')
                return i18n.display_name
            except ServiceI18N.DoesNotExist:
                pass
        
        # 3. Primer I18N disponible
        i18n = self.i18n_catalog.first()
        if i18n:
            return i18n.display_name
        
        # 4. Fallback al code
        return self.code
```

---

### **Service.get_price(empresa, fecha):**

```python
class Service(models.Model):
    def get_price(self, empresa, fecha=None):
        """Igual que Part.get_price()"""
        from datetime import date
        
        if fecha is None:
            fecha = date.today()
        
        # 1. Precio de empresa
        price = self.prices.filter(
            company=empresa,
            valid_from__lte=fecha
        ).filter(
            models.Q(valid_to__gte=fecha) | models.Q(valid_to__isnull=True)
        ).order_by('-valid_from').first()
        
        if price:
            return price
        
        # 2. Fallback global
        price_global = self.prices.filter(
            company__isnull=True,
            valid_from__lte=fecha
        ).filter(
            models.Q(valid_to__gte=fecha) | models.Q(valid_to__isnull=True)
        ).order_by('-valid_from').first()
        
        return price_global
```

---

## 📊 **TABLA COMPARATIVA**

| Método | Part | Service | Fallback |
|--------|------|---------|----------|
| **get_display_name()** | ✅ | ✅ | locale → es-CL → primer I18N → SKU/code |
| **get_price()** | ✅ | ✅ | empresa → global → None |

---

## 🎯 **CASOS DE USO REALES**

### **Caso 1: Crear Documento con Items del Catálogo**

```python
def crear_documento_desde_catalogo(empresa, cliente, items_data):
    """
    Crear documento automáticamente desde catálogo.
    
    items_data = [
        {'type': 'part', 'sku': 'OIL-5W30', 'cantidad': 2},
        {'type': 'service', 'code': 'OIL_CHANGE', 'cantidad': 1},
    ]
    """
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        tipo='PRESUPUESTO'
    )
    
    locale = cliente.get_locale()  # ej: 'es-PE'
    
    for item_data in items_data:
        if item_data['type'] == 'part':
            part = Part.objects.get(sku=item_data['sku'])
            price_record = part.get_price(empresa)  # ✅ Obtener precio
            
            if price_record:
                LineaRepuesto.objects.create(
                    documento=documento,
                    part=part,
                    nombre=part.get_display_name(locale),  # ✅ Nombre localizado
                    cantidad=item_data['cantidad'],
                    precio_unitario=price_record.price
                )
        
        elif item_data['type'] == 'service':
            service = Service.objects.get(code=item_data['code'])
            price_record = service.get_price(empresa)  # ✅ Obtener precio
            
            if price_record:
                LineaServicio.objects.create(
                    documento=documento,
                    service=service,
                    nombre=service.get_display_name(locale),  # ✅ Nombre localizado
                    cantidad=item_data['cantidad'],
                    precio_unitario=price_record.price
                )
    
    return documento
```

---

### **Caso 2: API REST para Catálogo**

```python
@api_view(['GET'])
def catalog_item_detail(request, item_type, item_id):
    """
    Detalle de item del catálogo con precio para la empresa del usuario.
    
    GET /api/catalog/part/123/
    GET /api/catalog/service/456/
    """
    locale = request.GET.get('locale', 'es-CL')
    empresa = request.user.empresa
    
    if item_type == 'part':
        item = Part.objects.get(pk=item_id)
    elif item_type == 'service':
        item = Service.objects.get(pk=item_id)
    else:
        return Response({'error': 'Invalid type'}, status=400)
    
    # Usar métodos utilitarios
    price_record = item.get_price(empresa)  # ✅
    display_name = item.get_display_name(locale)  # ✅
    
    return Response({
        'id': item.id,
        'sku_or_code': item.sku if item_type == 'part' else item.code,
        'display_name': display_name,
        'price': {
            'amount': price_record.price if price_record else None,
            'currency': price_record.currency if price_record else None,
            'valid_from': price_record.valid_from if price_record else None,
            'valid_to': price_record.valid_to if price_record else None,
        },
        'available': bool(price_record)
    })
```

---

### **Caso 3: Template con Catálogo Multi-idioma**

```django
<!-- Listado de repuestos para un taller chileno -->
{% for part in parts %}
<tr>
    <td>{{ part.sku }}</td>
    <td>{{ part.get_display_name }}</td>  {# Usa es-CL por defecto #}
    <td>
        {% with price=part.get_price:request.user.empresa %}
            {% if price %}
                {{ price.currency }} {{ price.price|floatformat:0 }}
            {% else %}
                <span class="text-muted">Sin precio</span>
            {% endif %}
        {% endwith %}
    </td>
</tr>
{% endfor %}
```

---

## 🚫 **ANTI-PATRONES (NO HACER)**

### **❌ Mal: Código improvisado sin métodos utilitarios**

```python
# ❌ NO: Lógica dispersa y duplicada
def get_part_name(part, locale):
    try:
        i18n = part.i18n.get(locale=locale)
        return i18n.display_name
    except:
        return part.sku  # ❌ Fallback incorrecto (no intenta es-CL)

def get_part_price(part, empresa):
    # ❌ Lógica de fechas incorrecta
    prices = part.prices.filter(company=empresa)
    if prices.exists():
        return prices.first().price
    return None  # ❌ No intenta fallback a global

# ❌ Duplicación en múltiples lugares
```

---

### **✅ Bien: Usar métodos utilitarios**

```python
# ✅ SÍ: API clara y consistente
name = part.get_display_name(locale)
price_record = part.get_price(empresa)

if price_record:
    print(f"{name}: {price_record.currency} {price_record.price}")
```

---

## 🧪 **TESTS**

### **Test 1: get_display_name() con fallbacks**

```python
import pytest
from datetime import date

@pytest.mark.django_db
def test_part_get_display_name_exact():
    """Locale exacto existe"""
    part = Part.objects.create(sku='TEST-001')
    PartI18N.objects.create(part=part, locale='es-CL', display_name='Prueba CL')
    
    assert part.get_display_name('es-CL') == 'Prueba CL'

@pytest.mark.django_db
def test_part_get_display_name_fallback_es_cl():
    """Fallback a es-CL"""
    part = Part.objects.create(sku='TEST-001')
    PartI18N.objects.create(part=part, locale='es-CL', display_name='Prueba CL')
    
    # Pedir es-PE, no existe, debe usar es-CL
    assert part.get_display_name('es-PE') == 'Prueba CL'

@pytest.mark.django_db
def test_part_get_display_name_fallback_first():
    """Fallback al primer I18N disponible"""
    part = Part.objects.create(sku='TEST-001')
    PartI18N.objects.create(part=part, locale='en-US', display_name='Test US')
    
    # No existe es-CL ni locale pedido, usa primer disponible
    assert part.get_display_name('fr-FR') == 'Test US'

@pytest.mark.django_db
def test_part_get_display_name_fallback_sku():
    """Fallback al SKU si no hay I18N"""
    part = Part.objects.create(sku='TEST-001')
    
    assert part.get_display_name('es-CL') == 'TEST-001'
```

---

### **Test 2: get_price() con fallbacks**

```python
@pytest.mark.django_db
def test_part_get_price_company_specific():
    """Precio de empresa específica"""
    empresa = Empresa.objects.create(nombre='Test')
    part = Part.objects.create(sku='TEST-001')
    
    price = PartPrice.objects.create(
        part=part,
        company=empresa,
        currency='CLP',
        price=10000,
        valid_from=date(2025, 1, 1)
    )
    
    result = part.get_price(empresa)
    assert result == price
    assert result.price == 10000

@pytest.mark.django_db
def test_part_get_price_fallback_global():
    """Fallback a precio global"""
    empresa = Empresa.objects.create(nombre='Test')
    part = Part.objects.create(sku='TEST-001')
    
    # Solo precio global (company=NULL)
    price_global = PartPrice.objects.create(
        part=part,
        company=None,
        currency='CLP',
        price=15000,
        valid_from=date(2025, 1, 1)
    )
    
    result = part.get_price(empresa)
    assert result == price_global
    assert result.price == 15000

@pytest.mark.django_db
def test_part_get_price_date_specific():
    """Precio vigente en fecha específica"""
    empresa = Empresa.objects.create(nombre='Test')
    part = Part.objects.create(sku='TEST-001')
    
    # Precio vigente hasta junio
    PartPrice.objects.create(
        part=part,
        company=empresa,
        currency='CLP',
        price=10000,
        valid_from=date(2025, 1, 1),
        valid_to=date(2025, 6, 30)
    )
    
    # Precio vigente desde julio
    price_new = PartPrice.objects.create(
        part=part,
        company=empresa,
        currency='CLP',
        price=12000,
        valid_from=date(2025, 7, 1)
    )
    
    # En mayo, debe usar primer precio
    result_may = part.get_price(empresa, date(2025, 5, 15))
    assert result_may.price == 10000
    
    # En agosto, debe usar segundo precio
    result_aug = part.get_price(empresa, date(2025, 8, 15))
    assert result_aug.price == 12000

@pytest.mark.django_db
def test_part_get_price_none():
    """Sin precio configurado"""
    empresa = Empresa.objects.create(nombre='Test')
    part = Part.objects.create(sku='TEST-001')
    
    result = part.get_price(empresa)
    assert result is None
```

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

- [✅] Part.get_display_name() implementado
- [✅] Part.get_price() implementado
- [✅] Service.get_display_name() implementado
- [✅] Service.get_price() implementado
- [✅] Fallback a es-CL
- [✅] Fallback a primer I18N
- [✅] Fallback a SKU/code
- [✅] Fallback a precio global
- [✅] Lógica de vigencia correcta
- [✅] order_by('-valid_from') para más reciente
- [✅] Documentación completa
- [✅] Ejemplos de uso
- [✅] Tests documentados
- [✅] Django check passing

---

## 🎯 **BENEFICIOS**

```
✅ API clara y consistente
✅ Evita improvisaciones
✅ Fallbacks inteligentes
✅ Código reutilizable
✅ Fácil de mantener
✅ Fácil de testear
✅ Documentación completa
```

---

## 📋 **ARCHIVOS MODIFICADOS**

1. ✅ `taller/models/catalogo_repuestos.py`
   - Part.get_display_name() mejorado
   - Part.get_price() agregado

2. ✅ `taller/models/catalogo_servicios.py`
   - Service.get_display_name() mejorado
   - Service.get_price() agregado

---

## 🚀 **USO RECOMENDADO**

### **Siempre usar estos métodos en lugar de:**

```python
# ❌ NO hacer:
name = part.i18n.get(locale='es-CL').display_name  # Puede fallar
price = part.prices.filter(company=empresa).first().price  # Lógica incorrecta

# ✅ SÍ hacer:
name = part.get_display_name('es-CL')  # Nunca falla, siempre retorna algo
price_record = part.get_price(empresa)  # Lógica completa con fallbacks
if price_record:
    price = price_record.price
```

---

**Estado:** ✅ **MÉTODOS UTILITARIOS IMPLEMENTADOS Y DOCUMENTADOS**

**Próximo paso:** Usar estos métodos en views, templates y APIs

**¡API clara y consistente para evitar improvisaciones!** 🛠️

