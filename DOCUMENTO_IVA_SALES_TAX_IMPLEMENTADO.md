# DocumentoForm - Cálculo Automático de IVA/Sales Tax Implementado

## ✅ Implementación Completada

### 1. **Patch Drop-in para `taller/models/documento.py`**

#### Características Implementadas:
- ✅ **Cálculo automático** - `neto_repuestos`, `neto_servicios`, `neto_otros_servicios`
- ✅ **Regla Chile** - IVA 19% solo a repuestos (regla eGarage)
- ✅ **Regla USA** - Sales tax configurable (usa `tax_rate_applied` si viene; si no, 0% por defecto)
- ✅ **Redondeo por país** - CL: 0 decimales, US: 2 decimales
- ✅ **Recálculo automático** - En `clean()` y `save()`
- ✅ **Robusto** - Funciona aunque `LineaOtroServicio` no tenga subtotal
- ✅ **Extensible** - Conectable con `ConfiguracionEmpresa` para tasas

#### Métodos Implementados:

##### **Helpers Internos:**
```python
def _decimals(self):
    """Decimales por país/moneda: US -> 2, CL -> 0"""

def _q(self, value, decs=None):
    """Quantize con HALF_UP según decimales de la empresa"""

def _resolve_tax_rate(self):
    """Resuelve la tasa: si el campo ya viene seteado, la usa.
    Si CL y no viene, 19.0. Si US y no viene, 0.0 por defecto"""

def _sum_repuesto(self):
    """Calcula cantidad*precio_unitario - descuento línea"""

def _sum_servicio(self):
    """Calcula cantidad*precio_unitario - descuento línea"""

def _sum_otro_servicio(self):
    """Calcula cantidad * precio_cliente"""
```

##### **Método Principal:**
```python
def recompute_totals(self, persist=False):
    """
    Recalcula netos, impuesto y total conforme reglas:
    - CL: IVA 19% SOLO sobre repuestos
    - US: por defecto 0% (usa tax_rate_applied si viene)
    """
```

### 2. **Campos de Forma de Pago Agregados**

#### Nuevos Campos en el Modelo:
```python
metodo_pago = models.CharField(max_length=20, choices=[...])
ult4 = models.CharField(max_length=4, blank=True, null=True)
monto_pagado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
saldo_pendiente = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
fecha_pago = models.DateTimeField(blank=True, null=True)
nota_pago = models.TextField(blank=True, null=True)
```

#### Migración Creada:
- ✅ **Migración 0013** - `add_payment_fields_and_calculations`
- ✅ **Campos agregados** - `metodo_pago`, `ult4`, `monto_pagado`, `saldo_pendiente`, `fecha_pago`, `nota_pago`

### 3. **Señales Automáticas** (`taller/models/signals.py`)

#### Recálculo Automático:
```python
@receiver(post_save, sender="taller.LineaRepuesto")
@receiver(post_delete, sender="taller.LineaRepuesto")
def _recalc_repuesto(sender, instance, **kwargs):
    """Recalcula totales cuando se crea/edita/elimina una línea de repuesto"""

@receiver(post_save, sender="taller.LineaServicio")
@receiver(post_delete, sender="taller.LineaServicio")
def _recalc_servicio(sender, instance, **kwargs):
    """Recalcula totales cuando se crea/edita/elimina una línea de servicio"""

@receiver(post_save, sender="taller.LineaOtroServicio")
@receiver(post_delete, sender="taller.LineaOtroServicio")
def _recalc_otro(sender, instance, **kwargs):
    """Recalcula totales cuando se crea/edita/elimina una línea de otro servicio"""
```

#### Activación en `apps.py`:
```python
def ready(self):
    from . import signals  # noqa
```

### 4. **Reglas Fiscales Implementadas**

#### Chile (CL):
- ✅ **IVA 19%** - Aplica SOLO a repuestos
- ✅ **Servicios exentos** - No se gravan con IVA
- ✅ **Redondeo** - 0 decimales (enteros)
- ✅ **Base imponible** - Solo `neto_repuestos`

#### USA (US):
- ✅ **Sales Tax** - Configurable por estado
- ✅ **Tasa por defecto** - 0% si no se especifica
- ✅ **Redondeo** - 2 decimales
- ✅ **Base imponible** - Solo `neto_repuestos` (extensible)

#### Cálculo de Totales:
```python
# Chile
tax_base = rep  # IVA solo a repuestos
tax_amount = (tax_base * 19.0 / 100.0)
total = rep + srv + osrv - desc + tax_amount

# USA
tax_base = rep  # Sales tax solo a repuestos (por defecto)
tax_amount = (tax_base * tax_rate_applied / 100.0)
total = rep + srv + osrv - desc + tax_amount
```

### 5. **Integración con Templates PDF**

#### Bloque de Totales Actualizado:
- ✅ **Campos de pago** - Método, monto pagado, saldo pendiente
- ✅ **Formateo de moneda** - Con templatetag `eg_money`
- ✅ **Monto en palabras** - Español/Inglés automático
- ✅ **Localización** - Labels por país

#### Contexto de Moneda:
```python
"empresa_moneda": {
    "simbolo": "$",
    "codigo": "CLP",  # o "USD"
    "decimales": 0,   # o 2
}
```

### 6. **Métodos de Compatibilidad**

