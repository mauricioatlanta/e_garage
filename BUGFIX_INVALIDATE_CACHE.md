🔧 **BUG FIX: invalidate_company_cache**

## ❌ **Problema Detectado:**
```
AttributeError: 'int' object has no attribute 'id'
```

**Ubicación:** `taller/context_processors/__init__.py` línea 151
**Causa:** La función `invalidate_company_cache(user)` esperaba un objeto User pero recibía `request.user.id` (int)

## ✅ **Solución Implementada:**

### Antes:
```python
def invalidate_company_cache(user):
    """Invalida el caché de branding para un usuario específico."""
    cache_key = f"company_branding_{user.id}"  # ❌ Error aquí
    cache.delete(cache_key)
```

### Después:
```python
def invalidate_company_cache(user):
    """Invalida el caché de branding para un usuario específico.
    
    Args:
        user: Puede ser un objeto User o un ID de usuario (int)
    """
    if hasattr(user, 'id'):
        user_id = user.id
    else:
        user_id = user  # Es un ID directamente
        
    cache_key = f"company_branding_{user_id}"
    cache.delete(cache_key)
```

## 🧪 **Pruebas Realizadas:**
✅ Funciona con objeto User: `invalidate_company_cache(user)`
✅ Funciona con ID: `invalidate_company_cache(user.id)` 
✅ Compatible con llamada existente en `company_settings_views.py`

## 📍 **Ubicaciones de Uso:**
- `taller/views_extra/company_settings_views.py:57` ✅ Corregido
- Cualquier otro lugar que llame la función ✅ Compatible

**Estado:** ✅ BUG RESUELTO - La carga de logos ahora funciona sin errores
