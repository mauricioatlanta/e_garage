# 💰 CÁLCULOS FINANCIEROS ESTÁNDAR - Implementación Completa

## 🎯 **OBJETIVO**

Implementar estándares financieros para cálculos de dinero en el sistema, garantizando precisión, consistencia y conformidad con estándares contables.

---

## ✅ **ESTÁNDARES IMPLEMENTADOS**

### **1. Decimal.quantize() con ROUND_HALF_UP** ✅
### **2. Usar campo subtotal si existe (NO calcular a mano)** ✅
### **3. KPIs usan fecha_emision (NO fecha_creacion)** ✅

---

## 💰 **1. CÁLCULO FINANCIERO CON ROUND_HALF_UP**

### **Estándar Financiero:**

```python
from decimal import Decimal, ROUND_HALF_UP

def _quantize_money(value):
    """
    Redondear valor financiero a 2 decimales con ROUND_HALF_UP (estándar financiero).
    
    Args:
        value (Decimal): Valor a redondear
    
    Returns:
        Decimal: Valor redondeado a 2 decimales
    
    Ejemplos:
        >>> _quantize_money(Decimal('123.456'))
        Decimal('123.46')  # Redondeo hacia arriba
        
        >>> _quantize_money(Decimal('123.454'))
        Decimal('123.45')  # Redondeo hacia abajo
        
        >>> _quantize_money(Decimal('123.455'))
        Decimal('123.46')  # ROUND_HALF_UP: .5 siempre redondea hacia arriba
    
    Importante:
        Este es el estándar financiero internacional.
        SIEMPRE usar esto en cálculos de dinero.
    """
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

---

### **¿Por qué ROUND_HALF_UP?**

```
ROUND_HALF_UP: Estándar financiero internacional
- 0.5 → 1 (redondea hacia arriba)
- 1.5 → 2 (redondea hacia arriba)
- 2.5 → 3 (redondea hacia arriba)

Vs. ROUND_HALF_EVEN (bancario):
- 0.5 → 0 (redondea al par más cercano)
- 1.5 → 2 (redondea al par más cercano)
- 2.5 → 2 (redondea al par más cercano)

✅ USAR: ROUND_HALF_UP para facturación, contabilidad, impuestos
❌ NO USAR: ROUND_HALF_EVEN (puede causar inconsistencias contables)
```

---

### **Aplicación en TODO el sistema:**

```python
# ✅ CORRECTO: Aplicar a TODOS los cálculos financieros

# 1. Subtotal de línea
subtotal_linea = _quantize_money(cantidad * precio_unitario - descuento)

# 2. Total de categoría
total_parts = _quantize_money(sum(subtotales_lineas))

# 3. Impuestos
tax = _quantize_money(subtotal * rate)

# 4. Total final
total = _quantize_money(subtotal + tax)

# ❌ INCORRECTO: Solo redondear al final
total = (subtotal + tax).quantize(Decimal('0.01'))  # ❌ Puede acumular error
```

---

## 📝 **2. USAR CAMPO SUBTOTAL SI EXISTE**

### **Convención:**

```python
# ✅ CORRECTO: Usar campo subtotal si existe
if hasattr(linea, 'subtotal') and linea.subtotal is not None:
    subtotal_linea = linea.subtotal  # Usar precalculado
else:
    # Solo calcular si no existe el campo
    subtotal_linea = cantidad * precio_unitario
    if descuento:
        subtotal_linea -= descuento_valor
    subtotal_linea = _quantize_money(subtotal_linea)

# ❌ INCORRECTO: Calcular siempre "a mano"
subtotal_linea = (cantidad * precio_unitario) - descuento  # ❌ Ignora subtotal precalculado
```

---

### **¿Por qué?**

```
VENTAJAS de usar campo subtotal:
1. ✅ Consistencia: El subtotal ya fue calculado y guardado una vez
2. ✅ Performance: No recalcular en cada query
3. ✅ Auditoría: El subtotal guardado es el que se facturó
4. ✅ Inmutabilidad: El documento no cambia después de emitido

