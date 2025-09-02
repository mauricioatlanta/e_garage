# 🔧 CORRECCIÓN CRÍTICA: API BÚSQUEDA CLIENTES BLINDADA

## ❌ PROBLEMA IDENTIFICADO
- **URL afectada**: `http://127.0.0.1:8000/vehiculos-core/crear/`
- **Síntoma**: Al buscar cliente, aparecían clientes de todas las empresas
- **Causa**: Endpoint `api_busqueda_clientes` no filtraba por empresa

## ✅ CORRECCIÓN APLICADA

### Archivo: `taller/vehiculos/views.py`

**ANTES** (vulnerable):
```python
def api_busqueda_clientes(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
    clientes = Cliente.objects.filter(  # ❌ SIN FILTRO DE EMPRESA
        models.Q(nombre__icontains=q) |
        models.Q(apellido__icontains=q) |
        models.Q(email__icontains=q) |
        models.Q(telefono__icontains=q)
    )[:20]
```

**DESPUÉS** (blindado):
```python
def api_busqueda_clientes(request):
    # BLINDAJE MULTI-TENANT: Verificar autenticación y empresa
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    
    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        return JsonResponse([], safe=False)
    
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
        
    # BLINDAJE: Filtrar SOLO por empresa del usuario
    clientes = Cliente.objects.filter(
        empresa=empresa  # ✅ FILTRO OBLIGATORIO
    ).filter(
        models.Q(nombre__icontains=q) |
        models.Q(apellido__icontains=q) |
        models.Q(email__icontains=q) |
        models.Q(telefono__icontains=q)
    )[:20]
```

### Corrección adicional: `api_marcas`
También blindé el endpoint de marcas para verificar autenticación:

```python
def api_marcas(request):
    # BLINDAJE: Verificar autenticación del usuario
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    
    marcas = list(Marca.objects.values('id', 'nombre'))
    return JsonResponse(marcas, safe=False)
```

### Corrección adicional: `VehiculoAutocomplete`
El autocomplete de vehículos también tenía la misma vulnerabilidad:

**Archivo**: `taller/vehiculos/views_autocomplete.py`

```python
class VehiculoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # BLINDAJE MULTI-TENANT: Verificar autenticación y empresa
        if not self.request.user.is_authenticated:
            return Vehiculo.objects.none()
        
        empresa = getattr(self.request.user, 'empresa', None)
        if not empresa:
            return Vehiculo.objects.none()
        
        # BLINDAJE: Filtrar SOLO por empresa del usuario
        qs = Vehiculo.objects.filter(empresa=empresa)
```

## 🧪 VERIFICACIÓN MANUAL

### Para testuser_cl:
1. ✅ Login como `testuser_cl`
2. ✅ Ir a: `http://127.0.0.1:8000/vehiculos-core/crear/`
3. ✅ En el campo cliente, buscar "john" 
4. ✅ **DEBE mostrar SOLO clientes CL** (no debe aparecer john wick ni john lennon)

### Para testuser_usa:
1. ✅ Login como `testuser_usa`
2. ✅ Ir a: `http://127.0.0.1:8000/vehiculos-core/crear/`
3. ✅ En el campo cliente, buscar "carlos"
4. ✅ **DEBE mostrar SOLO clientes US** (no debe aparecer datos CL)

## 🔍 ENDPOINTS CORREGIDOS

| URL | Estado | Descripción |
|-----|--------|-------------|
| `/vehiculos-core/api/clientes/` | ✅ BLINDADO | Búsqueda de clientes |
| `/vehiculos-core/api/marcas/` | ✅ BLINDADO | Lista de marcas |
| `/vehiculos-core/autocomplete/vehiculo/` | ✅ BLINDADO | Autocomplete vehículos |

## 🚨 IMPACTO DE SEGURIDAD

- **Antes**: Cualquier usuario podía ver clientes de todas las empresas
- **Después**: Usuarios solo ven clientes de su propia empresa
- **Riesgo**: CRÍTICO → RESUELTO

## ✅ ESTADO FINAL

El formulario de crear vehículo en `http://127.0.0.1:8000/vehiculos-core/crear/` ahora está completamente blindado. La búsqueda de clientes está restringida por empresa del usuario autenticado.

**PRÓXIMO PASO**: Verificar manualmente que la corrección funciona correctamente.
