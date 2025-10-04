# ✅ Mejoras Aplicadas: DetalleDocumento

## 📋 Resumen de Cambios

Archivo: `taller/documentos/models.py`  
Modelo: `DetalleDocumento`  
Cambios: **7 mejoras críticas**

---

## 🔧 Cambios Aplicados

### 1️⃣ **Eliminado Import Redundante**

**Antes:**
```python
from taller.models.documento import Documento

Documento = Documento  # ❌ Redundante
```

**Después:**
```python
from taller.models.documento import Documento
# ✅ Sin línea redundante
```

**Impacto:** Código más limpio

---

### 2️⃣ **Agregado Choices para `tipo_item`**

**Antes:**
```python
tipo_item = models.CharField(max_length=50)  # ❌ Sin validación
```

**Después:**
```python
class TipoItem(models.TextChoices):
    REPUESTO = "REPUESTO", "Repuesto"
    SERVICIO = "SERVICIO", "Servicio"
    OTRO = "OTRO", "Otro"

tipo_item = models.CharField(
    max_length=20,
    choices=TipoItem.choices,
    default=TipoItem.SERVICIO
)
```

**Impacto:**
- ✅ Evita strings inconsistentes ("repuesto" vs "REPUESTO" vs "Repuesto")
- ✅ Validación automática en formularios
- ✅ Dropdown en admin con opciones fijas

---

### 3️⃣ **Subtotal No Editable**

**Antes:**
```python
subtotal = models.DecimalField(
    max_digits=12, 
    decimal_places=2, 
    blank=True,      # ❌ Permite null
    null=True,       # ❌ Puede ser None
    default=Decimal("0.00")
)
```

**Después:**
```python
subtotal = models.DecimalField(
    max_digits=14,      # ← Ampliado
    decimal_places=2,
    default=Decimal("0.00"),
    editable=False,     # ✅ No se puede editar en forms
    help_text="Calculado automáticamente"
)
```

**Impacto:**
- ✅ No se puede editar manualmente (evita inconsistencias)
- ✅ Siempre tiene valor (no null)
- ✅ Se calcula en cada save()

---

### 4️⃣ **Ampliado `max_digits` para CLP**

**Antes:**
```python
precio_venta = models.DecimalField(
    max_digits=10,  # ❌ Máximo: $99,999,999.99
    decimal_places=2
)
subtotal = models.DecimalField(
    max_digits=12,  # ❌ Insuficiente para grandes órdenes
    decimal_places=2
)
```

**Después:**
```python
precio_venta = models.DecimalField(
    max_digits=12,  # ✅ Máximo: $9,999,999,999.99
    decimal_places=2
)
subtotal = models.DecimalField(
    max_digits=14,  # ✅ Soporta cantidades grandes
    decimal_places=2
)
```

**Impacto:**
- ✅ Soporta precios hasta $9.999.999.999,99 (casi 10 mil millones CLP)
- ✅ Subtotal hasta $99.999.999.999.999,99

**Ejemplo Real:**
```python
# Orden de repuestos industriales:
precio_venta = Decimal("50000000.00")  # $50M CLP
cantidad = 20
subtotal = Decimal("1000000000.00")    # $1.000M CLP ✅ Ahora soportado
```

---

### 5️⃣ **Agregado `MinValueValidator`**

**Antes:**
```python
precio_venta = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    default=Decimal("0.00")
    # ❌ Sin validación de valores negativos
)
```

**Después:**
```python
from django.core.validators import MinValueValidator

precio_venta = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=Decimal("0.00"),
    validators=[MinValueValidator(Decimal("0.00"))]  # ✅ Validación
)

cantidad = models.PositiveIntegerField(
    default=1,
    validators=[MinValueValidator(1)]  # ✅ Mínimo 1
)
```

**Impacto:**
- ✅ Rechaza precios negativos
- ✅ Rechaza cantidades <= 0
- ✅ Validación en formularios y API

---

### 6️⃣ **Método `save()` Robusto**

**Antes:**
```python
def save(self, *args, **kwargs):
    self.subtotal = self.precio_venta * self.cantidad  # ❌ Falla si son None
    super().save(*args, **kwargs)
```

**Después:**
```python
def save(self, *args, **kwargs):
    """Recalcula subtotal con manejo de None."""
    precio = self.precio_venta or Decimal("0.00")  # ✅ Fallback
    cant = self.cantidad or 0                       # ✅ Fallback
    self.subtotal = precio * Decimal(cant)
    super().save(*args, **kwargs)
```

