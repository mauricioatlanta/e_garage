# Reorganización de Templates - Estructura Estandarizada

## Resumen

Se ha reorganizado completamente la estructura de templates para estandarizar la organización por país e idioma, con una capa común para templates compartidos.

## Cambios Implementados

### 1. Estructura de Carpetas Estandarizada

Todos los países ahora tienen la misma estructura de carpetas base:

```
templates/
├── <country>/<lang>/
│   ├── account/
│   ├── clientes/
│   ├── vehiculos/
│   ├── servicios/
│   ├── onboarding/
│   └── otros_servicios/
├── common/
│   ├── account/
│   ├── clientes/
│   ├── vehiculos/
│   ├── servicios/
│   ├── onboarding/
│   └── otros_servicios/
```

**Países soportados:** `cl`, `us`, `mx`, `pe`, `co`, `ec`, `ve`, `br`
**Idiomas soportados:** `es`, `en`

### 2. Helper Centralizado de Resolución

Nuevo helper en `taller/utils/templates.py`:

#### `normalize_country_code(country: str) -> str`
Normaliza códigos de país a formato estándar:
- `USA`, `US`, `UNITED STATES` → `us`
- `CL`, `CHILE` → `cl`
- `MX`, `MEX`, `MEXICO` → `mx`
- Y así para todos los países...

#### `resolve_template_path(template_path, country, lang) -> str`
Resuelve templates usando la jerarquía:
1. `<country>/<lang>/<template_path>` (específico por país/idioma)
2. `common/<template_path>` (template compartido)

**Ejemplo:**
```python
from taller.utils.templates import resolve_template_path

# Busca: us/en/clientes/crear_cliente.html
# Si no existe: common/clientes/crear_cliente.html
template = resolve_template_path("clientes/crear_cliente.html", "US", "en")
```

### 3. Actualización del Mixin

`CountryLangTemplateMixin` ahora:
- Usa `normalize_country_code()` para normalizar códigos
- Usa `resolve_template_path()` para resolver templates
- Soporta todos los países: cl, us, mx, pe, co, ec, ve, br
- Detecta país desde URL path, empresa, o request.country

### 4. Copia de Templates de Referencia

Se copiaron todos los templates de `cl/es` a los demás países/idiomas:
- Archivos que ya existían se mantuvieron (no se sobrescribieron)
- Archivos faltantes se copiaron desde la referencia

## Uso

### En Vistas (Class-Based Views)

```python
from taller.mixins import CountryLangTemplateMixin
from django.views.generic import TemplateView

class CrearClienteView(CountryLangTemplateMixin, TemplateView):
    base_template_name = "clientes/crear_cliente.html"
    # El mixin resuelve automáticamente el template correcto
```

### En Vistas (Function-Based Views)

```python
from taller.utils.templates import resolve_template_path
from django.template.response import TemplateResponse

def crear_cliente(request):
    # Obtener país e idioma
    country = getattr(request.user.empresa, 'pais', 'cl') if request.user.is_authenticated else 'cl'
    lang = get_language() or 'es'
    
    # Resolver template
    template_name = resolve_template_path("clientes/crear_cliente.html", country, lang)
    
    return TemplateResponse(request, template_name, context)
```

### Normalización de Códigos de País

```python
from taller.utils.templates import normalize_country_code

# Todos estos retornan "us"
normalize_country_code("USA")
normalize_country_code("US")
normalize_country_code("United States")

# Todos estos retornan "cl"
normalize_country_code("CL")
normalize_country_code("Chile")
```

## Estructura de Archivos

### Archivos de Referencia (cl/es)

Los siguientes archivos existen en `templates/cl/es/` y deben existir (con el mismo nombre) en los demás países:

**account/**
- `login.html`
- `signup.html`

**clientes/**
- `_tabla_clientes.html`
- `cliente_form.html`
- `cliente_list.html`
- `confirmar_eliminacion.html`
- `crear_cliente.html`
- `debug_cliente.html`
- `editar_cliente.html`
- `eliminar_confirmar.html`
- `lista_clientes.html`
- `ver_cliente.html`

**vehiculos/**
- `crear.html`
- `crear_vehiculo.html`
- `detalle_vehiculo.html`
- `editar_vehiculo.html`
- `lista_vehiculos.html`

**servicios/**
- `servicios_menu.html`

**onboarding/**
- `bienvenida.html`

## Migración de Código Existente

### Antes (hardcoded)
```python
return render(request, "taller/cl/es/clientes/crear_cliente.html", context)
```

### Después (usando helper)
```python
from taller.utils.templates import resolve_template_path
template_name = resolve_template_path("clientes/crear_cliente.html", country, lang)
return TemplateResponse(request, template_name, context)
```

## Notas Importantes

1. **No usar "USA" en rutas**: Siempre usar `us` (normalizado)
2. **Códigos en minúsculas**: Todos los códigos de país se normalizan a minúsculas
3. **Fallback automático**: Si no existe template específico, se usa `common/`
4. **Compatibilidad**: La función `select_country_lang_template()` se mantiene por compatibilidad pero está marcada como DEPRECATED

## Próximos Pasos (Opcional)

1. Migrar vistas que aún usan paths hardcodeados a usar `resolve_template_path()`
2. Mover templates compartidos a `templates/common/` cuando no haya diferencias por país
3. Actualizar documentación de desarrollo con ejemplos de uso