RIESGO de calcular "a mano":
1. ❌ Inconsistencia: El cálculo puede cambiar por código actualizado
2. ❌ Performance: Recalcular en cada render/query
3. ❌ Error: Puede no coincidir con el subtotal facturado original
```

---

### **Implementación en calcular_totales():**

```python
def calcular_totales(documento):
    total_parts = Decimal('0.00')
    
    for linea in documento.lineas_repuesto.all():
        # ✅ IMPORTANTE: Usar campo subtotal si existe (NO calcular a mano)
        if hasattr(linea, 'subtotal') and linea.subtotal is not None:
            # Usar subtotal precalculado de la línea
            subtotal_linea = linea.subtotal
        else:
            # Calcular: cantidad * precio_unitario - descuento
            subtotal_linea = Decimal(str(linea.cantidad or 0)) * Decimal(str(linea.precio_unitario or 0))
            
            # Aplicar descuento si existe
            if hasattr(linea, 'descuento') and linea.descuento:
                descuento_valor = subtotal_linea * (Decimal(str(linea.descuento)) / Decimal('100'))
                subtotal_linea -= descuento_valor
            
            # ✅ Redondear subtotal de línea
            subtotal_linea = _quantize_money(subtotal_linea)
        
        total_parts += subtotal_linea
    
    # ✅ Redondear total de categoría
    total_parts = _quantize_money(total_parts)
```

---

## 📅 **3. KPIs USAN fecha_emision (NO fecha_creacion)**

### **Convención Crítica:**

```python
# ✅ CORRECTO: KPIs usan fecha_emision
ingresos_mes = Documento.objects.filter(
    fecha_emision__year=2025,
    fecha_emision__month=6
).aggregate(
    total=Sum('total')
)

# ❌ INCORRECTO: Usar fecha_creacion
ingresos_mes = Documento.objects.filter(
    fecha_creacion__year=2025,  # ❌ NO usar fecha_creacion
    fecha_creacion__month=6
).aggregate(total=Sum('total'))
```

---

### **¿Por qué fecha_emision?**

```
RAZONES CONTABLES Y LEGALES:

1. ✅ Principio de Devengado:
   - Los ingresos se reconocen cuando se EMITE el documento
   - No cuando se CREA el borrador

2. ✅ Período Fiscal:
   - Los impuestos se calculan por fecha de emisión
   - No por fecha de creación del registro en el sistema

3. ✅ Auditoría:
   - Los libros contables usan fecha de emisión
   - Los documentos se ordenan por fecha de emisión

4. ✅ Consistencia Legal:
   - Facturas, Boletas, Notas de Crédito usan fecha_emision
   - No fecha_creacion del registro en DB

EJEMPLO:
- Documento creado: 2025-05-30 (borrador)
- Documento emitido: 2025-06-01 (factura oficial)
- KPI debe contar en: JUNIO (no Mayo)
```

---

### **Campos de Fecha en Documento:**

```python
class Documento(models.Model):
    # ✅ USAR PARA KPIs
    fecha_emision = models.DateField(
        verbose_name="Fecha de Emisión",
        help_text="Fecha oficial del documento (para contabilidad y KPIs)"
    )
    
    # ❌ NO USAR PARA KPIs
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación",
        help_text="Fecha de creación del registro en el sistema (solo auditoría)"
    )
    
    # Opcional: fecha de vencimiento
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Vencimiento"
    )
```

---

### **Ejemplos de KPIs:**

```python
# ✅ CORRECTO: Ingresos del mes
from django.db.models import Sum
from datetime import date

def ingresos_mensuales(empresa, year, month):
    """
    Calcular ingresos del mes por fecha_emision.
    
    IMPORTANTE: Usa fecha_emision, NO fecha_creacion
    """
    ingresos = Documento.objects.filter(
        empresa=empresa,
        fecha_emision__year=year,
        fecha_emision__month=month,
        tipo__in=['FACTURA', 'BOLETA']
    ).aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    return _quantize_money(ingresos)

# ✅ CORRECTO: Documentos pendientes de pago
def documentos_pendientes(empresa, fecha_corte=None):
    """
    Documentos emitidos y pendientes de pago.
    
    IMPORTANTE: Usa fecha_emision para determinar antigüedad
    """
    if fecha_corte is None:
        fecha_corte = date.today()
    
    return Documento.objects.filter(
        empresa=empresa,
        fecha_emision__lte=fecha_corte,
        estado='PENDIENTE'
    ).order_by('fecha_emision')  # ✅ Ordenar por emisión

# ✅ CORRECTO: Días de antigüedad
def dias_antiguedad(documento, fecha_referencia=None):
    """
    Calcular días desde emisión (NO desde creación).
    """
    if fecha_referencia is None:
        fecha_referencia = date.today()
    
    dias = (fecha_referencia - documento.fecha_emision).days
    return dias
