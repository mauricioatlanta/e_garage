# ➕ AGREGAR UBICACIONES ON-THE-FLY

> **Dos enfoques** para permitir a usuarios agregar ciudades/regiones si no existen

---

## 🎯 **OBJETIVO**

Permitir que usuarios agreguen ubicaciones que no están en la BD mientras llenan el formulario de Cliente.

**Casos de uso:**
- Cliente vive en ciudad pequeña no pre-cargada
- Ciudad nueva (fundada recientemente)
- Error u omisión en datos pre-cargados

---

## 🔀 **DOS OPCIONES IMPLEMENTABLES**

### **Comparación rápida:**

| Aspecto | Opción A: Modal | Opción B: Autocomplete |
|---------|-----------------|------------------------|
| **UX** | 🟡 Requiere modal/popup | 🟢 Seamless (inline) |
| **Complejidad** | 🟢 Simple | 🟡 Media (requiere librería) |
| **Mobile-friendly** | 🟡 Modales a veces problemáticos | 🟢 Funciona bien |
| **JavaScript** | 🟢 Vanilla JS | 🟡 Requiere Select2/DAL |
| **Control** | 🟢 Total | 🟡 Depende de librería |
| **Recomendado** | Para usuarios internos | Para usuarios finales |

---

## 🅰️ **OPCIÓN A: BOTÓN + MODAL**

### **UX Flow:**

```
1. Usuario elige Estado
   ↓
2. Ciudades se cargan en select
   ↓
3. Si no encuentra su ciudad:
   → Click en "➕ Nueva Ciudad"
   ↓
4. Se abre modal con formulario
   ↓
5. Usuario ingresa:
   - Nombre de ciudad
   - (opcional) Población
   ↓
6. Submit → Ciudad se crea
   ↓
7. Modal se cierra
   ↓
8. Select se actualiza con ciudad nueva (ya seleccionada)
```

---

### **Implementación Completa:**

#### **1. Vista para crear ciudad (AJAX)**

```python
# taller/clientes/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from taller.models.ubicacion import Estado, Ciudad


@login_required
@require_POST
def ajax_crear_ciudad(request):
    """
    Endpoint AJAX para crear ciudad on-the-fly.
    POST /api/ciudades/crear/
    
    Params:
        - estado_id: ID del estado
        - nombre: Nombre de la ciudad
        - poblacion: (opcional) Población
    """
    estado_id = request.POST.get("estado_id")
    nombre = request.POST.get("nombre", "").strip()
    poblacion = request.POST.get("poblacion", "").strip()
    
    # Validaciones
    if not estado_id:
        return JsonResponse({"error": "Estado requerido"}, status=400)
    
    if not nombre:
        return JsonResponse({"error": "Nombre de ciudad requerido"}, status=400)
    
    if len(nombre) < 2:
        return JsonResponse({"error": "Nombre muy corto (mínimo 2 caracteres)"}, status=400)
    
    # Verificar que estado existe
    try:
        estado = Estado.objects.get(pk=estado_id)
    except Estado.DoesNotExist:
        return JsonResponse({"error": "Estado no encontrado"}, status=404)
    
    # Normalizar nombre (Title Case)
    nombre_normalizado = nombre.title()
    
    # Crear o obtener ciudad
    ciudad, created = Ciudad.objects.get_or_create(
        estado=estado,
        nombre=nombre_normalizado,
        defaults={
            "poblacion": int(poblacion) if poblacion.isdigit() else None,
        }
    )
    
    # Response
    return JsonResponse({
        "id": ciudad.id,
        "nombre": ciudad.nombre,
        "estado_id": estado.id,
        "estado_nombre": estado.nombre,
        "created": created,
        "message": "Ciudad creada" if created else "Ciudad ya existía",
    })


# urls.py
urlpatterns = [
    # ... otras URLs ...
    path("api/ciudades/crear/", ajax_crear_ciudad, name="api_crear_ciudad"),
]
```

---

#### **2. Template con Modal**

