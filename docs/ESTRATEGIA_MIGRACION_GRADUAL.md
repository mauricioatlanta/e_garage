# 🔄 ESTRATEGIA DE MIGRACIÓN GRADUAL - Sin Romper Nada

> **Objetivo:** Usar los nuevos modelos (Estado/Ciudad) en formularios mientras se mantiene compatibilidad con campos legacy

---

## 🎯 **FILOSOFÍA: CONVIVENCIA PACÍFICA**

```
┌─────────────────────────────────────────────────────────┐
│                    FORMULARIOS                          │
│  Usan: Estado/Ciudad (modelos nuevos)                   │
│  Selects con datos pre-cargados                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                AL GUARDAR CLIENTE                        │
│  ✅ Crea Address con Ciudad nueva                       │
│  ✅ Asigna billing_address al cliente                   │
│  ✅ TAMBIÉN rellena campos legacy (compatibilidad)      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                   CLIENTE (BD)                           │
│  ┌─────────────────────────────────────────────┐        │
│  │ CAMPOS LEGACY (mantenidos):                 │        │
│  │  • region (TallerRegion)                    │        │
│  │  • ciudad (TallerCiudad)                    │        │
│  │  • estado_usa (Estado)                      │        │
│  │  • ciudad_usa (Ciudad)                      │        │
│  │  • zipcode                                  │        │
│  └─────────────────────────────────────────────┘        │
│                                                          │
│  ┌─────────────────────────────────────────────┐        │
│  │ CAMPOS NUEVOS (usar preferentemente):       │        │
│  │  • billing_address → Address → Ciudad → Estado│     │
│  │  • shipping_address                          │        │
│  └─────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                CÓDIGO EXISTENTE                          │
│  Sigue funcionando porque campos legacy existen         │
│  No se rompe nada ✅                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 **ESTADO ACTUAL (YA IMPLEMENTADO)**

### **Modelo Cliente actual:**

```python
class Cliente(models.Model):
    # === CAMPOS LEGACY ===
    # Chile (FK a modelos viejos)
    region = models.ForeignKey(TallerRegion, ...)      # Región vieja
    ciudad = models.ForeignKey(TallerCiudad, ...)      # Ciudad vieja
    
    # Otros países (FK a modelos NUEVOS, pero nombres legacy)
    estado_usa = models.ForeignKey(EstadoUSA, ...)     # EstadoUSA = Estado (nuevo)
    ciudad_usa = models.ForeignKey(CiudadUSA, ...)     # CiudadUSA = Ciudad (nuevo)
    zipcode = models.CharField(...)
    
    # === CAMPOS NUEVOS ===
    billing_address = models.ForeignKey("ubicacion.Address", ...)
    shipping_address = models.ForeignKey("ubicacion.Address", ...)
```

**Nota importante:**
```python
# En taller/models/clientes.py (líneas 5-7):
from .ubicacion import Ciudad as CiudadUSA
from .ubicacion import Estado as EstadoUSA

# ✅ EstadoUSA y CiudadUSA SON LOS MODELOS NUEVOS
# ✅ Solo TallerRegion y TallerCiudad son legacy
```

---

## 🚀 **IMPLEMENTACIÓN: FORMULARIO CON MIGRACIÓN GRADUAL**

### **Paso 1: Formulario que usa modelos nuevos**

```python
# taller/clientes/forms_hybrid.py

from django import forms
from taller.models.clientes import Cliente
from taller.models.ubicacion import Estado, Ciudad
from taller.models.region_ciudad import TallerRegion, TallerCiudad
from ubicacion.models import Address


