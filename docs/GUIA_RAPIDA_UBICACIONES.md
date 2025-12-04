# 🚀 GUÍA RÁPIDA - Sistema de Ubicaciones Multi-País

> **¿Qué es esto?** Un sistema completo para manejar ubicaciones geográficas (estados/regiones y ciudades) para 8 países de LATAM y USA.

---

## ⚡ INICIO RÁPIDO (3 pasos)

### 1️⃣ **Cargar todas las ubicaciones**

```bash
# Carga TODOS los países (CL, US, BR, MX, PE, VE, CO, EC)
python manage.py cargar_todas_ubicaciones
```

**Resultado esperado:**
- ✅ ~200 estados/regiones/departamentos
- ✅ ~800+ ciudades principales
- ⏱️ Tiempo: 2-5 minutos

### 2️⃣ **Verificar que todo está bien**

```bash
# Ver resumen de lo cargado
python manage.py verificar_ubicaciones
```

**Deberías ver:**
```
✅ Chile: 16 regiones, 100+ ciudades
✅ USA: 51 estados, 300+ ciudades
✅ Brasil: 27 estados, 100+ ciudades
... etc
```

### 3️⃣ **Migrar datos legacy (si aplica)**

```bash
# Migra clientes con campos legacy a billing_address
python manage.py backfill_addresses --dry-run  # Preview
python manage.py backfill_addresses            # Ejecutar
```

---

## 🎯 COMANDOS DISPONIBLES

### **Cargar por país individual**

```bash
# Chile (16 regiones + ~100 ciudades)
python manage.py cargar_estados_chile

# USA (51 estados + ~300 ciudades)
python manage.py cargar_estados_usa

# Brasil (27 estados + ~100 ciudades)
python manage.py cargar_estados_brasil

# México (32 estados + ~60 ciudades)
python manage.py cargar_estados_mexico

# Perú (25 departamentos + ~50 ciudades)
python manage.py cargar_estados_peru

# Venezuela (24 estados + ~40 ciudades)
python manage.py cargar_estados_venezuela

# Colombia (33 departamentos + ~60 ciudades)
python manage.py cargar_estados_colombia

# Ecuador (24 provincias + ~40 ciudades)
python manage.py cargar_estados_ecuador
```

### **Cargar múltiples países**

```bash
# Solo Chile, Colombia y Ecuador
python manage.py cargar_todas_ubicaciones --paises CL CO EC

# Todos excepto los que ya tienen datos
python manage.py cargar_todas_ubicaciones --skip-existing
```

### **Verificación y diagnóstico**

```bash
# Resumen general
python manage.py verificar_ubicaciones

# Solo un país específico
python manage.py verificar_ubicaciones --pais CL

# Con detalle de estados y ciudades
python manage.py verificar_ubicaciones --detallado
```

---

## 📊 MODELOS DE DATOS

### **Estado** (Región/Departamento/Provincia)

```python
from taller.models.ubicacion import Estado

# Obtener estados de un país
estados_chile = Estado.objects.filter(pais="CL")

# Buscar estado específico
rm = Estado.objects.get(pais="CL", codigo="RM")  # Región Metropolitana
california = Estado.objects.get(pais="US", codigo="CA")  # California

# Acceder a ciudades
ciudades_rm = rm.ciudades.all()
```

### **Ciudad**

```python
from taller.models.ubicacion import Ciudad

# Obtener ciudades de un estado
ciudades_california = Ciudad.objects.filter(estado__codigo="CA", estado__pais="US")

# Buscar ciudad específica
santiago = Ciudad.objects.get(nombre="Santiago", estado__pais="CL")

# Acceder al estado/país
print(santiago.estado.nombre)  # "Región Metropolitana de Santiago"
print(santiago.estado.pais)     # "CL"
```

### **Address** (Dirección completa)

```python
from ubicacion.models import Address
from taller.models.ubicacion import Ciudad

# Crear dirección
ciudad = Ciudad.objects.get(nombre="Santiago", estado__pais="CL")

address = Address.objects.create(
    line1="Av. Providencia 123",
    line2="Oficina 456",
    city=ciudad,
    postal_code="7500000"
)

# Acceder a país desde Address
print(address.pais)  # "CL" (propiedad computada)
print(address.city.estado.nombre)  # "Región Metropolitana de Santiago"
```

---

## 🔧 USO EN FORMULARIOS

### **Ejemplo básico: Select dinámico Estado → Ciudad**

```python
# forms.py
from django import forms
from taller.models.ubicacion import Estado, Ciudad

class ClienteForm(forms.Form):
    estado = forms.ModelChoiceField(
        queryset=Estado.objects.none(),  # Se llena en __init__
        widget=forms.Select(attrs={
            "class": "form-control",
            "data-ciudades-url": "/api/ciudades/"  # Endpoint AJAX
        })
    )
    
    ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),  # Se llena vía AJAX
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        
        # Filtrar estados por país de la empresa
        if empresa and empresa.pais:
            self.fields["estado"].queryset = Estado.objects.filter(
                pais=empresa.pais
            ).order_by("nombre")
```

### **Endpoint AJAX para ciudades**

```python
# views.py
from django.http import JsonResponse
from taller.models.ubicacion import Ciudad

def ajax_ciudades_por_estado(request):
    estado_id = request.GET.get("estado_id")
    
    if not estado_id:
        return JsonResponse({"error": "estado_id requerido"}, status=400)
    
    ciudades = Ciudad.objects.filter(estado_id=estado_id).order_by("nombre")
    
    return JsonResponse([
        {"id": c.id, "nombre": c.nombre}
        for c in ciudades
    ], safe=False)
```

