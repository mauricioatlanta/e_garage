# 🔒 Ajustes de Seguridad para views_fbv.py

## 📋 Problemas Detectados

### 1. Decoradores Faltantes
Varias vistas verifican autenticación manualmente en vez de usar `@login_required`:
- `api_marcas` (línea 233)
- `api_colores` (línea 273)
- `api_modelos_usa` (línea 284)
- `ajax_agregar_marca` (línea 386)
- `ajax_agregar_modelo` (línea 411)

### 2. Formato de Respuesta Inconsistente
Algunas vistas devuelven arrays pelados `[]` en vez del formato estandarizado:
- `ajax_motores_por_modelo` (línea 354) → devuelve `[{id, nombre}]` ❌
- `ajax_cajas_por_modelo` (línea 371) → devuelve `[{id, nombre}]` ❌

**Debería ser:** `{"success": true, "motores": [{id, nombre}]}`

### 3. Scoping de Motor/Caja
Al crear motores/cajas nuevos, no se asigna `country`:
- `ajax_agregar_motor` (línea 462): `MotorVehiculo.objects.get_or_create(nombre=nombre)` ❌
- `ajax_agregar_caja` (línea 498): `CajaVehiculo.objects.get_or_create(nombre=nombre)` ❌

---

## 🛠️ Parches Quirúrgicos (Copy-Paste)

### Parche 1: `api_marcas` con decorador

**Antes (líneas 232-241):**
```python
@require_GET
def api_marcas(request):
    """Marcas por país del usuario. Requiere auth."""
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    country = _get_country(request)
    data = list(
        Marca.objects.filter(country=country).order_by("nombre").values("id", "nombre")
    )
    return JsonResponse(data, safe=False)
```

**Después:**
```python
@require_GET
@login_required
def api_marcas(request):
    """Marcas por país del usuario."""
    country = _get_country(request)
    empresa = getattr(request.user, "empresa", None)
    
    qs = Marca.objects.filter(country=country)
    # Si Marca tiene FK empresa, descomenta:
    # if hasattr(Marca, "empresa") and empresa:
    #     qs = qs.filter(empresa=empresa)
    
    data = list(qs.order_by("nombre").values("id", "nombre"))
    return JsonResponse(data, safe=False)
```

---

### Parche 2: `api_colores` con decorador

**Antes (líneas 273-281):**
```python
@require_GET
def api_colores(request):
    """Colores disponibles."""
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    country = _get_country(request)
    colores = ColorVehiculo.get_colores_para_pais(country)
    data = [{"id": c.pk, "nombre": c.nombre} for c in colores]
    return JsonResponse(data, safe=False)
```

**Después:**
```python
@require_GET
@login_required
def api_colores(request):
    """Colores disponibles para el país del usuario."""
    country = _get_country(request)
    empresa = getattr(request.user, "empresa", None)
    colores = ColorVehiculo.get_colores_para_pais(country, empresa)
    data = [{"id": c.pk, "nombre": c.nombre} for c in colores]
    return JsonResponse(data, safe=False)
```

---

### Parche 3: `api_modelos_usa` con decorador

**Antes (líneas 284-303):**
```python
@require_GET
def api_modelos_usa(request):
    """Modelos para USA desde catálogo."""
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    # ...
```

**Después:**
```python
@require_GET
@login_required
def api_modelos_usa(request):
    """Modelos para USA desde catálogo."""
    marca_param = request.GET.get("marca", "").strip()
    if not marca_param:
        return JsonResponse([], safe=False)
    # ... resto igual
```

---

### Parche 4: `ajax_motores_por_modelo` formato estandarizado

**Antes (líneas 352-366):**
```python
@require_GET
@login_required
def ajax_motores_por_modelo(request):
    """Motores filtrados por modelo."""
    modelo_id = request.GET.get("modelo_id")
    if not modelo_id:
        return JsonResponse([], safe=False)
    
    try:
        motores = MotorVehiculo.objects.filter(modelos__id=modelo_id).order_by("nombre")
        data = [{"id": m.pk, "nombre": m.nombre} for m in motores]
        return JsonResponse(data, safe=False)
    except Exception as e:
        log.error(f"Error en ajax_motores_por_modelo: {e}")
        return JsonResponse([], safe=False)
```

**Después:**
```python
@require_GET
@login_required
def ajax_motores_por_modelo(request):
    """Motores filtrados por modelo."""
    modelo_id = request.GET.get("modelo_id")
    if not modelo_id:
        return JsonResponse({"success": True, "motores": []})
    
    try:
        country = _get_country(request)
        
        # Validar que modelo existe y pertenece al país
        try:
            modelo = Modelo.objects.get(pk=modelo_id, country=country)
        except Modelo.DoesNotExist:
            return JsonResponse({"success": True, "motores": []})
        
        motores = MotorVehiculo.objects.filter(modelos=modelo).order_by("nombre")
        
        # Si MotorVehiculo tiene country, filtrar también
        # if hasattr(MotorVehiculo, "country"):
        #     motores = motores.filter(country=country)
        
        data = [{"id": str(m.pk), "nombre": m.nombre} for m in motores]
        return JsonResponse({"success": True, "motores": data})
    except Exception as e:
        log.error(f"Error en ajax_motores_por_modelo: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
```

