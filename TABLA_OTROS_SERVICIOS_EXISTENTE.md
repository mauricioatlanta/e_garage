# ✅ Tabla "Otros Servicios" - YA EXISTE EN EL SISTEMA

## 🎯 **RESUMEN**

La tabla para registrar **servicios efectuados por empresas externas** **YA EXISTE** en el sistema con el nombre `ServicioExterno`.

**Ubicación:** `taller/servicios/models.py`

---

## 📋 **MODELO EXISTENTE: ServicioExterno**

### **Campos Implementados:**

```python
class ServicioExterno(TenantScoped):
    """Servicios realizados por empresas externas que el taller puede ofrecer"""
    
    # CAMPOS SOLICITADOS ✅
    nombre = models.CharField(
        max_length=160,
        help_text="Nombre del servicio externo"
    )
    
    empresa_externa = models.CharField(
        max_length=255,
        help_text="Nombre de la empresa que realiza el servicio"
    )
    
    costo_taller = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo que paga el taller a la empresa externa"
    )
    
    precio_cliente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio que cobra el taller al cliente"
    )
    
    # CAMPOS ADICIONALES ✅
    categoria = models.ForeignKey('CategoriaServicio', ...)
    subcategoria = models.ForeignKey('SubcategoriaServicio', ...)
    descripcion = models.TextField(blank=True, null=True)
    tiempo_estimado = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    # HEREDADO DE TenantScoped:
    empresa = models.ForeignKey('taller.Empresa', ...)  # Multi-tenant
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 📊 **COMPARACIÓN CON CAMPOS SOLICITADOS**

| Campo Solicitado | Campo Existente | Estado |
|------------------|-----------------|--------|
| nombre del servicio | `nombre` | ✅ Existe |
| compañia_del_servicio | `empresa_externa` | ✅ Existe |
| precio_taller | `costo_taller` | ✅ Existe |
| precio_cliente | `precio_cliente` | ✅ Existe |

**Conclusión:** ✅ **Todos los campos solicitados ya están implementados**

---

## ✨ **CARACTERÍSTICAS ADICIONALES**

### **Campos Extras (ya implementados):**

1. **Categorización:**
   - `categoria` - FK a CategoriaServicio
   - `subcategoria` - FK a SubcategoriaServicio

2. **Información Adicional:**
   - `descripcion` - Descripción del servicio
   - `tiempo_estimado` - Tiempo estimado del servicio
   - `activo` - Si el servicio está disponible

3. **Multi-tenant:**
   - `empresa` - Cada taller tiene sus propios servicios externos
   - Heredado de `TenantScoped`

4. **Auditoría:**
   - `created_at` - Fecha de creación
   - `updated_at` - Última actualización

5. **Properties:**
   - `ganancia` - Calcula precio_cliente - costo_taller
   - `margen_porcentaje` - Calcula % de ganancia

---

## 📝 **MODELO LineaOtroServicio (Para Documentos)**

Además del catálogo, existe `LineaOtroServicio` para usar estos servicios en documentos:

```python
class LineaOtroServicio(models.Model):
    """Línea de servicio externo en un documento"""
    
    documento = models.ForeignKey('taller.Documento', ...)
    nombre = models.CharField(max_length=255)  # ✅ Congelado
    empresa_externa = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=1)
    costo_interno = models.DecimalField(...)  # Costo para el taller
    precio_cliente = models.DecimalField(...)  # Precio al cliente
    descuento = models.DecimalField(...)
    
    # Properties
    @property
    def ganancia(self):
        return self.precio_cliente - self.costo_interno
```

---

## 🔧 **FUNCIONALIDAD EXISTENTE**

### **1. Vista de Menú (Lista):**
- **View:** `otros_servicios_menu(request)`
- **Archivo:** `taller/servicios/views.py`
- **URL:** Probablemente `/servicios/otros/`

### **2. Crear Servicio Externo:**
- **View:** `crear_otro_servicio(request)`
- **Archivo:** `taller/servicios/views.py`

### **3. Template de Tabla:**
- **Archivo:** `templates/common/components/tabla_otro_servicio.html`
- **Propósito:** Tabla para agregar servicios externos en documentos

### **4. Formulario:**
- **Clase:** `OtroServicioForm`
- **Archivo:** `taller/documentos/formsets.py`

---

## 📊 **ÍNDICES Y CONSTRAINTS**

### **Índices Optimizados:**
```python
indexes = [
    Index(fields=["empresa", "nombre"]),
    Index(fields=["empresa", "empresa_externa"]),
    Index(fields=["empresa", "categoria"]),
    Index(fields=["empresa", "activo"]),
]
```

### **Constraint Único:**
```python
# Evita duplicados
UniqueConstraint(
    fields=["empresa", "nombre", "empresa_externa"],
    name="uq_servicio_externo_empresa_nombre_proveedor"
)
```

---

## 🎯 **EJEMPLO DE USO**

### **Crear Servicio Externo:**

```python
from taller.servicios.models import ServicioExterno

