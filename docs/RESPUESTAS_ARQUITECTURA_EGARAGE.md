# 🏗️ Respuestas de Arquitectura - eGarage Django

## Análisis de las 3 Preguntas Esenciales sobre la Arquitectura

---

## 📂 1. ESTRUCTURA DE APLICACIONES Y LÓGICA DE NEGOCIO (Django)

### Resumen de Arquitectura

El proyecto **eGarage** utiliza una estructura de aplicaciones Django bien organizada, aunque con cierta complejidad debido a evolución histórica. La lógica está distribuida en módulos especializados.

---

### Tabla de Aplicaciones Principales

| App/Módulo de Django | Propósito Principal | Modelos Clave | Ubicación |
|---------------------|---------------------|---------------|-----------|
| **`core`** | Funcionalidades base compartidas | `TenantScoped` (mixins), configuración global | `core/models.py` |
| **`taller.models`** | **Modelos centrales del sistema** | Ver detalle abajo | `taller/models/*.py` |
| **`taller.models.empresa`** | **Configuración de Tenant/Multi-tenant** | `Empresa` (Tenant principal) | `taller/models/empresa.py` |
| **`taller.models.configuracion`** | Configuración por empresa | `ConfiguracionEmpresa` (moneda, impuestos) | `taller/models/configuracion.py` |
| **`taller.models.mixins`** | Mixins compartidos | `AuditMixin` (created_at, updated_at, created_by, updated_by) | `taller/models/mixins.py` |
| **`taller.documentos`** | **Gestión de documentos** (Presupuesto, OrdenTrabajo, Factura) | `Documento`, `LineaRepuesto`, `LineaServicio`, `LineaOtroServicio` | `taller/documentos/models.py` <br> `taller/models/documento.py` |
| **`taller.models.repuesto`** | Inventario de repuestos | `Repuesto` (stock, precio_compra, precio_venta) | `taller/models/repuesto.py` |
| **`taller.models.catalogo_servicios`** | Catálogo de servicios | `Service`, `ServicePrice`, `ServiceI18N` | `taller/models/catalogo_servicios.py` |
| **`taller.clientes`** | Gestión de clientes | `Cliente` | `taller/models/clientes.py` |
| **`taller.models.vehiculos`** | Gestión de vehículos | `Vehiculo`, `Marca`, `Modelo` | `taller/models/vehiculos.py` |
| **`taller.reportes`** | Reportes y estadísticas | No tiene modelos propios, usa otros | `taller/reportes/views.py` |
| **`taller.analytics`** | Analytics e IA | No tiene modelos, motor de IA | `taller/analytics/ai_reports.py` |
| **`taller.models.tecnico`** | Gestión de técnicos/mecánicos | `Tecnico` | `taller/models/tecnico.py` |
| **`taller.impuestos`** | Lógica de impuestos | Motor de cálculo (no modelos) | `taller/impuestos/engine.py` |

---

### ✅ Respuesta a la Pregunta 1:

#### **¿Cómo has distribuido la lógica de negocio en tus principales Apps de Django?**

**Distribución encontrada:**

1. **`core` o `common` - Contiene:**
   - ✅ **`TenantScoped`** (abstract model con `empresa` ForeignKey para multi-tenancy)
   - ✅ Mixins base para tenant-scoping
   - ❌ **NO contiene** `AuditMixin` (está en `taller.models.mixins`)
   - ❌ **NO contiene** modelo `Empresa` (está en `taller.models.empresa`)

2. **`taller.models.empresa` - Contiene:**
   - ✅ **`Empresa`** (Modelo principal del Tenant)
     - Campos: `pais`, `moneda`, `zona_horaria`, `plan`, `suscripcion_activa`
     - **Relación OneToOne con User**: `user = models.OneToOneField(User)`
   - ✅ **`ConfiguracionEmpresa`** (OneToOne con Empresa)
     - Campos: `tasa_impuesto`, `moneda`, `aplicar_impuesto_por_defecto`
     - Ubicación: `taller/models/configuracion.py`

3. **`taller.documentos` / `taller.models.documento` - Contiene:**
   - ✅ **`Documento`** (hereda de `AuditMixin`)
     - Tipos: `PRES` (Presupuesto), `OT` (OrdenTrabajo), `FAC` (Factura)
     - Campos de cálculo: `neto_repuestos`, `neto_servicios`, `tax_rate_applied`, `tax_amount`, `total`
   - ✅ **`LineaRepuesto`**, **`LineaServicio`**, **`LineaOtroServicio`**
   - ✅ **Lógica de cálculo de impuestos**: Método `recalcular_totales()` en el modelo
     - Ubicación: `taller/models/documento.py` líneas 509-580

