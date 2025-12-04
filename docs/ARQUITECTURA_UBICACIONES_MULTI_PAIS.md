# 🌎 ARQUITECTURA DE UBICACIONES MULTI-PAÍS

> **Versión:** 2.0  
> **Fecha:** Diciembre 2024  
> **Estado:** ✅ En producción

---

## 📋 **ÍNDICE**

1. [Visión General](#visión-general)
2. [Modelos de Datos](#modelos-de-datos)
3. [Países Soportados](#países-soportados)
4. [Migración desde Legacy](#migración-desde-legacy)
5. [Carga de Datos](#carga-de-datos)
6. [Uso en Formularios](#uso-en-formularios)
7. [Agregar Ubicaciones On-the-fly](#agregar-ubicaciones-on-the-fly)
8. [API y Queries](#api-y-queries)

---

## 1️⃣ **VISIÓN GENERAL**

### Objetivo
Tener un **sistema unificado** de ubicaciones geográficas que:
- ✅ Soporte **8 países** (CL, US, BR, MX, PE, VE, CO, EC)
- ✅ Use estándares **ISO 3166-1 alpha-2** para países
- ✅ Permita carga masiva de ubicaciones por país
- ✅ Permita agregar ubicaciones nuevas desde formularios
- ✅ **NO rompa compatibilidad** con datos legacy existentes

### Arquitectura en 3 capas

```
┌─────────────────────────────────────────┐
│  Capa 1: PAÍS (ISO 3166-1 alpha-2)     │
│  CL, US, BR, MX, PE, VE, CO, EC         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Capa 2: ESTADO/REGIÓN/DEPARTAMENTO     │
│  Modelo: Estado                          │
│  - Chile: Región Metropolitana (RM)     │
│  - USA: California (CA)                  │
│  - Brasil: São Paulo (SP)                │
│  - México: Jalisco (JA)                  │
│  - Perú: Lima (LIM)                      │
│  - Venezuela: Distrito Capital (DC)      │
│  - Colombia: Cundinamarca (CUN)          │
│  - Ecuador: Pichincha (P)                │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Capa 3: CIUDAD                          │
│  Modelo: Ciudad                           │
│  FK a Estado                              │
│  - Santiago (RM, Chile)                   │
│  - Los Angeles (CA, USA)                  │
│  - São Paulo (SP, Brasil)                 │
│  - Guadalajara (JA, México)               │
│  - Lima (LIM, Perú)                       │
│  - Caracas (DC, Venezuela)                │
│  - Bogotá (CUN, Colombia)                 │
│  - Quito (P, Ecuador)                     │
└─────────────────────────────────────────┘
```

---

## 2️⃣ **MODELOS DE DATOS**

### **Estado** (taller/models/ubicacion.py)

```python
class Estado(models.Model):
    """
    Unidad administrativa de nivel 1:
    - Chile: Región
    - USA: State
    - Brasil: Estado
    - México: Estado
    - Perú: Departamento
    - Venezuela: Estado
    - Colombia: Departamento
    - Ecuador: Provincia
    """
    nombre = models.CharField(max_length=100)  # "Región Metropolitana"
    codigo = models.CharField(max_length=10)   # "RM", "CA", "SP"
    pais = models.CharField(max_length=2)      # ISO 3166-1 alpha-2
    
    # Impuestos por estado
    sales_tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Metadatos
    timezone = models.CharField(max_length=50)
    
    # Campos específicos por país (opcionales)
    codigo_ibge = models.CharField(...)  # Brasil
    nome = models.CharField(...)         # Brasil (portugués)
    sigla = models.CharField(...)        # Brasil
    
    class Meta:
        unique_together = [("pais", "codigo")]  # ✅ Clave compuesta
```

### **Ciudad** (taller/models/ubicacion.py)

```python
class Ciudad(models.Model):
    """
    Ciudad/Municipio dentro de un Estado
    """
    nombre = models.CharField(max_length=100)  # "Santiago"
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    
    # Metadatos útiles
    poblacion = models.IntegerField(null=True, blank=True)
    es_capital = models.BooleanField(default=False)
    latitud = models.DecimalField(...)
    longitud = models.DecimalField(...)
    
    # Impuesto local (se suma al del estado)
    sales_tax_local = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Campos específicos Brasil
    codigo_ibge = models.CharField(...)
    nome = models.CharField(...)
    
    class Meta:
        unique_together = [("estado", "nombre")]  # ✅ Una ciudad por estado
        db_table = "taller_ciudad_usa"  # Reutiliza tabla existente
```

### **Address** (ubicacion/models.py)

```python
class Address(models.Model):
    """
    Dirección completa multi-país
    """
    # Líneas de dirección
    line1 = models.CharField(max_length=160)  # "123 Main St"
    line2 = models.CharField(max_length=160, blank=True)  # "Apt 4B"
    
    # FK a Ciudad (que contiene Estado → País)
    city = models.ForeignKey("taller.Ciudad", on_delete=models.PROTECT)
    
    # Código postal
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Coordenadas (opcional para mapas)
    latitude = models.DecimalField(...)
    longitude = models.DecimalField(...)
    
    # ✅ PROPIEDAD COMPUTADA: País del address
    @property
    def pais(self):
        return self.city.estado.pais
```

### **Cliente** - Campos Legacy + Nuevos

```python
class Cliente(models.Model):
    # === CAMPOS LEGACY (mantener por compatibilidad) ===
    region = models.ForeignKey(TallerRegion, ...)      # Chile legacy
    ciudad = models.ForeignKey(TallerCiudad, ...)      # Chile legacy
    estado_usa = models.ForeignKey(EstadoUSA, ...)     # USA/BR/VE/PE legacy
    ciudad_usa = models.ForeignKey(CiudadUSA, ...)     # USA/BR/VE/PE legacy
    zipcode = models.CharField(...)                    # Legacy
    direccion = models.CharField(...)                  # Legacy (texto libre)
    
    # === NUEVOS CAMPOS (arquitectura limpia) ===
    billing_address = models.ForeignKey("ubicacion.Address", ...)
    shipping_address = models.ForeignKey("ubicacion.Address", ...)
```

---

## 3️⃣ **PAÍSES SOPORTADOS**

### Tabla de Cobertura

| País | ISO | División L1 | Cantidad | Ciudades Pre-cargadas | Comando |
|------|-----|-------------|----------|----------------------|---------|
| 🇨🇱 Chile | CL | Regiones | 16 | ~50 principales | `cargar_estados_chile` |
| 🇺🇸 USA | US | States | 50 + DC | ~300 principales | `cargar_estados_usa` ✅ |
| 🇧🇷 Brasil | BR | Estados | 27 | ~100 principales | `cargar_estados_brasil` ✅ |
| 🇲🇽 México | MX | Estados | 32 | ~60 principales | `cargar_estados_mexico` ✅ |
| 🇵🇪 Perú | PE | Departamentos | 25 | ~50 principales | `cargar_estados_peru` ✅ |
| 🇻🇪 Venezuela | VE | Estados | 24 | ~40 principales | `cargar_estados_venezuela` ✅ |
| 🇨🇴 Colombia | CO | Departamentos | 33 | ~60 principales | `cargar_estados_colombia` 🚧 |
| 🇪🇨 Ecuador | EC | Provincias | 24 | ~40 principales | `cargar_estados_ecuador` 🚧 |

**Leyenda:**
- ✅ = Implementado y en producción
- 🚧 = Por implementar

---

## 4️⃣ **MIGRACIÓN DESDE LEGACY**

### Estrategia de Migración (sin romper nada)

#### Fase 1: Convivencia (Actual) ✅

```
Cliente tiene:
├── Campos legacy (funcionando)
│   ├── region, ciudad (Chile)
│   ├── estado_usa, ciudad_usa (USA/BR/VE/PE)
│   └── zipcode, direccion (texto)
└── Campos nuevos (opcional)
    ├── billing_address (FK a Address)
    └── shipping_address (FK a Address)

Regla: Si billing_address existe, usarlo. Si no, usar legacy.
```

#### Fase 2: Backfill Progresivo 🚧

```bash
# Comando existente para migrar datos legacy a Address
python manage.py backfill_addresses --dry-run  # Preview
python manage.py backfill_addresses            # Ejecutar
```

**Lógica del backfill:**
1. Para cada Cliente sin `billing_address`:
   - Si tiene `region` y `ciudad` (Chile):
     - Buscar/crear Estado equivalente con país CL
     - Buscar/crear Ciudad equivalente
     - Crear Address con city = ciudad_nueva
   - Si tiene `estado_usa` y `ciudad_usa`:
     - Ya está en el modelo nuevo (Estado/Ciudad)
     - Crear Address con city = ciudad_usa
   - Asignar `billing_address` al Cliente

2. **NO borrar** campos legacy todavía

#### Fase 3: Deprecación (Futuro) 🔮

Después de 2-3 releases con Fase 2 estable:
1. Migración para hacer `billing_address` obligatorio
2. Migración para borrar columnas legacy
3. Actualizar formularios legacy

---

## 5️⃣ **CARGA DE DATOS**

### Comandos de Management

Cada país tiene su comando de carga:

```bash
# Chile (16 regiones + ~50 ciudades)
python manage.py cargar_estados_chile

# USA (51 entidades + ~300 ciudades)
python manage.py cargar_estados_usa

# Brasil (27 estados + ~100 ciudades)
python manage.py cargar_estados_brasil

# México (32 estados + ~60 ciudades)
python manage.py cargar_estados_mexico

# Perú (25 departamentos + ~50 ciudades)
python manage.py cargar_estados_peru

# Venezuela (24 estados + ~40 ciudades)
python manage.py cargar_estados_venezuela

# Colombia (33 departamentos + ~60 ciudades) 🚧
python manage.py cargar_estados_colombia

# Ecuador (24 provincias + ~40 ciudades) 🚧
python manage.py cargar_estados_ecuador
```

### Estructura del Comando (Ejemplo)

```python
class Command(BaseCommand):
    help = "Carga estados/ciudades de [PAÍS]"
    
    def handle(self, *args, **options):
        # 1. Definir datos
        estados_data = [
            {
                "codigo": "RM",
                "nombre": "Región Metropolitana",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),  # IVA Chile
                "ciudades": [
                    {"nombre": "Santiago", "es_capital": True},
                    {"nombre": "Puente Alto"},
                    # ... más ciudades
                ]
            },
            # ... más estados
        ]
        
        # 2. Crear/actualizar Estados
        for data in estados_data:
            estado, created = Estado.objects.update_or_create(
                pais="CL",
                codigo=data["codigo"],
                defaults={
                    "nombre": data["nombre"],
                    "timezone": data["timezone"],
                    "sales_tax": data["sales_tax"],
                }
            )
            
            # 3. Crear ciudades
            for ciudad_data in data["ciudades"]:
                Ciudad.objects.get_or_create(
                    estado=estado,
                    nombre=ciudad_data["nombre"],
                    defaults={"es_capital": ciudad_data.get("es_capital", False)}
                )
        
        self.stdout.write(self.style.SUCCESS("✅ Carga completada"))
```

### Idempotencia

Todos los comandos son **idempotentes**:
- Usan `get_or_create()` o `update_or_create()`
- No borran datos existentes
- Se pueden ejecutar múltiples veces sin problemas

---

## 6️⃣ **USO EN FORMULARIOS**

### Formulario Unificado (CustomerForm)

```python
from taller.models.ubicacion import Estado, Ciudad
from ubicacion.models import Address

class CustomerForm(forms.ModelForm):
    # Select dinámico de estado (filtrado por país de la empresa)
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.none(),  # Se llena en __init__
        required=False,
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-ciudades-url": "/api/ciudades/",  # AJAX endpoint
        })
    )
    
    # Select dinámico de ciudad (filtrado por estado seleccionado)
    ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),  # Se llena vía AJAX
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    # Campos de dirección
    direccion_linea1 = forms.CharField(max_length=160, required=True)
    direccion_linea2 = forms.CharField(max_length=160, required=False)
    codigo_postal = forms.CharField(max_length=20, required=False)
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        
        # Filtrar estados por país de la empresa
        if self.empresa and self.empresa.pais:
            self.fields["estado"].queryset = Estado.objects.filter(
                pais=self.empresa.pais
            ).order_by("nombre")
        
        # Si es edición, cargar ciudades del estado actual
        if self.instance.pk and self.instance.billing_address:
            estado = self.instance.billing_address.city.estado
            self.fields["ciudad"].queryset = Ciudad.objects.filter(
                estado=estado
            ).order_by("nombre")
    
    def save(self, commit=True):
        cliente = super().save(commit=False)
        
        # Crear Address desde los campos del formulario
        if self.cleaned_data.get("ciudad"):
            address = Address.objects.create(
                line1=self.cleaned_data["direccion_linea1"],
                line2=self.cleaned_data.get("direccion_linea2", ""),
                city=self.cleaned_data["ciudad"],
                postal_code=self.cleaned_data.get("codigo_postal", "")
            )
            cliente.billing_address = address
        
        if commit:
            cliente.save()
        
        return cliente
```

### AJAX para Cascada Estado → Ciudad

```python
# taller/clientes/views.py

def ajax_ciudades_por_estado(request):
    """
    Endpoint AJAX para obtener ciudades de un estado.
    GET /api/ciudades/?estado_id=123
    """
    estado_id = request.GET.get("estado_id")
    
    if not estado_id:
        return JsonResponse({"error": "estado_id requerido"}, status=400)
    
    ciudades = Ciudad.objects.filter(estado_id=estado_id).order_by("nombre")
    
    data = [
        {"id": c.id, "nombre": c.nombre}
        for c in ciudades
    ]
    
    return JsonResponse(data, safe=False)
```

### JavaScript para Select Dinámico

```javascript
// Cuando cambia el select de estado
$("#id_estado").on("change", function() {
    const estadoId = $(this).val();
    const $ciudadSelect = $("#id_ciudad");
    
    if (!estadoId) {
        $ciudadSelect.html('<option value="">Seleccione ciudad</option>');
        return;
    }
    
    // Cargar ciudades vía AJAX
    $.ajax({
        url: "/api/ciudades/",
        data: { estado_id: estadoId },
        success: function(ciudades) {
            $ciudadSelect.html('<option value="">Seleccione ciudad</option>');
            ciudades.forEach(function(ciudad) {
                $ciudadSelect.append(
                    $("<option>").val(ciudad.id).text(ciudad.nombre)
                );
            });
        }
    });
});
```

---

## 7️⃣ **AGREGAR UBICACIONES ON-THE-FLY**

### Caso de Uso
Usuario está llenando el formulario de Cliente y la ciudad que necesita **no está** en la lista.

### Solución 1: Campo "Otra ciudad" (Más simple)

```python
class CustomerForm(forms.ModelForm):
    # ... campos normales ...
    
    ciudad_otra = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Si no encuentra la ciudad, escríbala aquí"
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        ciudad = cleaned_data.get("ciudad")
        ciudad_otra = cleaned_data.get("ciudad_otra")
        estado = cleaned_data.get("estado")
        
        # Validar que al menos una esté presente
        if not ciudad and not ciudad_otra:
            raise forms.ValidationError("Debe seleccionar o escribir una ciudad")
        
        # Si escribió otra ciudad, crearla
        if ciudad_otra and estado:
            ciudad, created = Ciudad.objects.get_or_create(
                estado=estado,
                nombre=ciudad_otra.strip().title(),
                defaults={"es_capital": False}
            )
            cleaned_data["ciudad"] = ciudad
        
        return cleaned_data
```

### Solución 2: Modal "Agregar Ciudad" (Más sofisticada)

```html
<!-- Modal en el template -->
<div id="modalAgregarCiudad" class="modal">
    <div class="modal-content">
        <h3>Agregar Nueva Ciudad</h3>
        <form id="formAgregarCiudad">
            <input type="text" id="nuevaCiudadNombre" placeholder="Nombre de la ciudad">
            <button type="submit">Agregar</button>
        </form>
    </div>
</div>

<!-- Botón junto al select de ciudad -->
<button type="button" onclick="mostrarModalAgregarCiudad()">
    ➕ Agregar ciudad
</button>
```

```javascript
function mostrarModalAgregarCiudad() {
    const estadoId = $("#id_estado").val();
    if (!estadoId) {
        alert("Primero seleccione un estado/región");
        return;
    }
    $("#modalAgregarCiudad").show();
}

$("#formAgregarCiudad").on("submit", function(e) {
    e.preventDefault();
    const estadoId = $("#id_estado").val();
    const nombreCiudad = $("#nuevaCiudadNombre").val().trim();
    
    // POST a endpoint para crear ciudad
    $.ajax({
        url: "/api/ciudades/crear/",
        method: "POST",
        data: {
            estado_id: estadoId,
            nombre: nombreCiudad,
            csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val()
        },
        success: function(ciudad) {
            // Agregar al select
            $("#id_ciudad").append(
                $("<option>").val(ciudad.id).text(ciudad.nombre).prop("selected", true)
            );
            $("#modalAgregarCiudad").hide();
        }
    });
});
```

```python
# Vista para crear ciudad on-the-fly
@require_POST
def ajax_crear_ciudad(request):
    estado_id = request.POST.get("estado_id")
    nombre = request.POST.get("nombre", "").strip()
    
    if not estado_id or not nombre:
        return JsonResponse({"error": "Datos incompletos"}, status=400)
    
    try:
        estado = Estado.objects.get(pk=estado_id)
    except Estado.DoesNotExist:
        return JsonResponse({"error": "Estado no existe"}, status=404)
    
    # Crear ciudad (o devolver existente)
    ciudad, created = Ciudad.objects.get_or_create(
        estado=estado,
        nombre=nombre.title(),
        defaults={"es_capital": False}
    )
    
    return JsonResponse({
        "id": ciudad.id,
        "nombre": ciudad.nombre,
        "created": created
    })
```

---

## 8️⃣ **API Y QUERIES**

### Queries Comunes

```python
# Obtener todos los estados de un país
estados_chile = Estado.objects.filter(pais="CL").order_by("nombre")

# Obtener todas las ciudades de un estado
ciudades_rm = Ciudad.objects.filter(estado__codigo="RM", estado__pais="CL")

# Obtener país de un Address
address = Address.objects.get(pk=123)
pais = address.city.estado.pais  # "CL", "US", etc.

# Buscar clientes por país
clientes_usa = Cliente.objects.filter(
    billing_address__city__estado__pais="US"
)

# Agregar select_related para optimización
addresses = Address.objects.select_related(
    "city__estado"
).filter(city__estado__pais="BR")
```

### Endpoints REST (opcional)

```python
# urls.py
urlpatterns = [
    path("api/estados/", views.api_estados, name="api_estados"),
    path("api/ciudades/", views.api_ciudades, name="api_ciudades"),
    path("api/ciudades/crear/", views.ajax_crear_ciudad, name="api_crear_ciudad"),
]

# views.py
def api_estados(request):
    """Lista estados filtrados por país"""
    pais = request.GET.get("pais")
    qs = Estado.objects.all()
    
    if pais:
        qs = qs.filter(pais=pais)
    
    data = [
        {
            "id": e.id,
            "codigo": e.codigo,
            "nombre": e.nombre,
            "pais": e.pais
        }
        for e in qs.order_by("nombre")
    ]
    
    return JsonResponse(data, safe=False)
```

---

## 🎯 **RESUMEN DE DECISIONES CLAVE**

1. ✅ **Usar ISO 3166-1 alpha-2** para códigos de país (CL, US, BR, etc.)
2. ✅ **Modelo Estado único** para todas las divisiones administrativas L1
3. ✅ **Ciudad con FK a Estado** (no a País directamente)
4. ✅ **Address como capa de abstracción** sobre Ciudad
5. ✅ **Campos legacy se mantienen** hasta backfill completo
6. ✅ **Comandos idempotentes** para carga de datos
7. ✅ **Formularios permiten agregar ubicaciones** si no existen
8. ✅ **AJAX para select dinámico** Estado → Ciudad

---

## 📝 **PRÓXIMOS PASOS**

### Inmediatos
- [ ] Crear comando `cargar_estados_chile`
- [ ] Crear comando `cargar_estados_colombia`
- [ ] Crear comando `cargar_estados_ecuador`
- [ ] Agregar CO y EC a choices de Estado.pais
- [ ] Actualizar formularios legacy para usar nuevos modelos

### Mediano Plazo
- [ ] Ejecutar `backfill_addresses` en producción
- [ ] Migrar vistas de creación/edición a CustomerForm
- [ ] Dashboard de cobertura de ubicaciones por país

### Largo Plazo
- [ ] Deprecar campos legacy (región, ciudad, estado_usa, etc.)
- [ ] Integración con APIs de geocoding (Google Maps, OpenStreetMap)
- [ ] Sistema de validación de códigos postales por país

---

## 🔗 **REFERENCIAS**

- [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
- [Divisiones administrativas por país](https://en.wikipedia.org/wiki/Table_of_administrative_divisions_by_country)
- Django GeoDjango: https://docs.djangoproject.com/en/stable/ref/contrib/gis/