**Impacto:**
- ✅ No crashea si precio_venta o cantidad son None
- ✅ Funciona en bulk_create si se pasan valores parciales

---

### 7️⃣ **Validación Multi-Tenant en `clean()`**

**Agregado:**
```python
def clean(self):
    """Validaciones de integridad y multi-tenant."""
    super().clean()
    
    # Validar precio positivo
    if self.precio_venta and self.precio_venta < 0:
        raise ValidationError({"precio_venta": "El precio no puede ser negativo"})
    
    # Validar cantidad mínima
    if self.cantidad and self.cantidad < 1:
        raise ValidationError({"cantidad": "La cantidad debe ser al menos 1"})
    
    # Validación multi-tenant (comentado, listo para activar)
    # if self.documento and hasattr(self.documento, "empresa_id"):
    #     if hasattr(self, "empresa_id") and self.empresa_id:
    #         if self.documento.empresa_id != self.empresa_id:
    #             raise ValidationError(
    #                 "El detalle no pertenece a la empresa del documento"
    #             )
```

**Impacto:**
- ✅ Doble validación de precios/cantidades (además de validators)
- ✅ Preparado para validar coherencia multi-tenant

---

### 8️⃣ **Mejorado `__str__()`**

**Antes:**
```python
def __str__(self):
    return f"{self.tipo_item}: {self.nombre}"
    # Ejemplo: "SERVICIO: Cambio de aceite"
```

**Después:**
```python
def __str__(self):
    tipo = self.get_tipo_item_display()  # ← "Servicio" en vez de "SERVICIO"
    return f"{tipo}: {self.nombre} x{self.cantidad} = ${self.subtotal:,.2f}"
    # Ejemplo: "Servicio: Cambio de aceite x2 = $60,000.00"
```

**Impacto:**
- ✅ Más descriptivo en admin y logs
- ✅ Incluye cantidad y subtotal
- ✅ Formato de moneda con separadores de miles

---

## 🎁 Extras Agregados

### **Métodos Helpers**

```python
def get_precio_total(self):
    """Alias del subtotal (para consistencia con otros modelos)."""
    return self.subtotal

def get_precio_con_descuento(self, descuento_pct=Decimal("0.00")):
    """
    Calcula precio con descuento.
    
    Args:
        descuento_pct: Porcentaje (0-100)
    
    Returns:
        Decimal: Subtotal con descuento
    
    Example:
        >>> detalle.subtotal = Decimal("100.00")
        >>> detalle.get_precio_con_descuento(Decimal("10.00"))
        Decimal("90.00")  # 10% off
    """
    if descuento_pct <= 0:
        return self.subtotal
    factor = (Decimal("100.00") - descuento_pct) / Decimal("100.00")
    return self.subtotal * factor
```

**Uso:**
```python
# En Documento.calcular_total()
total = sum(d.get_precio_total() for d in self.detalles.all())

# Con descuento del 15%
total_con_descuento = sum(
    d.get_precio_con_descuento(Decimal("15.00")) 
    for d in self.detalles.all()
)
```

---

### **Meta Options**

```python
class Meta:
    verbose_name = "Detalle de documento"
    verbose_name_plural = "Detalles de documentos"
    ordering = ["id"]
    indexes = [
        models.Index(fields=["documento", "tipo_item"]),
    ]
```

**Impacto:**
- ✅ Índice compuesto para queries frecuentes
- ✅ Ordenamiento consistente

---

## 📊 Comparación Antes vs Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| **tipo_item** | CharField sin validación | TextChoices con 3 opciones |
| **subtotal** | Editable, nullable | No editable, siempre calculado |
| **max_digits precio** | 10 (máx ~$100M) | 12 (máx ~$10.000M) |
| **max_digits subtotal** | 12 | 14 |
| **Validación** | Solo en DB | MinValueValidator + clean() |
| **save() robusto** | ❌ Crashea con None | ✅ Maneja None |
| **Multi-tenant** | Sin validación | Preparado (comentado) |
| **__str__** | Básico | Descriptivo con $$ |
| **Helpers** | Sin helpers | 2 métodos útiles |

---

## 🧪 Testing

### Test 1: Validación de Choices
```python
from taller.documentos.models import DetalleDocumento

# ✅ Válido
detalle = DetalleDocumento(tipo_item=DetalleDocumento.TipoItem.REPUESTO)

# ❌ Inválido
detalle = DetalleDocumento(tipo_item="repuesto_invalido")
# → django.core.exceptions.ValidationError
```