---

### Parche 5: `ajax_cajas_por_modelo` formato estandarizado

**Antes (líneas 369-383):**
```python
@require_GET
@login_required
def ajax_cajas_por_modelo(request):
    """Cajas filtradas por modelo."""
    modelo_id = request.GET.get("modelo_id")
    if not modelo_id:
        return JsonResponse([], safe=False)
    
    try:
        cajas = CajaVehiculo.objects.filter(modelos__id=modelo_id).order_by("nombre")
        data = [{"id": c.pk, "nombre": c.nombre} for c in cajas]
        return JsonResponse(data, safe=False)
    except Exception as e:
        log.error(f"Error en ajax_cajas_por_modelo: {e}")
        return JsonResponse([], safe=False)
```

**Después:**
```python
@require_GET
@login_required
def ajax_cajas_por_modelo(request):
    """Cajas filtradas por modelo."""
    modelo_id = request.GET.get("modelo_id")
    if not modelo_id:
        return JsonResponse({"success": True, "cajas": []})
    
    try:
        country = _get_country(request)
        
        # Validar que modelo existe y pertenece al país
        try:
            modelo = Modelo.objects.get(pk=modelo_id, country=country)
        except Modelo.DoesNotExist:
            return JsonResponse({"success": True, "cajas": []})
        
        cajas = CajaVehiculo.objects.filter(modelos=modelo).order_by("nombre")
        
        # Si CajaVehiculo tiene country, filtrar también
        # if hasattr(CajaVehiculo, "country"):
        #     cajas = cajas.filter(country=country)
        
        data = [{"id": str(c.pk), "nombre": c.nombre} for c in cajas]
        return JsonResponse({"success": True, "cajas": data})
    except Exception as e:
        log.error(f"Error en ajax_cajas_por_modelo: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
```

---

### Parche 6: `ajax_agregar_marca` con decorador

**Antes (líneas 386-408):**
```python
@require_POST
def ajax_agregar_marca(request):
    """Agregar nueva marca via AJAX."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "No autenticado"})
    # ...
```

**Después:**
```python
@require_POST
@login_required
def ajax_agregar_marca(request):
    """Agregar nueva marca via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)
        
        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)
        
        kwargs = {"nombre": nombre, "country": country}
        # Si Marca tiene empresa:
        # if hasattr(Marca, "empresa") and empresa:
        #     kwargs["empresa"] = empresa
        
        marca, created = Marca.objects.get_or_create(**kwargs)
        
        return JsonResponse({
            "success": True,
            "marca": {"id": str(marca.pk), "nombre": marca.nombre},
            "created": created
        })
    except Exception as e:
        log.error(f"Error agregando marca: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
```

---

### Parche 7: `ajax_agregar_modelo` con decorador

**Antes (líneas 411-436):**
```python
@require_POST
def ajax_agregar_modelo(request):
    """Agregar nuevo modelo via AJAX."""
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "No autenticado"})
    # ...
```

**Después:**
```python
@require_POST
@login_required
def ajax_agregar_modelo(request):
    """Agregar nuevo modelo via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        marca_id = data.get("marca_id")
        
        if not nombre or not marca_id:
            return JsonResponse({"success": False, "error": "Nombre y marca requeridos"}, status=400)
        
        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)
        
        # Validar que marca pertenece al país
        marca = get_object_or_404(Marca, id=marca_id, country=country)
        
        kwargs = {"nombre": nombre, "marca": marca, "country": country}
        # Si Modelo tiene empresa:
        # if hasattr(Modelo, "empresa") and empresa:
        #     kwargs["empresa"] = empresa
        
        modelo, created = Modelo.objects.get_or_create(**kwargs)
        
        return JsonResponse({
            "success": True,
            "modelo": {"id": str(modelo.pk), "nombre": modelo.nombre},
            "created": created
        })
    except Exception as e:
        log.error(f"Error agregando modelo: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
```

---

### Parche 8: `ajax_agregar_motor` con scoping por país

**Antes (líneas 439-472):**
```python
@require_POST
@login_required
def ajax_agregar_motor(request):
    # ... validaciones ...
    
    motor, created = MotorVehiculo.objects.get_or_create(nombre=nombre)  # ❌ Sin country
    motor.modelos.add(modelo)
```

**Después:**
```python
@require_POST
@login_required
def ajax_agregar_motor(request):
    """Agregar nuevo motor via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        modelo_id = data.get("modelo_id")
        
        if not nombre or not modelo_id:
            return JsonResponse({"success": False, "error": "Nombre y modelo requeridos"}, status=400)
        
        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)
        
        # Validar que modelo pertenece al país
        modelo = get_object_or_404(Modelo, id=modelo_id, country=country)
        
        # Crear motor con country (y empresa si aplica)
        kwargs = {"nombre": nombre, "country": country}
        # if hasattr(MotorVehiculo, "empresa") and empresa:
        #     kwargs["empresa"] = empresa
        
        motor, created = MotorVehiculo.objects.get_or_create(**kwargs)
        motor.modelos.add(modelo)
        
        return JsonResponse({
            "success": True,
            "motor": {"id": str(motor.pk), "nombre": motor.nombre},
            "created": created
        })
    except Exception as e:
        log.error(f"Error agregando motor: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
```