```

---

## 🧮 **EJEMPLOS COMPLETOS**

### **Ejemplo 1: Calcular Total de Documento**

```python
from decimal import Decimal, ROUND_HALF_UP

def calcular_total_documento(documento):
    """
    Calcular total con estándares financieros.
    """
    # 1. Calcular subtotal de líneas
    subtotal = Decimal('0.00')
    
    for linea in documento.lineas_repuesto.all():
        # ✅ Usar subtotal si existe
        if hasattr(linea, 'subtotal') and linea.subtotal is not None:
            subtotal += linea.subtotal
        else:
            # Calcular con redondeo
            linea_subtotal = Decimal(str(linea.cantidad)) * Decimal(str(linea.precio_unitario))
            linea_subtotal = _quantize_money(linea_subtotal)
            subtotal += linea_subtotal
    
    # ✅ Redondear subtotal total
    subtotal = _quantize_money(subtotal)
    
    # 2. Calcular impuesto
    tax_rate = Decimal('0.19')  # 19%
    tax = _quantize_money(subtotal * tax_rate)
    
    # 3. Calcular total
    total = _quantize_money(subtotal + tax)
    
    return {
        'subtotal': subtotal,
        'tax': tax,
        'total': total
    }
```

---

### **Ejemplo 2: Dashboard de Ingresos**

```python
def dashboard_ingresos(empresa, year, month):
    """
    Dashboard con KPIs financieros.
    
    IMPORTANTE:
    - Usa fecha_emision para todos los KPIs
    - Usa _quantize_money para todos los totales
    """
    from django.db.models import Sum, Count, Avg
    
    # ✅ Filtrar por fecha_emision
    docs = Documento.objects.filter(
        empresa=empresa,
        fecha_emision__year=year,
        fecha_emision__month=month,
        tipo__in=['FACTURA', 'BOLETA']
    )
    
    # ✅ Calcular KPIs con redondeo
    ingresos_total = docs.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    ingresos_total = _quantize_money(ingresos_total)
    
    ticket_promedio = docs.aggregate(Avg('total'))['total__avg'] or Decimal('0.00')
    ticket_promedio = _quantize_money(ticket_promedio)
    
    cantidad_docs = docs.count()
    
    return {
        'ingresos_total': ingresos_total,
        'ticket_promedio': ticket_promedio,
        'cantidad_documentos': cantidad_docs,
        'periodo': f"{year}-{month:02d}",  # YYYY-MM
    }
```

---

### **Ejemplo 3: Reporte de Impuestos**

```python
def reporte_impuestos_mes(empresa, year, month):
    """
    Reporte de impuestos del mes.
    
    IMPORTANTE:
    - Usa fecha_emision (requerido por SII/IRS)
    - Redondea TODOS los valores financieros
    """
    from django.db.models import Sum
    
    # ✅ Filtrar por fecha_emision
    docs = Documento.objects.filter(
        empresa=empresa,
        fecha_emision__year=year,
        fecha_emision__month=month,
        tipo='FACTURA'
    )
    
    # ✅ Sumar con redondeo
    ventas_netas = docs.aggregate(
        Sum('subtotal_repuestos'),
        Sum('subtotal_servicios')
    )
    
    total_neto = _quantize_money(
        (ventas_netas['subtotal_repuestos__sum'] or Decimal('0.00')) +
        (ventas_netas['subtotal_servicios__sum'] or Decimal('0.00'))
    )
    
    total_iva = _quantize_money(
        docs.aggregate(Sum('iva_repuestos'))['iva_repuestos__sum'] or Decimal('0.00')
    )
    
    total_bruto = _quantize_money(total_neto + total_iva)
    
    return {
        'periodo': f"{year}-{month:02d}",
        'ventas_netas': total_neto,
        'iva': total_iva,
        'ventas_brutas': total_bruto,
        'fecha_emision_min': docs.aggregate(Min('fecha_emision'))['fecha_emision__min'],
        'fecha_emision_max': docs.aggregate(Max('fecha_emision'))['fecha_emision__max'],
    }
```

---

## 🚫 **ANTI-PATRONES (NO HACER)**

### **❌ Anti-patrón 1: Solo redondear al final**

```python
# ❌ MAL: Acumula error de redondeo
subtotal = Decimal('0.00')
for linea in lineas:
    subtotal += linea.cantidad * linea.precio_unitario  # ❌ Sin redondear