```html
<!-- templates/clientes/cliente_form.html -->

{% extends "base.html" %}

{% block content %}
<div class="container">
    <h2>{{ titulo }}</h2>
    
    <form method="post" id="formCliente">
        {% csrf_token %}
        
        <!-- ... campos de nombre, teléfono, etc. ... -->
        
        <div class="row">
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_estado">Estado/Región</label>
                    {{ form.estado_selector }}
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_ciudad">Ciudad</label>
                    <div class="input-group">
                        {{ form.ciudad_selector }}
                        <div class="input-group-append">
                            <button 
                                type="button" 
                                class="btn btn-success" 
                                id="btnNuevaCiudad"
                                data-toggle="modal" 
                                data-target="#modalNuevaCiudad"
                                disabled
                            >
                                ➕ Nueva
                            </button>
                        </div>
                    </div>
                    <small class="form-text text-muted">
                        ¿No encuentras tu ciudad? Agrégala con el botón "➕ Nueva"
                    </small>
                </div>
            </div>
        </div>
        
        <button type="submit" class="btn btn-primary">Guardar Cliente</button>
    </form>
</div>


<!-- MODAL PARA CREAR CIUDAD -->
<div class="modal fade" id="modalNuevaCiudad" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">➕ Agregar Nueva Ciudad</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            
            <div class="modal-body">
                <form id="formNuevaCiudad">
                    <div class="form-group">
                        <label for="nuevaCiudadEstado">Estado/Región</label>
                        <input 
                            type="text" 
                            class="form-control" 
                            id="nuevaCiudadEstado" 
                            readonly
                        >
                        <input type="hidden" id="nuevaCiudadEstadoId">
                    </div>
                    
                    <div class="form-group">
                        <label for="nuevaCiudadNombre">Nombre de la Ciudad *</label>
                        <input 
                            type="text" 
                            class="form-control" 
                            id="nuevaCiudadNombre" 
                            required
                            placeholder="Ej: Villa Alemana"
                        >
                    </div>
                    
                    <div class="form-group">
                        <label for="nuevaCiudadPoblacion">Población (opcional)</label>
                        <input 
                            type="number" 
                            class="form-control" 
                            id="nuevaCiudadPoblacion"
                            placeholder="Ej: 150000"
                        >
                    </div>
                    
                    <div class="alert alert-info">
                        <strong>ℹ️ Nota:</strong> La ciudad se agregará a la base de datos y estará disponible para todos los usuarios.
                    </div>
                    
                    <div id="errorNuevaCiudad" class="alert alert-danger" style="display: none;"></div>
                </form>
            </div>
            
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">
                    Cancelar
                </button>
                <button type="button" class="btn btn-primary" id="btnGuardarNuevaCiudad">
                    <span class="spinner-border spinner-border-sm" role="status" style="display: none;" id="spinnerGuardar"></span>
                    Agregar Ciudad
                </button>
            </div>
        </div>
    </div>
</div>


<script>
document.addEventListener('DOMContentLoaded', function() {
    const estadoSelect = document.getElementById('id_estado_selector');
    const ciudadSelect = document.getElementById('id_ciudad_selector');
    const btnNuevaCiudad = document.getElementById('btnNuevaCiudad');
    const btnGuardarNuevaCiudad = document.getElementById('btnGuardarNuevaCiudad');
    const formNuevaCiudad = document.getElementById('formNuevaCiudad');
    
    // === CARGAR CIUDADES CUANDO CAMBIA ESTADO ===
    estadoSelect.addEventListener('change', function() {
        const estadoId = this.value;
        const estadoNombre = this.options[this.selectedIndex].text;
        
        // Limpiar select de ciudades
        ciudadSelect.innerHTML = '<option value="">Seleccione Ciudad</option>';
        btnNuevaCiudad.disabled = !estadoId;
        
        if (!estadoId) return;
        
        // Guardar estado seleccionado para modal
        document.getElementById('nuevaCiudadEstadoId').value = estadoId;
        document.getElementById('nuevaCiudadEstado').value = estadoNombre;
        
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
            .catch(error => {
                console.error('Error cargando ciudades:', error);
                alert('Error al cargar ciudades. Intente nuevamente.');
            });
    });
    
    
    // === GUARDAR NUEVA CIUDAD ===
    btnGuardarNuevaCiudad.addEventListener('click', function() {
        const estadoId = document.getElementById('nuevaCiudadEstadoId').value;
        const nombre = document.getElementById('nuevaCiudadNombre').value.trim();
        const poblacion = document.getElementById('nuevaCiudadPoblacion').value.trim();
        const errorDiv = document.getElementById('errorNuevaCiudad');
        const spinner = document.getElementById('spinnerGuardar');
        
        // Validar
        if (!nombre) {
            errorDiv.textContent = 'El nombre de la ciudad es requerido';
            errorDiv.style.display = 'block';
            return;
        }
        
        // Ocultar error
        errorDiv.style.display = 'none';
        
        // Mostrar spinner
        spinner.style.display = 'inline-block';
        btnGuardarNuevaCiudad.disabled = true;
        
        // Obtener CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Enviar AJAX
        fetch('/api/ciudades/crear/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
            },
            body: new URLSearchParams({
                estado_id: estadoId,
                nombre: nombre,
                poblacion: poblacion,
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                // Mostrar error
                errorDiv.textContent = data.error;
                errorDiv.style.display = 'block';
                spinner.style.display = 'none';
                btnGuardarNuevaCiudad.disabled = false;
            } else {
                // Éxito: agregar ciudad al select
                const option = document.createElement('option');
                option.value = data.id;
                option.textContent = data.nombre;
                option.selected = true;
                ciudadSelect.appendChild(option);
                
                // Cerrar modal
                $('#modalNuevaCiudad').modal('hide');
                
                // Limpiar formulario
                formNuevaCiudad.reset();
                spinner.style.display = 'none';
                btnGuardarNuevaCiudad.disabled = false;
                
                // Notificación
                alert(`✅ Ciudad "${data.nombre}" agregada exitosamente`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            errorDiv.textContent = 'Error al crear ciudad. Intente nuevamente.';
            errorDiv.style.display = 'block';
            spinner.style.display = 'none';
            btnGuardarNuevaCiudad.disabled = false;
        });
    });
    
    
    // === LIMPIAR MODAL AL CERRAR ===
    $('#modalNuevaCiudad').on('hidden.bs.modal', function() {
        formNuevaCiudad.reset();
        document.getElementById('errorNuevaCiudad').style.display = 'none';
    });
});
</script>
{% endblock %}
```