class ClienteHybridForm(forms.ModelForm):
    """
    Formulario que usa modelos nuevos (Estado/Ciudad) pero mantiene
    compatibilidad con campos legacy.
    """
    
    # === CAMPOS DE FORMULARIO (usan modelos NUEVOS) ===
    
    estado_selector = forms.ModelChoiceField(
        queryset=Estado.objects.none(),  # Se llena en __init__
        required=False,
        label="Estado/Región",
        widget=forms.Select(attrs={
            "class": "form-control",
            "id": "id_estado_selector",
            "data-ciudades-url": "/api/ciudades/",
        })
    )
    
    ciudad_selector = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),  # Se llena vía AJAX
        required=False,
        label="Ciudad",
        widget=forms.Select(attrs={
            "class": "form-control",
            "id": "id_ciudad_selector",
        })
    )
    
    # Campos de dirección
    direccion_linea1 = forms.CharField(
        max_length=160,
        required=False,
        label="Dirección",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    
    codigo_postal = forms.CharField(
        max_length=20,
        required=False,
        label="Código Postal / Zipcode",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    
    class Meta:
        model = Cliente
        fields = [
            "nombre",
            "apellido",
            "telefono",
            "email",
            # NO incluir region, ciudad, estado_usa, ciudad_usa
            # Se llenarán automáticamente en save()
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        
        # Filtrar estados por país de la empresa
        if self.empresa and self.empresa.pais:
            self.fields["estado_selector"].queryset = Estado.objects.filter(
                pais=self.empresa.pais
            ).order_by("nombre")
        
        # Si es edición, pre-cargar valores
        if self.instance.pk:
            # Si tiene billing_address, usar eso
            if self.instance.billing_address:
                ciudad = self.instance.billing_address.city
                self.fields["ciudad_selector"].initial = ciudad
                self.fields["estado_selector"].initial = ciudad.estado
                self.fields["direccion_linea1"].initial = self.instance.billing_address.line1
                self.fields["codigo_postal"].initial = self.instance.billing_address.postal_code
                
                # Cargar ciudades del estado
                self.fields["ciudad_selector"].queryset = Ciudad.objects.filter(
                    estado=ciudad.estado
                ).order_by("nombre")
            
            # Si NO tiene billing_address pero tiene campos legacy
            elif self.instance.estado_usa_id:
                # Usuario de país NO-Chile con estado_usa
                self.fields["estado_selector"].initial = self.instance.estado_usa
                if self.instance.ciudad_usa:
                    self.fields["ciudad_selector"].initial = self.instance.ciudad_usa
                    self.fields["ciudad_selector"].queryset = Ciudad.objects.filter(
                        estado=self.instance.estado_usa
                    ).order_by("nombre")
                if self.instance.zipcode:
                    self.fields["codigo_postal"].initial = self.instance.zipcode
    
    def save(self, commit=True):
        cliente = super().save(commit=False)
        
        # === ESTRATEGIA: RELLENAR AMBOS (nuevo Y legacy) ===
        
        estado = self.cleaned_data.get("estado_selector")
        ciudad = self.cleaned_data.get("ciudad_selector")
        direccion = self.cleaned_data.get("direccion_linea1", "")
        codigo_postal = self.cleaned_data.get("codigo_postal", "")
        
        if ciudad:
            # === 1. CREAR/ACTUALIZAR ADDRESS (NUEVO) ===
            if self.instance.billing_address:
                # Actualizar existente
                address = self.instance.billing_address
                address.line1 = direccion
                address.city = ciudad
                address.postal_code = codigo_postal
                address.save()
            else:
                # Crear nuevo
                address = Address.objects.create(
                    line1=direccion or "N/A",
                    city=ciudad,
                    postal_code=codigo_postal
                )
                cliente.billing_address = address
            
            # === 2. RELLENAR CAMPOS LEGACY (COMPATIBILIDAD) ===
            
            # Determinar si es Chile o no
            if estado.pais == "CL":
                # Chile: usar TallerRegion/TallerCiudad
                # Buscar/crear equivalentes en modelos legacy
                taller_region, _ = TallerRegion.objects.get_or_create(
                    nombre=estado.nombre
                )
                taller_ciudad, _ = TallerCiudad.objects.get_or_create(
                    nombre=ciudad.nombre,
                    region=taller_region
                )
                
                cliente.region = taller_region
                cliente.ciudad = taller_ciudad
                # Limpiar campos USA
                cliente.estado_usa = None
                cliente.ciudad_usa = None
            
            else:
                # Otros países: usar estado_usa/ciudad_usa (que SON Estado/Ciudad nuevos)
                cliente.estado_usa = estado
                cliente.ciudad_usa = ciudad
                cliente.zipcode = codigo_postal
                # Limpiar campos Chile
                cliente.region = None
                cliente.ciudad = None
        
        if commit:
            cliente.save()
        
        return cliente
```

---

## 📝 **EJEMPLO DE USO EN VISTA**

```python
# taller/clientes/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms_hybrid import ClienteHybridForm
from taller.models.clientes import Cliente


@login_required
def crear_cliente(request):
    """
    Vista para crear cliente usando formulario híbrido
    """
    empresa = request.user.empresa
    
    if request.method == "POST":
        form = ClienteHybridForm(request.POST, empresa=empresa)
        if form.is_valid():
            cliente = form.save()
            return redirect("cliente_detalle", pk=cliente.pk)
    else:
        form = ClienteHybridForm(empresa=empresa)
    
    return render(request, "clientes/cliente_form.html", {
        "form": form,
        "titulo": "Crear Cliente",
    })


@login_required
def editar_cliente(request, pk):
    """
    Vista para editar cliente
    """
    empresa = request.user.empresa
    cliente = get_object_or_404(Cliente, pk=pk, empresa=empresa)
    
    if request.method == "POST":
        form = ClienteHybridForm(request.POST, instance=cliente, empresa=empresa)
        if form.is_valid():
            cliente = form.save()
            return redirect("cliente_detalle", pk=cliente.pk)
    else:
        form = ClienteHybridForm(instance=cliente, empresa=empresa)
    
    return render(request, "clientes/cliente_form.html", {
        "form": form,
        "titulo": "Editar Cliente",
        "cliente": cliente,
    })
```

---

## 🎨 **TEMPLATE CON AJAX**

```html
<!-- templates/clientes/cliente_form.html -->

{% extends "base.html" %}

{% block content %}
<div class="container">
    <h2>{{ titulo }}</h2>
    
    <form method="post">
        {% csrf_token %}
        
        <div class="row">
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_nombre">Nombre *</label>
                    {{ form.nombre }}
                </div>
            </div>
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_apellido">Apellido</label>
                    {{ form.apellido }}
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_telefono">Teléfono</label>
                    {{ form.telefono }}
                </div>
            </div>
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_email">Email</label>
                    {{ form.email }}
                </div>
            </div>
        </div>
        
        <h4>Ubicación</h4>
        
        <div class="row">
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_estado_selector">
                        {% if empresa.pais == 'CL' %}
                            Región
                        {% elif empresa.pais == 'US' %}
                            State
                        {% elif empresa.pais == 'MX' or empresa.pais == 'BR' %}
                            Estado
                        {% elif empresa.pais == 'CO' or empresa.pais == 'PE' %}
                            Departamento
                        {% elif empresa.pais == 'EC' %}
                            Provincia
                        {% else %}
                            Estado/Región
                        {% endif %}
                    </label>
                    {{ form.estado_selector }}
                </div>
            </div>
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_ciudad_selector">Ciudad</label>
                    {{ form.ciudad_selector }}
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div class="form-group">
                    <label for="id_direccion_linea1">Dirección</label>
                    {{ form.direccion_linea1 }}
                </div>
            </div>
            <div class="col-md-4">
                <div class="form-group">
                    <label for="id_codigo_postal">Código Postal</label>
                    {{ form.codigo_postal }}
                </div>
            </div>
        </div>
        
        <button type="submit" class="btn btn-primary">Guardar</button>
        <a href="{% url 'clientes_lista' %}" class="btn btn-secondary">Cancelar</a>
    </form>
</div>

<script>
// AJAX para cargar ciudades cuando cambia el estado
document.getElementById('id_estado_selector').addEventListener('change', function() {
    const estadoId = this.value;
    const ciudadSelect = document.getElementById('id_ciudad_selector');
    
    // Limpiar select de ciudades
    ciudadSelect.innerHTML = '<option value="">Seleccione Ciudad</option>';
    
    if (!estadoId) return;
    
    // Cargar ciudades vía AJAX
    fetch(`/api/ciudades/?estado_id=${estadoId}`)
        .then(response => response.json())
        .then(ciudades => {
            ciudades.forEach(ciudad => {
                const option = document.createElement('option');
                option.value = ciudad.id;
                option.textContent = ciudad.nombre;
                ciudadSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error:', error));
});
</script>
{% endblock %}
```

---

## 🔌 **ENDPOINT AJAX PARA CIUDADES**

```python
# taller/clientes/views.py

from django.http import JsonResponse
from taller.models.ubicacion import Ciudad


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


# urls.py
urlpatterns = [
    # ... otras URLs ...
    path("api/ciudades/", ajax_ciudades_por_estado, name="api_ciudades"),
]
```

---

## ✅ **VENTAJAS DE ESTE ENFOQUE**

### **1. No Rompe Nada** ✅
```python
# Código viejo sigue funcionando
if cliente.region:  # Chile legacy
    print(cliente.region.nombre)

if cliente.estado_usa:  # USA/otros legacy
    print(cliente.estado_usa.nombre)

# Código nuevo TAMBIÉN funciona
if cliente.billing_address:
    print(cliente.billing_address.city.nombre)
```

### **2. Migración Gradual** ✅
```python
# Clientes viejos: solo tienen campos legacy
# Clientes nuevos: tienen billing_address + campos legacy (duplicados)
# Código funciona con ambos
```

### **3. Formularios Modernos** ✅
```python
# Selects poblados con datos pre-cargados (~800 ciudades)
# AJAX para cascada Estado → Ciudad
# UX mejorada
```

### **4. Datos Consistentes** ✅
```python
# Al guardar, se rellenan AMBOS:
#   - billing_address (nuevo, normalizado)
#   - campos legacy (compatibilidad)
```

---

## 📊 **ESTRATEGIA DE FASES**

### **Fase 1: Implementación (Ahora)** 🚀

1. ✅ Cargar datos: `python manage.py cargar_todas_ubicaciones`
2. ✅ Crear `ClienteHybridForm` (código arriba)
3. ✅ Crear endpoint AJAX para ciudades
4. ✅ Actualizar template con selects
5. ✅ Probar creación/edición de clientes

**Resultado:** Nuevos clientes usan modelo nuevo + campos legacy llenos

---

### **Fase 2: Backfill (1-2 meses después)** 📈

```bash
# Migrar clientes viejos que solo tienen campos legacy
python manage.py backfill_addresses
```

**Resultado:** Todos los clientes tienen `billing_address`

---

### **Fase 3: Deprecación (6-12 meses después)** 🗑️

1. Verificar que todos los clientes tienen `billing_address`
2. Actualizar código para usar solo `billing_address`
3. Crear migración para borrar columnas legacy:
   ```python
   operations = [
       migrations.RemoveField("Cliente", "region"),
       migrations.RemoveField("Cliente", "ciudad"),
       migrations.RemoveField("Cliente", "estado_usa"),
       migrations.RemoveField("Cliente", "ciudad_usa"),
       migrations.RemoveField("Cliente", "zipcode"),
   ]
   ```

**Resultado:** Modelo limpio, solo `billing_address`

---

## 🎯 **RESUMEN: CÓMO FUNCIONA**

```
USUARIO LLENA FORMULARIO
  ↓
Elige Estado (de modelo NUEVO: Estado)
  ↓
AJAX carga Ciudades (de modelo NUEVO: Ciudad)
  ↓
Elige Ciudad
  ↓
Submit → save()
  ↓
┌─────────────────────────────────────────┐
│ Se guarda en DOS lugares:               │
│                                         │
│ 1. billing_address (NUEVO)              │
│    → Address                             │
│      → Ciudad                            │
│        → Estado                          │
│                                         │
│ 2. Campos legacy (COMPATIBILIDAD)       │
│    Si CL: region + ciudad                │
│    Si otros: estado_usa + ciudad_usa     │
└─────────────────────────────────────────┘
  ↓
TODO EL CÓDIGO VIEJO SIGUE FUNCIONANDO ✅
TODO EL CÓDIGO NUEVO TAMBIÉN FUNCIONA ✅
```

---

## 💡 **RECOMENDACIÓN FINAL**

**Implementa el formulario híbrido (ClienteHybridForm) ahora:**

1. ✅ Usa Estado/Ciudad en selects (datos ya cargados)
2. ✅ Guarda en `billing_address` (nuevo)
3. ✅ TAMBIÉN guarda en campos legacy (compatibilidad)
4. ✅ No se rompe nada
5. ✅ UX mejorada (selects con datos)

**Próximos pasos:**
- Fase 1: Implementar ahora (este documento)
- Fase 2: Backfill en 1-2 meses
- Fase 3: Deprecar legacy en 6-12 meses

---

**¿Listo para implementar?** 🚀

El código completo está arriba. Solo necesitas:
1. Crear `forms_hybrid.py`
2. Agregar endpoint AJAX
3. Actualizar template
4. ¡Probar!