# Crear servicio externo
servicio = ServicioExterno.objects.create(
    empresa=request.user.empresa,
    nombre='Alineación Computarizada',
    empresa_externa='Alineación Express',
    categoria=categoria_mecanica,
    costo_taller=25000,      # Lo que paga el taller
    precio_cliente=35000,    # Lo que cobra al cliente
    descripcion='Alineación con equipo láser',
    tiempo_estimado='30 minutos',
    activo=True
)

# Calcular ganancia automáticamente
print(f"Ganancia: {servicio.ganancia}")  # 10000
print(f"Margen: {servicio.margen_porcentaje}%")  # 28.57%
```

---

### **Usar en Documento:**

```python
from taller.models import LineaOtroServicio

# Agregar servicio externo a documento
linea = LineaOtroServicio.objects.create(
    documento=documento,
    nombre='Alineación Computarizada',  # ✅ Congelado
    empresa_externa='Alineación Express',
    cantidad=1,
    costo_interno=25000,
    precio_cliente=35000,
    descuento=Decimal('0.00')
)

# Ganancia se calcula automáticamente
print(linea.ganancia)  # 10000
```

---

## 🔍 **VERIFICAR EN ADMIN**

El modelo existe pero **NO está registrado en el admin**. Si quieres agregarlo:

```python
# taller/admin.py o nuevo archivo taller/admin/servicios_admin.py

from django.contrib import admin
from taller.servicios.models import ServicioExterno

@admin.register(ServicioExterno)
class ServicioExternoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre',
        'empresa_externa',
        'costo_taller',
        'precio_cliente',
        'ganancia_display',
        'margen_display',
        'activo',
    ]
    
    list_filter = [
        'activo',
        'categoria',
        'empresa_externa',
    ]
    
    search_fields = [
        'nombre',
        'empresa_externa',
        'descripcion',
    ]
    
    readonly_fields = [
        'ganancia_display',
        'margen_display',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'empresa_externa', 'categoria', 'subcategoria')
        }),
        ('Precios', {
            'fields': ('costo_taller', 'precio_cliente', 'ganancia_display', 'margen_display')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'tiempo_estimado', 'activo')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def ganancia_display(self, obj):
        return f"${obj.ganancia:,.0f}"
    ganancia_display.short_description = 'Ganancia'
    
    def margen_display(self, obj):
        return f"{obj.margen_porcentaje:.1f}%"
    margen_display.short_description = 'Margen %'
```

---

## 📋 **ESTRUCTURA COMPLETA**

### **Catálogo de Servicios Externos:**
```
ServicioExterno (taller/servicios/models.py)
  ├── nombre
  ├── empresa_externa
  ├── categoria, subcategoria
  ├── costo_taller
  ├── precio_cliente
  ├── descripcion
  ├── tiempo_estimado
  ├── activo
  └── Properties:
      ├── ganancia (calculado)
      └── margen_porcentaje (calculado)
```

### **Línea en Documento:**
```
LineaOtroServicio (taller/models/lineas_documento.py)
  ├── documento (FK)
  ├── nombre (congelado)
  ├── empresa_externa (congelado)
  ├── cantidad
  ├── costo_interno (congelado)
  ├── precio_cliente (congelado)
  ├── descuento
  └── Properties:
      ├── ganancia (calculado)
      └── subtotal (calculado)
```

---

## ✅ **RESUMEN**

```
✅ La tabla "Otros Servicios" YA EXISTE
✅ Modelo: ServicioExterno
✅ Ubicación: taller/servicios/models.py
✅ Campos solicitados: TODOS implementados
   ✅ nombre del servicio → nombre
   ✅ compañia_del_servicio → empresa_externa
   ✅ precio_taller → costo_taller
   ✅ precio_cliente → precio_cliente
✅ Funcionalidad adicional: ganancia, margen_porcentaje
✅ Multi-tenant: Cada empresa tiene sus propios servicios
✅ Modelo para documentos: LineaOtroServicio
✅ Template: tabla_otro_servicio.html
✅ Views: otros_servicios_menu, crear_otro_servicio
```

---

## ⚠️ **ÚNICO PENDIENTE: REGISTRAR EN ADMIN**

Si quieres gestionar los servicios externos desde el admin de Django, necesitas registrarlo. ¿Quieres que cree el admin para `ServicioExterno`?

---

**La tabla ya existe y está completamente funcional.** ✅