#### Retrocompatibilidad:
```python
def total_repuestos(self):
    """Compatibilidad: retorna neto_repuestos"""

def total_servicios(self):
    """Compatibilidad: retorna neto_servicios"""

def total_otros_servicios(self):
    """Compatibilidad: retorna neto_otros_servicios"""

def iva(self):
    """Compatibilidad: retorna tax_amount"""

def total_general(self):
    """Compatibilidad: retorna total"""

def recalcular_totales(self):
    """Compatibilidad: llama al nuevo método"""
```

### 7. **Prevención de Bucles Infinitos**

#### Método `save()` Optimizado:
```python
def save(self, *args, **kwargs):
    # ... lógica de guardado ...
    super().save(*args, **kwargs)

    # Solo recalcular si no estamos ya en una actualización de campos específicos
    if 'update_fields' not in kwargs:
        self.refresh_from_db()
        self.recompute_totals(persist=True)
```

#### Método `recompute_totals()`:
```python
def recompute_totals(self, persist=False):
    # ... cálculos ...
    if persist:
        self.save(update_fields=[
            "neto_repuestos", "neto_servicios", "neto_otros_servicios",
            "tax_rate_applied", "tax_amount", "total"
        ])
```

### 8. **Archivos Creados/Modificados**

#### Modelo Principal:
- ✅ `taller/models/documento.py` - Patch completo aplicado

#### Señales:
- ✅ `taller/models/signals.py` - Recálculo automático
- ✅ `taller/apps.py` - Activación de señales

#### Migración:
- ✅ `taller/migrations/0013_add_payment_fields_and_calculations.py`

#### Tests:
- ✅ `taller/tests/test_documento_calculos.py` - Tests completos
- ✅ `test_calculo_simple.py` - Test de verificación

#### Templates:
- ✅ `templates/taller/documentos/_pdf_totals_payment.html` - Bloque de totales
- ✅ `taller/templatetags/eg_money.py` - Templatetag de moneda

## 🚀 **Uso en Producción**

### 1. **Creación de Documento:**
```python
doc = Documento.objects.create(
    empresa=empresa,
    tipo="OT",
    cliente=cliente,
    vehiculo=vehiculo,
    tecnico_responsable=tecnico
)
# Los totales se calculan automáticamente
```

### 2. **Recálculo Manual:**
```python
doc.recompute_totals(persist=True)  # Recalcula y guarda
doc.recompute_totals(persist=False)  # Solo calcula en memoria
```

### 3. **Configuración de Tasa Personalizada:**
```python
doc.tax_rate_applied = Decimal("8.5")  # 8.5% sales tax
doc.recompute_totals(persist=True)
```

### 4. **Integración con ConfiguracionEmpresa (Futuro):**
```python
def _resolve_tax_rate(self):
    # Conectar con ConfiguracionEmpresa
    config = ConfiguracionEmpresa.objects.get(empresa=self.empresa)
    return config.tax_rate if config.tax_rate else self._default_tax_rate()
```

## 🎯 **Ventajas del Sistema**

### **Para Desarrolladores:**
- ✅ **Drop-in** - Solo aplicar el patch al modelo
- ✅ **Automático** - Recálculo en create/edit/delete de líneas
- ✅ **Robusto** - Funciona sin líneas, con líneas, con descuentos
- ✅ **Extensible** - Fácil conectar con configuración empresarial

### **Para Usuarios:**
- ✅ **Preciso** - Cálculos fiscales correctos por país
- ✅ **Automático** - No requiere intervención manual
- ✅ **Consistente** - Mismos resultados siempre
- ✅ **Completo** - Incluye forma de pago y totales

### **Para el Sistema:**
- ✅ **Multi-país** - Chile y USA con reglas específicas
- ✅ **Multi-tenant** - Filtrado por empresa
- ✅ **Auditable** - Trazabilidad de cálculos
- ✅ **Escalable** - Fácil agregar nuevos países

## 🔧 **Configuración Adicional**

### **Para Gravar Servicios en USA:**
```python
# En el modelo Documento, agregar:
apply_vat_to_services = models.BooleanField(default=False)

# En _resolve_tax_rate():
if pais == "US":
    tax_base = rep + (srv if self.apply_vat_to_services else Decimal("0"))
```

### **Para Conectar con ConfiguracionEmpresa:**
```python
def _resolve_tax_rate(self):
    try:
        config = ConfiguracionEmpresa.objects.get(empresa=self.empresa)
        return config.tax_rate
    except ConfiguracionEmpresa.DoesNotExist:
        # Fallback a valores por defecto
        pais = (self.empresa.pais or "CL").upper()
        return Decimal("19.0") if pais == "CL" else Decimal("0.0")
```

## 🚀 Estado: LISTO PARA PRODUCCIÓN

### Características Implementadas:
- ✅ Cálculo automático de IVA/Sales Tax
- ✅ Reglas fiscales CL/US correctas
- ✅ Recálculo automático con señales
- ✅ Campos de forma de pago completos
- ✅ Prevención de bucles infinitos
- ✅ Métodos de compatibilidad
- ✅ Integración con templates PDF
- ✅ Tests completos
- ✅ Migración aplicada

**El sistema de cálculo automático de IVA/Sales Tax está completamente implementado y listo para producción. Solo aplicar el patch al modelo Documento y activar las señales.**