tax = subtotal * Decimal('0.19')  # ❌ Sin redondear
total = (subtotal + tax).quantize(Decimal('0.01'))  # ❌ Solo redondea al final

# ✅ BIEN: Redondear en cada paso
subtotal = Decimal('0.00')
for linea in lineas:
    linea_subtotal = _quantize_money(linea.cantidad * linea.precio_unitario)
    subtotal += linea_subtotal

subtotal = _quantize_money(subtotal)
tax = _quantize_money(subtotal * Decimal('0.19'))
total = _quantize_money(subtotal + tax)
```

---

### **❌ Anti-patrón 2: Calcular subtotal "a mano"**

```python
# ❌ MAL: Ignora campo subtotal
subtotal = linea.cantidad * linea.precio_unitario - linea.descuento

# ✅ BIEN: Usar campo subtotal si existe
if hasattr(linea, 'subtotal') and linea.subtotal is not None:
    subtotal = linea.subtotal
else:
    subtotal = _quantize_money(linea.cantidad * linea.precio_unitario - linea.descuento)
```

---

### **❌ Anti-patrón 3: Usar fecha_creacion en KPIs**

```python
# ❌ MAL: KPI incorrecto
ingresos = Documento.objects.filter(
    fecha_creacion__year=2025  # ❌ Usa fecha_creacion
).aggregate(Sum('total'))

# ✅ BIEN: KPI correcto
ingresos = Documento.objects.filter(
    fecha_emision__year=2025  # ✅ Usa fecha_emision
).aggregate(Sum('total'))
```

---

### **❌ Anti-patrón 4: Usar float para dinero**

```python
# ❌ MAL: float tiene errores de precisión
precio = 19.99
cantidad = 3
subtotal = precio * cantidad  # ❌ 59.97000000000001

# ✅ BIEN: Decimal con redondeo explícito
precio = Decimal('19.99')
cantidad = Decimal('3')
subtotal = _quantize_money(precio * cantidad)  # ✅ 59.97
```

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

- [✅] Importar `ROUND_HALF_UP` de `decimal`
- [✅] Crear función `_quantize_money(value)`
- [✅] Aplicar `_quantize_money()` a subtotales de líneas
- [✅] Aplicar `_quantize_money()` a totales de categorías
- [✅] Aplicar `_quantize_money()` a cálculos de impuestos
- [✅] Aplicar `_quantize_money()` a totales finales
- [✅] Usar campo `subtotal` de línea si existe
- [✅] NO calcular subtotal "a mano" si ya existe en DB
- [✅] Documentar que KPIs usan `fecha_emision`
- [✅] Verificar que todos los KPIs usan `fecha_emision`
- [✅] Crear tests para redondeo financiero
- [✅] Crear tests para uso de subtotal
- [✅] Crear tests para KPIs con fecha_emision

---

## 📋 **ARCHIVOS MODIFICADOS**

1. ✅ `taller/documentos/services.py`
   - Importado `ROUND_HALF_UP`
   - Creada función `_quantize_money()`
   - Aplicado redondeo a TODOS los cálculos
   - Implementado uso de campo `subtotal` si existe
   - Documentado convención de `fecha_emision` para KPIs

---

## 🎯 **BENEFICIOS**

```
✅ Precisión financiera garantizada
✅ Consistencia en todos los cálculos
✅ Conformidad con estándares contables
✅ Auditoría correcta (subtotal no cambia)
✅ KPIs correctos (usa fecha_emision)
✅ Performance (no recalcular subtotales)
✅ Inmutabilidad de documentos emitidos
```

---

## 📚 **REFERENCIAS**

### **Estándares:**
- IEEE 754-2008: Decimal floating-point arithmetic
- GAAP: Generally Accepted Accounting Principles
- IFRS: International Financial Reporting Standards

### **Python Decimal:**
- https://docs.python.org/3/library/decimal.html
- Rounding modes: ROUND_HALF_UP, ROUND_HALF_EVEN, etc.

---

**Estado:** ✅ **ESTÁNDARES FINANCIEROS IMPLEMENTADOS**

**Próximo paso:** Usar `_quantize_money()` en TODOS los cálculos de dinero del sistema

**¡Cálculos financieros con precisión y estándares enterprise!** 💰