4. **Inventario - Distribuido en:**
   - ✅ **`taller.models.repuesto`**: `Repuesto` (precio_compra, precio_venta, stock)
   - ✅ **`taller.models.catalogo_repuestos`**: `Part`, `PartPrice` (catálogo internacional)
   - ✅ **`taller.models.catalogo_servicios`**: `Service`, `ServicePrice`
   - ⚠️ **Lógica de stock**: Mezclada entre señales (`signals_inventory.py`) y métodos de modelo

5. **Otras Apps Clave:**
   - **`taller.clientes`**: `Cliente` (con filtrado por empresa)
   - **`taller.models.vehiculos`**: `Vehiculo`, `Marca`, `Modelo` (con soporte multi-país)
   - **`taller.reportes`**: Views de reportes (sin modelos propios)
   - **`taller.analytics`**: Motor de IA para reportes predictivos

---

## 🌍 2. IMPLEMENTACIÓN MULTI-PAÍS Y LOCALIZACIÓN (i18n)

### ✅ Respuesta a la Pregunta 2:

#### **¿Cómo aseguras que el usuario vea la moneda, el impuesto y el nombre de los documentos correctos para su país?**

### **2.1. Configuración del Tenant**

**SÍ, el modelo `Empresa` tiene configuración de país:**

```python
# taller/models/empresa.py
class Empresa(models.Model):
    pais = models.CharField(
        max_length=2,
        choices=PAIS_CHOICES,  # CL, US, MX
        default="CL",
        help_text="Define catálogos, moneda y regionalización"
    )
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default="CLP")
    zona_horaria = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default="America/New_York")
```

**Configuración adicional en `ConfiguracionEmpresa`:**
```python
# taller/models/configuracion.py
class ConfiguracionEmpresa(models.Model):
    empresa = models.OneToOneField("taller.Empresa", related_name="config")
    moneda = models.CharField(max_length=10, default="CLP")
    tasa_impuesto = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=Decimal("19.00"),  # 19% por defecto
        verbose_name="Tasa de Impuesto",
        help_text="IVA/Sales tax %"
    )
    aplicar_impuesto_por_defecto = models.BooleanField(default=False)
```

---

### **2.2. Sistema Centralizado de Configuración por País**

✅ **SÍ existe un sistema centralizado** en `taller/utils/country_config.py`:

```python
COUNTRY_SETTINGS = {
    "CL": {
        "currency": "CLP",
        "currency_symbol": "$",
        "decimals": 0,  # Sin decimales
        "tax_name": "IVA",
        "tax_rate": 19.0,  # 19%
        "lang": "es",
        "date_format": "DD/MM/YYYY",
    },
    "US": {
        "currency": "USD",
        "currency_symbol": "$",
        "decimals": 2,  # Con decimales
        "tax_name": "Sales Tax",
        "tax_rate": 0.0,  # Varía por estado
        "lang": "en",
        "date_format": "MM/DD/YYYY",
    },
    # ... México, Perú, Colombia, Ecuador, Brasil, Venezuela
}
```

**Función helper:**
```python
def get_configuracion_pais(empresa):
    """Retorna configuración específica según el país de la empresa"""
    from taller.utils.country_config import get_config_from_empresa
    config = get_config_from_empresa(empresa)
    return {
        "moneda": config["currency"],
        "simbolo_moneda": config["currency_symbol"],
        "decimales": config["decimals"],
        "impuesto_default": config["tax_rate"] / 100.0,  # Convierte a decimal
        # ...
    }
```

---

### **2.3. Manejo de Impuestos**

#### **¿Tienes una única función de Python que recibe la tasa del Tenant?**

**Respuesta: HÍBRIDO - Mezcla de enfoques:**

✅ **Función centralizada para obtener tasa:**
```python
# taller/documentos/api.py
def _tax_rate_for_empresa(emp) -> Decimal:
    """
    Lee tasa desde CompanySettings si existe.
    >1 como porcentaje (19 => 0.19); <=1 como fracción (0.19).
    Fallback: CL=0.19, otro país=0.00.
    """
    cs = _get_company_settings(emp)
    if cs:
        for name in ("iva", "iva_porcentaje", "sales_tax", "tax_rate", "tasa_iva"):
            if hasattr(cs, name):
                val = Decimal(str(getattr(cs, name)))
                return (val / Decimal("100")) if val > 1 else val
    return Decimal("0.19") if (getattr(emp, "pais", "") or "").upper() == "CL" else Decimal("0.00")
```