---

## 🅱️ **OPCIÓN B: AUTOCOMPLETE CON SELECT2**

### **UX Flow:**

```
1. Usuario empieza a escribir ciudad
   ↓
2. Select2 busca en BD (AJAX)
   ↓
3. Muestra resultados
   ↓
4. Si no encuentra:
   → Muestra opción "Agregar 'NOMBRE_ESCRITO'"
   ↓
5. Usuario selecciona "Agregar..."
   ↓
6. AJAX crea ciudad en BD
   ↓
7. Select2 selecciona ciudad nueva automáticamente
```

### **Ventajas:**
- ✅ UX más fluida (sin modal)
- ✅ Mobile-friendly
- ✅ Buscar + crear en un solo widget

---

### **Implementación con Select2:**

#### **1. Instalar Select2**

```bash
# Via npm
npm install select2

# O via CDN (en template)
```

#### **2. Template con Select2**

```html
<!-- templates/clientes/cliente_form.html -->

{% extends "base.html" %}

{% block extra_css %}
<!-- Select2 CSS -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<link href="https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css" rel="stylesheet" />
{% endblock %}

{% block content %}
<div class="container">
    <h2>{{ titulo }}</h2>
    
    <form method="post" id="formCliente">
        {% csrf_token %}
        
        <div class="row">
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_estado">Estado/Región</label>
                    <select 
                        id="id_estado" 
                        name="estado_selector" 
                        class="form-control"
                    >
                        <option value="">Seleccione Estado</option>
                        {% for estado in estados %}
                        <option value="{{ estado.id }}">{{ estado.nombre }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="form-group">
                    <label for="id_ciudad">Ciudad</label>
                    <select 
                        id="id_ciudad" 
                        name="ciudad_selector" 
                        class="form-control"
                    >
                        <option value="">Seleccione o escriba ciudad</option>
                    </select>
                    <small class="form-text text-muted">
                        Empiece a escribir para buscar. Si no existe, podrá agregarla.
                    </small>
                </div>
            </div>
        </div>
        
        <button type="submit" class="btn btn-primary">Guardar Cliente</button>
    </form>
</div>
{% endblock %}

{% block extra_js %}
<!-- Select2 JS -->
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

<script>
$(document).ready(function() {
    let estadoIdActual = null;
    
    // === SELECT2 PARA CIUDAD CON CREACIÓN ===
    $('#id_ciudad').select2({
        theme: 'bootstrap-5',
        placeholder: 'Seleccione o escriba ciudad',
        allowClear: true,
        minimumInputLength: 2,  // Mínimo 2 caracteres para buscar
        
        ajax: {
            url: '/api/ciudades/buscar/',
            dataType: 'json',
            delay: 250,  // Debounce
            data: function(params) {
                return {
                    q: params.term,  // Término de búsqueda
                    estado_id: estadoIdActual,
                };
            },
            processResults: function(data) {
                // Agregar opción "Crear nueva" al final
                const results = data.map(ciudad => ({
                    id: ciudad.id,
                    text: ciudad.nombre,
                }));
                
                // Si no hay resultados y usuario escribió algo
                if (results.length === 0 && $('#id_ciudad').data('select2').$dropdown) {
                    const term = $('#id_ciudad').data('select2').$container.find('.select2-search__field').val();
                    if (term && term.length >= 2) {
                        results.push({
                            id: `__crear__${term}`,
                            text: `➕ Agregar "${term}"`,
                            crear: true,
                            nombre: term,
                        });
                    }
                }
                
                return { results };
            },
        },
        
        // Personalizar texto cuando no hay resultados
        language: {
            noResults: function() {
                return "No se encontraron ciudades. Escriba para agregar una nueva.";
            },
            searching: function() {
                return "Buscando...";
            }
        },
        
        // Personalizar template
        templateResult: function(data) {
            if (data.crear) {
                return $('<span style="color: #28a745; font-weight: bold;">' + data.text + '</span>');
            }
            return data.text;
        },
    });
    
    
    // === CUANDO CAMBIA ESTADO ===
    $('#id_estado').on('change', function() {
        estadoIdActual = $(this).val();
        
        // Resetear select de ciudad
        $('#id_ciudad').val(null).trigger('change');
        
        // Habilitar/deshabilitar según estado
        $('#id_ciudad').prop('disabled', !estadoIdActual);
    });
    
    
    // === CUANDO SELECCIONA OPCIÓN "CREAR" ===
    $('#id_ciudad').on('select2:select', function(e) {
        const data = e.params.data;
        
        // Si es la opción "crear"
        if (data.id && data.id.toString().startsWith('__crear__')) {
            const nombre = data.nombre;
            
            if (!estadoIdActual) {
                alert('⚠️ Primero seleccione un estado');
                $(this).val(null).trigger('change');
                return;
            }
            
            // Confirmar
            if (!confirm(`¿Desea agregar la ciudad "${nombre}"?`)) {
                $(this).val(null).trigger('change');
                return;
            }
            
            // Crear ciudad vía AJAX
            const csrfToken = $('[name=csrfmiddlewaretoken]').val();
            
            $.ajax({
                url: '/api/ciudades/crear/',
                method: 'POST',
                data: {
                    estado_id: estadoIdActual,
                    nombre: nombre,
                    csrfmiddlewaretoken: csrfToken,
                },
                success: function(response) {
                    // Crear opción en select2 con la ciudad nueva
                    const newOption = new Option(response.nombre, response.id, true, true);
                    $('#id_ciudad').append(newOption).trigger('change');
                    
                    // Notificación
                    alert(`✅ Ciudad "${response.nombre}" agregada exitosamente`);
                },
                error: function(xhr) {
                    const error = xhr.responseJSON?.error || 'Error al crear ciudad';
                    alert('❌ ' + error);
                    $('#id_ciudad').val(null).trigger('change');
                }
            });
        }
    });
});
</script>
{% endblock %}
```