---

### Parche 9: `ajax_agregar_caja` con scoping por país

**Antes (líneas 475-508):**
```python
@require_POST
@login_required
def ajax_agregar_caja(request):
    # ... validaciones ...
    
    caja, created = CajaVehiculo.objects.get_or_create(nombre=nombre)  # ❌ Sin country
    caja.modelos.add(modelo)
```

**Después:**
```python
@require_POST
@login_required
def ajax_agregar_caja(request):
    """Agregar nueva caja via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        modelo_id = data.get("modelo_id")
        
        if not nombre or not modelo_id:
            return JsonResponse({"success": False, "error": "Nombre y modelo requeridos"}, status=400)
        
        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)
        
        # Validar que modelo pertenece al país
        modelo = get_object_or_404(Modelo, id=modelo_id, country=country)
        
        # Crear caja con country (y empresa si aplica)
        kwargs = {"nombre": nombre, "country": country}
        # if hasattr(CajaVehiculo, "empresa") and empresa:
        #     kwargs["empresa"] = empresa
        
        caja, created = CajaVehiculo.objects.get_or_create(**kwargs)
        caja.modelos.add(modelo)
        
        return JsonResponse({
            "success": True,
            "caja": {"id": str(caja.pk), "nombre": caja.nombre},
            "created": created
        })
    except Exception as e:
        log.error(f"Error agregando caja: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
```

---

## ✅ Checklist de Implementación

- [ ] Aplicar Parche 1: `api_marcas` con `@login_required`
- [ ] Aplicar Parche 2: `api_colores` con `@login_required`
- [ ] Aplicar Parche 3: `api_modelos_usa` con `@login_required`
- [ ] Aplicar Parche 4: `ajax_motores_por_modelo` formato `{success, motores}`
- [ ] Aplicar Parche 5: `ajax_cajas_por_modelo` formato `{success, cajas}`
- [ ] Aplicar Parche 6: `ajax_agregar_marca` con `@login_required` y scoping
- [ ] Aplicar Parche 7: `ajax_agregar_modelo` con `@login_required` y scoping
- [ ] Aplicar Parche 8: `ajax_agregar_motor` con `country` en get_or_create
- [ ] Aplicar Parche 9: `ajax_agregar_caja` con `country` en get_or_create
- [ ] Verificar imports: `from django.contrib.auth.decorators import login_required`
- [ ] Probar endpoints con pytest (ver `urls.py` para ejemplos)
- [ ] Ejecutar smoke tests multi-tenant

---

## 🧪 Testing Rápido

```bash
# 1. Verificar decoradores
python manage.py shell
>>> from taller.vehiculos import views_fbv
>>> views_fbv.api_marcas.__wrapped__.__name__
'login_required'  # ✅ Debe estar decorado

# 2. Test manual de respuesta
curl -X GET "http://localhost:8000/cl/es/vehiculos/ajax/motores-por-modelo/?modelo_id=1" \
  -H "Cookie: sessionid=..." \
  | jq '.success'
# Debe devolver: true

# 3. Test multi-tenant
# Usuario A (CL) crea motor "V8 5.0L"
# Usuario B (US) crea motor "V8 5.0L"
# Deben coexistir sin conflicto (country diferente)
```

---

## 🚀 Usando api_helpers.py (Opcional, Refactor Futuro)

Si quieres modernizar el código gradualmente:

```python
# Reemplazar helpers manuales
from taller.vehiculos.api_helpers import (
    ok, bad,  # Respuestas estandarizadas
    ajax_get, ajax_post,  # Decoradores combinados
    get_user_scope,  # Scoping multi-tenant
    parse_int,  # Validación de parámetros
)

@ajax_get  # ✅ Equivale a @login_required + @require_GET
def ajax_motores_por_modelo(request):
    modelo_id = request.GET.get("modelo_id")
    if not modelo_id:
        return ok(motores=[])
    
    try:
        modelo_id = parse_int(modelo_id, "modelo_id")
    except ValueError as e:
        return bad(str(e))
    
    empresa, pais = get_user_scope(request)
    # ... resto del código
    return ok(motores=[...])
```

---

## 📊 Impacto de los Cambios

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Seguridad** | Checks manuales dispersos | `@login_required` en todos |
| **Formato** | Arrays pelados `[]` | `{success, data}` consistente |
| **Multi-tenant** | Solo por country | country + empresa (opcional) |
| **Scoping motor/caja** | Global (sin country) | Con country en get_or_create |
| **Validación** | Manual en cada vista | Helpers reutilizables |
| **Mantenibilidad** | Código duplicado | Centralizado en helpers |

**Siguiente paso**: Aplicar parches uno por uno y probar cada endpoint con curl o pytest.