❌ **Pero el cálculo de impuestos está disperso:**

1. **En el modelo `Documento.recalcular_totales()`:**
```python
# taller/models/documento.py (líneas 509-580)
def recalcular_totales(self, save=True):
    """Recalcula sumas usando ORM"""
    pais = getattr(self.empresa, "pais", "CL")
    
    # Expresiones Django ORM para calcular subtotales
    rep_expr = ExpressionWrapper(
        (F("cantidad") * F("precio_unitario")) - Coalesce(F("descuento"), Value(0)),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    
    # Cálculo de impuestos con lógica if/else
    if pais == "US":
        tax_rate = Decimal("0.00")
    elif pais == "CL":
        tax_rate = Decimal("0.19")
    else:
        # Obtener de ConfiguracionEmpresa
        config = ConfiguracionEmpresa.objects.filter(empresa=self.empresa).first()
        tax_rate = (config.tasa_impuesto / 100) if config else Decimal("0.00")
```

2. **En las vistas de creación:**
```python
# taller/documentos/views_moderno.py (líneas 500-590)
# Hay lógica de cálculo de impuestos mezclada con la creación del documento
tax_rate_applied = Decimal("0.00")
if empresa.pais == "CL":
    tax_rate_applied = Decimal("19.00")
elif empresa.pais == "US":
    tax_rate_applied = Decimal("0.00")
```

3. **Resolución de tasa en el modelo:**
```python
# taller/models/documento.py (líneas 211-230)
def _resolve_tax_rate(self):
    """Resuelve la tasa: si el campo ya viene seteado, la usa.
    Si no, obtiene la tasa de ConfiguracionEmpresa o usa valores por defecto."""
    if getattr(self, "tax_rate_applied", None) not in (None, ""):
        return Decimal(str(self.tax_rate_applied))
    
    # Intentar obtener tasa de ConfiguracionEmpresa
    try:
        config = ConfiguracionEmpresa.objects.filter(empresa=self.empresa).first()
        if config and hasattr(config, "tasa_iva") and config.tasa_iva is not None:
            return Decimal(str(config.tasa_iva))
    except Exception:
        pass
```

---

### **2.4. Conclusión sobre Impuestos**

⚠️ **No existe una única función `calcular_impuesto(base, tasa)` centralizada.**

**Hay múltiples lugares donde se calcula:**
- ❌ Lógica `if/else` dispersa en vistas (`views_moderno.py`)
- ❌ Lógica `if/else` en métodos del modelo (`recalcular_totales()`)
- ✅ Función helper `_tax_rate_for_empresa()` pero no se usa consistentemente
- ✅ Sistema de configuración centralizado (`country_config.py`) pero no siempre se utiliza

**Recomendación:** Unificar en una única función:
```python
def calcular_impuesto(base: Decimal, empresa: Empresa) -> Decimal:
    """Calcula impuesto sobre base según configuración del tenant"""
    tasa = _tax_rate_for_empresa(empresa)
    return base * tasa
```

---

## 💾 3. INTERACCIÓN CON LA BASE DE DATOS (Reportes y Escalabilidad)

### ✅ Respuesta a la Pregunta 3:

#### **Para el módulo de Reportes, ¿están utilizando técnicas de optimización de Django?**

### **3.1. Uso de F Expressions y Annotate**

#### **¿Para calcular ganancia por repuesto (Precio Venta - Precio Compra), están usando F Expressions o Annotate para que el cálculo se haga directamente en la Base de Datos?**

**Respuesta: PARCIALMENTE - Mezcla de enfoques**

---

### ✅ **Ejemplos de Optimización con F Expressions:**