---

#### **3. Endpoint de búsqueda**

```python
# taller/clientes/views.py

from django.http import JsonResponse
from django.db.models import Q
from taller.models.ubicacion import Ciudad


def ajax_buscar_ciudades(request):
    """
    Endpoint para buscar ciudades (autocomplete).
    GET /api/ciudades/buscar/?q=sant&estado_id=123
    """
    query = request.GET.get('q', '').strip()
    estado_id = request.GET.get('estado_id')
    
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)
    
    # Filtrar ciudades
    ciudades = Ciudad.objects.filter(
        nombre__icontains=query
    )
    
    # Filtrar por estado si se especifica
    if estado_id:
        ciudades = ciudades.filter(estado_id=estado_id)
    
    # Limitar resultados
    ciudades = ciudades.order_by('nombre')[:10]
    
    # Serializar
    data = [
        {
            'id': c.id,
            'nombre': c.nombre,
            'estado_id': c.estado_id,
            'estado_nombre': c.estado.nombre,
        }
        for c in ciudades
    ]
    
    return JsonResponse(data, safe=False)


# urls.py
urlpatterns = [
    # ... otras URLs ...
    path("api/ciudades/buscar/", ajax_buscar_ciudades, name="api_buscar_ciudades"),
    path("api/ciudades/crear/", ajax_crear_ciudad, name="api_crear_ciudad"),
]
```