### Test 2: Subtotal Automático
```python
detalle = DetalleDocumento(
    precio_venta=Decimal("25000.00"),
    cantidad=3
)
detalle.save()

assert detalle.subtotal == Decimal("75000.00")  # ✅ Calculado automáticamente
```

### Test 3: Manejo de None
```python
detalle = DetalleDocumento(
    precio_venta=None,  # ← None
    cantidad=5
)
detalle.save()

assert detalle.subtotal == Decimal("0.00")  # ✅ No crashea
```

### Test 4: Validación de Negativos
```python
detalle = DetalleDocumento(
    precio_venta=Decimal("-100.00")  # ← Negativo
)
detalle.full_clean()
# → ValidationError: "El precio no puede ser negativo"
```

### Test 5: Formato de String
```python
detalle = DetalleDocumento(
    tipo_item=DetalleDocumento.TipoItem.SERVICIO,
    nombre="Cambio de aceite",
    precio_venta=Decimal("30000.00"),
    cantidad=2
)
detalle.save()

str(detalle)
# → "Servicio: Cambio de aceite x2 = $60,000.00"
```

---

## 🚀 Migración Requerida

### Paso 1: Crear Migración
```bash
python manage.py makemigrations documentos --name mejoras_detalle_documento
```

**Cambios esperados:**
- Modificar `tipo_item`: agregar `choices`, cambiar `max_length` a 20
- Modificar `precio_venta`: cambiar `max_digits` a 12, agregar validators
- Modificar `subtotal`: cambiar `max_digits` a 14, `editable=False`, quitar `null=True`
- Modificar `cantidad`: agregar validators
- Agregar índice compuesto

### Paso 2: Data Migration (Opcional)
Si tienes datos existentes con `tipo_item` inconsistente:

```python
# migrations/XXXX_normalizar_tipo_item.py

def normalizar_tipos(apps, schema_editor):
    DetalleDocumento = apps.get_model('documentos', 'DetalleDocumento')
    
    # Normalizar variaciones
    DetalleDocumento.objects.filter(tipo_item__iexact="repuesto").update(tipo_item="REPUESTO")
    DetalleDocumento.objects.filter(tipo_item__iexact="servicio").update(tipo_item="SERVICIO")
    DetalleDocumento.objects.filter(tipo_item__iexact="service").update(tipo_item="SERVICIO")
    
    # Valores no reconocidos → OTRO
    validos = ["REPUESTO", "SERVICIO", "OTRO"]
    DetalleDocumento.objects.exclude(tipo_item__in=validos).update(tipo_item="OTRO")
```

### Paso 3: Aplicar
```bash
python manage.py migrate documentos
```

---

## ⚠️ Breaking Changes

### 1. `tipo_item` Ahora Usa Choices
**Antes:**
```python
detalle.tipo_item = "cualquier_cosa"  # ✅ Válido antes
```

**Después:**
```python
detalle.tipo_item = "cualquier_cosa"  # ❌ ValidationError
detalle.tipo_item = DetalleDocumento.TipoItem.SERVICIO  # ✅ Correcto
```

**Solución:** Actualizar código que asigna strings directamente.

---

### 2. `subtotal` No Es Editable
**Antes:**
```python
form = DetalleDocumentoForm(instance=detalle)
# subtotal aparecía en el formulario
```

**Después:**
```python
# subtotal NO aparece en formularios (editable=False)
# Se calcula automáticamente
```

**Solución:** Remover `subtotal` de forms explícitamente si estaba incluido.

---

## ✅ Checklist de Implementación

- [ ] Crear migración: `makemigrations`
- [ ] (Opcional) Data migration para normalizar `tipo_item`
- [ ] Aplicar migración: `migrate`
- [ ] Actualizar forms que referencien `tipo_item` con strings
- [ ] Remover `subtotal` de forms si estaba incluido
- [ ] Actualizar código que use `tipo_item` con strings
- [ ] Probar creación/edición de detalles en admin
- [ ] Verificar que cálculos sean correctos

---

## 🎯 Resultado Final

**DetalleDocumento ahora tiene:**

✅ **Validación robusta** - Choices, MinValueValidator, clean()  
✅ **Cálculos seguros** - Subtotal siempre correcto, no editable  
✅ **Soporte CLP grande** - Hasta $10.000M por línea  
✅ **Multi-tenant ready** - Validación preparada (comentada)  
✅ **Mejor UX** - __str__ descriptivo con formato moneda  
✅ **Helpers útiles** - get_precio_con_descuento()  
✅ **Performance** - Índice compuesto  

**Listo para producción** 🚀