#### **1. Cálculo de Ingresos Totales en Reportes:**
```python
# taller/views_extra/business_intelligence.py (líneas 88-107)
def get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin):
    """Calcula la utilidad neta por repuesto"""
    repuestos_vendidos = (
        RepuestoDocumento.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__range=[fecha_inicio, fecha_fin],
            repuesto__isnull=False,
        )
        .select_related("repuesto")  # ✅ Optimización: JOIN en Python
        .values(
            "repuesto__nombre",
            "repuesto__precio_venta",
            "repuesto__precio_compra",
        )
        .annotate(
            cantidad_vendida=Sum("cantidad"),  # ✅ Agregación en DB
            ingresos_totales=Sum(F("cantidad") * F("precio_unitario")),  # ✅ F Expression en DB
        )
    )
    
    # ❌ PROBLEMA: El cálculo de utilidad se hace EN PYTHON (no en DB)
    utilidades = []
    for repuesto in repuestos_vendidos:
        precio_compra = repuesto["repuesto__precio_compra"]
        cantidad = repuesto["cantidad_vendida"]
        ingresos = repuesto["ingresos_totales"]
        
        costo_total = precio_compra * cantidad  # ❌ En Python
        utilidad_bruta = ingresos - costo_total  # ❌ En Python
```

**❌ Problema identificado:** Aunque se usa `F()` para ingresos, **la utilidad se calcula en Python**, no en la base de datos.

---

#### **2. Cálculo de Márgenes con ExpressionWrapper:**
```python
# taller/reportes/reportes_avanzados.py (líneas 323-333)
proveedor_margenes = (
    LineaOtroServicio.objects.filter(documento__tipo="FAC")
    .values("empresa_externa")
    .annotate(
        margen_promedio=Avg(
            ExpressionWrapper(
                (F("precio_cliente") - F("costo_interno")) * 100.0 / F("precio_cliente"),
                output_field=FloatField(),  # ✅ Tipo explícito
            )
        )
    )
)
```

**✅ Este ejemplo SÍ calcula en la base de datos** usando `ExpressionWrapper` y `F()`.

---

#### **3. Cálculo de Subtotales en Documentos:**
```python
# taller/models/documento.py (líneas 519-530)
def recalcular_totales(self, save=True):
    """Recalcula sumas usando ORM"""
    
    # ✅ Expresiones Django para cálculo en DB
    rep_expr = ExpressionWrapper(
        (F("cantidad") * F("precio_unitario")) - Coalesce(F("descuento"), Value(0)),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    
    # ✅ Agregación en DB
    rep_subtotal = self.lineas_repuesto.aggregate(
        total=Sum(rep_expr)
    )["total"] or Decimal("0.00")
```

**✅ Este ejemplo también usa F Expressions correctamente.**

---

#### **4. Reporte de Repuestos Más Vendidos:**
```python
# taller/reportes/views.py (líneas 135-148)
repuesto_ventas = (
    LineaRepuesto.objects.filter(
        documento__tipo="FAC",
        documento__empresa=empresa,
    )
    .values("codigo", "nombre")
    .annotate(
        cantidad_total=Sum("cantidad"),  # ✅ En DB
        ingresos=Sum(
            ExpressionWrapper(
                F("cantidad") * F("precio_unitario"),
                output_field=FloatField(),
            )
        )  # ✅ En DB
    )
)
```

**✅ Usa F Expressions correctamente.**

---

### **3.2. Análisis de Optimización de Rentabilidad**

#### **Cálculo de Rentabilidad por Repuesto - Estado Actual:**

**Código encontrado:**
```python
# taller/views_extra/business_intelligence.py (líneas 88-134)
def get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin):
    repuestos_vendidos = (
        RepuestoDocumento.objects.filter(...)
        .annotate(
            cantidad_vendida=Sum("cantidad"),
            ingresos_totales=Sum(F("cantidad") * F("precio_unitario")),  # ✅ DB
        )
    )
    
    # ❌ PROBLEMA: Cálculo de utilidad en Python
    for repuesto in repuestos_vendidos:
        precio_compra = repuesto["repuesto__precio_compra"]  # Desde DB
        cantidad = repuesto["cantidad_vendida"]  # Desde DB
        ingresos = repuesto["ingresos_totales"]  # Desde DB
        
        costo_total = precio_compra * cantidad  # ❌ En Python
        utilidad_bruta = ingresos - costo_total  # ❌ En Python
        margen_utilidad = (utilidad_bruta / ingresos * 100) if ingresos > 0 else 0  # ❌ En Python
```

---

### **3.3. Recomendación: Optimización Completa**