---

## 📊 **COMPARACIÓN DE OPCIONES**

### **Opción A: Modal**

**✅ Ventajas:**
- Simple de implementar (Vanilla JS)
- Control total sobre UX
- Funciona sin librerías externas
- Fácil agregar validaciones custom

**❌ Desventajas:**
- Requiere dos clicks (abrir modal + submit)
- Modales a veces problemáticos en mobile
- Interrumpe flujo del formulario

**📌 Recomendado para:**
- Usuarios internos (admin, staff)
- Formularios de backoffice
- Cuando necesitas agregar muchos campos (población, coordenadas, etc.)

---

### **Opción B: Select2 Autocomplete**

**✅ Ventajas:**
- UX fluida (inline, sin modal)
- Mobile-friendly
- Búsqueda + creación en un solo widget
- Aspecto profesional

**❌ Desventajas:**
- Requiere librería externa (Select2)
- Configuración más compleja
- Solo puedes pedir nombre (para más campos necesitas modal anyway)

**📌 Recomendado para:**
- Usuarios finales (clientes del sistema)
- Formularios públicos
- Cuando solo necesitas nombre (no metadata extra)

---

## 🎯 **RECOMENDACIÓN**

### **Para tu caso:**

**Usa OPCIÓN B (Select2) para clientes nuevos:**

Razones:
1. ✅ UX superior (inline, fluida)
2. ✅ Mobile-friendly
3. ✅ Para crear ciudad solo necesitas nombre
4. ✅ Select2 es estándar de facto

### **Usa OPCIÓN A (Modal) para backoffice/admin:**

Razones:
1. ✅ Puedes agregar más campos (población, coordenadas, etc.)
2. ✅ Más control sobre validaciones
3. ✅ No requiere librerías externas

---

## 💡 **MEJORA: HÍBRIDO (Lo mejor de ambos)**

Combina ambas opciones:

```html
<div class="form-group">
    <label>Ciudad</label>
    <div class="input-group">
        <!-- Select2 para búsqueda/selección -->
        <select id="id_ciudad" class="form-control"></select>
        
        <!-- Botón para modal (opciones avanzadas) -->
        <div class="input-group-append">
            <button 
                type="button" 
                class="btn btn-outline-secondary" 
                data-toggle="modal" 
                data-target="#modalCiudadAvanzado"
                title="Opciones avanzadas"
            >
                ⚙️
            </button>
        </div>
    </div>
    <small class="text-muted">
        Escriba para buscar o use ⚙️ para opciones avanzadas
    </small>
</div>
```

**Resultado:**
- Usuarios normales: usan Select2 (rápido, simple)
- Usuarios avanzados: usan modal (completo, con metadata)

---

## ✅ **CÓDIGO COMPLETO DISPONIBLE**

Ambas opciones están documentadas arriba con código completo y funcional:

1. **Opción A (Modal):** Sección 🅰️
2. **Opción B (Select2):** Sección 🅱️

Elige la que mejor se adapte a tu caso de uso y ¡implementa!