### **JavaScript para cascada**

```javascript
// Cuando cambia el estado, cargar ciudades
$("#id_estado").on("change", function() {
    const estadoId = $(this).val();
    const $ciudadSelect = $("#id_ciudad");
    
    if (!estadoId) {
        $ciudadSelect.html('<option value="">Seleccione ciudad</option>');
        return;
    }
    
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

## 💡 AGREGAR UBICACIONES ON-THE-FLY

### **Opción 1: Campo "Otra ciudad"**

```python
class ClienteForm(forms.Form):
    # ... campos normales ...
    
    ciudad_otra = forms.CharField(
        max_length=100,
        required=False,
        help_text="Si no encuentra la ciudad, escríbala aquí"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        ciudad = cleaned_data.get("ciudad")
        ciudad_otra = cleaned_data.get("ciudad_otra")
        estado = cleaned_data.get("estado")
        
        # Si escribió otra ciudad, crearla
        if ciudad_otra and estado:
            ciudad, created = Ciudad.objects.get_or_create(
                estado=estado,
                nombre=ciudad_otra.strip().title()
            )
            cleaned_data["ciudad"] = ciudad
        
        return cleaned_data
```

### **Opción 2: Endpoint para crear ciudad**

```python
# views.py
from django.views.decorators.http import require_POST

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
    
    ciudad, created = Ciudad.objects.get_or_create(
        estado=estado,
        nombre=nombre.title()
    )
    
    return JsonResponse({
        "id": ciudad.id,
        "nombre": ciudad.nombre,
        "created": created
    })
```

---

## 🔍 QUERIES COMUNES

```python
# Obtener todas las ciudades de un país
ciudades_chile = Ciudad.objects.filter(estado__pais="CL")

# Buscar clientes por país (usando Address)
clientes_usa = Cliente.objects.filter(
    billing_address__city__estado__pais="US"
)

# Contar clientes por estado
from django.db.models import Count

stats = Estado.objects.filter(pais="CL").annotate(
    num_clientes=Count("ciudades__addresses__clients_billing")
)

for estado in stats:
    print(f"{estado.nombre}: {estado.num_clientes} clientes")

# Optimizar queries con select_related
addresses = Address.objects.select_related(
    "city__estado"
).filter(city__estado__pais="BR")
```

---

## 📋 CHECKLIST DE DEPLOYMENT

### **Primera vez en producción:**

```bash
# 1. Aplicar migraciones
python manage.py migrate

# 2. Cargar ubicaciones
python manage.py cargar_todas_ubicaciones

# 3. Verificar carga
python manage.py verificar_ubicaciones

# 4. Migrar datos legacy (si aplica)
python manage.py backfill_addresses --dry-run
python manage.py backfill_addresses

# 5. Verificar migración
python manage.py verificar_ubicaciones
```

### **Actualización posterior:**

```bash
# Cargar solo países nuevos
python manage.py cargar_todas_ubicaciones --skip-existing

# O cargar país específico
python manage.py cargar_estados_colombia
```

---

## 🚨 TROUBLESHOOTING

### **Problema: "Ciudad ya existe"**
```python
# Los comandos usan get_or_create, son idempotentes
# Si ya existe, solo la actualiza
python manage.py cargar_estados_chile  # OK ejecutar múltiples veces
```

### **Problema: "No aparecen ciudades en el formulario"**
```javascript
// Verificar que el endpoint AJAX esté configurado
console.log($("#id_estado").data("ciudades-url"));

// Verificar respuesta del endpoint
fetch("/api/ciudades/?estado_id=123")
    .then(r => r.json())
    .then(console.log);
```

### **Problema: "Clientes sin billing_address"**
```bash
# Ejecutar backfill
python manage.py backfill_addresses

# Verificar progreso
python manage.py verificar_ubicaciones
```

---

## 📚 RECURSOS ADICIONALES

- **Documentación completa:** `docs/ARQUITECTURA_UBICACIONES_MULTI_PAIS.md`
- **Códigos ISO 3166-1:** https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
- **Divisiones administrativas:** https://en.wikipedia.org/wiki/Table_of_administrative_divisions_by_country

---

## 🎯 RESUMEN DE ARQUITECTURA

```
País (ISO 3166-1 alpha-2)
  ↓
Estado/Región/Departamento/Provincia
  ↓
Ciudad
  ↓
Address (Dirección completa)
  ↓
Cliente.billing_address / shipping_address
```

**Regla de oro:** 
- ✅ **Usar:** `billing_address` (Address → Ciudad → Estado → País)
- ❌ **Evitar:** Campos legacy (`region`, `ciudad`, `estado_usa`, `ciudad_usa`)

---

## ✅ PRÓXIMOS PASOS RECOMENDADOS

1. ✅ **Cargar ubicaciones:** `python manage.py cargar_todas_ubicaciones`
2. ✅ **Verificar carga:** `python manage.py verificar_ubicaciones`
3. ✅ **Actualizar formularios** para usar los nuevos modelos
4. ✅ **Migrar datos legacy:** `python manage.py backfill_addresses`
5. ✅ **Deprecar campos legacy** en 2-3 releases

¡Listo! 🎉