**Versión optimizada (todo en DB):**
```python
def get_repuestos_utilidad_optimizado(empresa, fecha_inicio, fecha_fin):
    """Versión optimizada - TODO el cálculo en la base de datos"""
    from django.db.models import FloatField, Sum, F, ExpressionWrapper
    
    repuestos_vendidos = (
        RepuestoDocumento.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__range=[fecha_inicio, fecha_fin],
            repuesto__isnull=False,
        )
        .select_related("repuesto")
        .values(
            "repuesto__nombre",
            "repuesto__part_number",
            "repuesto__precio_venta",
            "repuesto__precio_compra",
        )
        .annotate(
            cantidad_vendida=Sum("cantidad"),
            ingresos_totales=Sum(F("cantidad") * F("precio_unitario")),
            
            # ✅ NUEVO: Calcular costo total en DB
            costo_total=Sum(
                ExpressionWrapper(
                    F("cantidad") * F("repuesto__precio_compra"),
                    output_field=FloatField()
                )
            ),
            
            # ✅ NUEVO: Calcular utilidad bruta en DB
            utilidad_bruta=ExpressionWrapper(
                Sum(F("cantidad") * F("precio_unitario")) - 
                Sum(F("cantidad") * F("repuesto__precio_compra")),
                output_field=FloatField()
            ),
            
            # ✅ NUEVO: Calcular margen en DB
            margen_utilidad=ExpressionWrapper(
                (
                    (Sum(F("cantidad") * F("precio_unitario")) - 
                     Sum(F("cantidad") * F("repuesto__precio_compra"))) * 100.0
                ) / Sum(F("cantidad") * F("precio_unitario")),
                output_field=FloatField()
            ),
        )
    )
    
    # Ahora solo necesitas convertir a lista (sin cálculos en Python)
    return list(repuestos_vendidos)
```

---

### **3.4. Otras Optimizaciones Encontradas**

✅ **Uso de `select_related()` y `prefetch_related()`:**
```python
.select_related("repuesto")  # JOIN en DB para evitar N+1 queries
```

✅ **Filtrado por empresa (multi-tenancy):**
```python
.filter(documento__empresa=empresa)  # Siempre filtrado por tenant
```

✅ **Índices en modelos:**
```python
# taller/models/documento.py
class Documento(AuditMixin, models.Model):
    tipo = models.CharField(max_length=4, db_index=True)  # ✅ Índice
    numero = models.CharField(max_length=32, db_index=True)  # ✅ Índice
    fecha_emision = models.DateField(default=timezone.now, db_index=True)  # ✅ Índice
```

---

### **3.5. Conclusión sobre Optimización**

| Aspecto | Estado | Nota |
|---------|--------|------|
| **Uso de F Expressions** | ✅ Parcialmente | Se usa en algunos lugares, no consistentemente |
| **Cálculo de rentabilidad en DB** | ❌ Parcialmente | Ingresos en DB ✅, pero utilidad en Python ❌ |
| **Agregaciones con Annotate** | ✅ Sí | `Sum()`, `Avg()` bien utilizados |
| **ExpressionWrapper** | ✅ Sí | Se usa en algunos reportes avanzados |
| **select_related/prefetch_related** | ✅ Sí | Se usa para evitar N+1 |
| **Filtrado por tenant** | ✅ Consistente | Siempre se filtra por `empresa` |

**Recomendación:** Migrar cálculos de utilidad/rentabilidad a usar `F()` y `ExpressionWrapper` para ejecutar todo en la base de datos.

---

## 📊 RESUMEN EJECUTIVO

### ✅ Fortalezas Identificadas:
1. ✅ Arquitectura multi-tenant clara con modelo `Empresa`
2. ✅ Sistema centralizado de configuración por país (`country_config.py`)
3. ✅ Uso parcial de F Expressions para optimización
4. ✅ Separación de responsabilidades por módulos
5. ✅ Mixins reutilizables (`AuditMixin`, `TenantScoped`)

### ⚠️ Áreas de Mejora:
1. ⚠️ Lógica de impuestos dispersa (múltiples if/else en diferentes lugares)
2. ⚠️ Cálculo de rentabilidad parcialmente en Python (debería estar en DB)
3. ⚠️ Falta función centralizada `calcular_impuesto(base, empresa)`
4. ⚠️ Algunos reportes no optimizados completamente

---

## 🔗 Referencias de Código

- **Modelo Empresa**: `taller/models/empresa.py:17-276`
- **Configuración País**: `taller/utils/country_config.py`
- **Cálculo Impuestos**: `taller/documentos/api.py:127-143`
- **Documento recalcular_totales**: `taller/models/documento.py:509-580`
- **Reporte Rentabilidad**: `taller/views_extra/business_intelligence.py:88-134`
- **AuditMixin**: `taller/models/mixins.py:5-24`

---

*Documento generado el: $(date)*
*Versión del sistema: eGarage Django*








