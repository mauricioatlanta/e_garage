# 🚀 Plan de Migración: extras_vehiculo.py Multi-Tenant

## 📋 Resumen de Cambios

### Antes (Problemas)
- ❌ `ColorVehiculo.nombre` con `unique=True` global → colisiones entre CL/US
- ❌ `get_colores_para_pais()` crea registros sin `country` → basura global
- ❌ `MotorVehiculo`/`CajaVehiculo` sin scoping → mezcla entre países
- ❌ Sin validador de HEX, sin índices útiles, unicidad case-sensitive

### Ahora (Solución)
- ✅ Campo `country` con `db_index=True` en todos los modelos
- ✅ `UniqueConstraint` por `country` + `Lower(nombre)` (case-insensitive)
- ✅ Validador `RegexValidator` para códigos HEX
- ✅ Helpers: `scoped()`, `ensure_defaults_for_country()`, `get_colores_para_pais()` mejorado
- ✅ Preparado para agregar FK `empresa` (comentado, listo para activar)

---

## 🔧 Paso 1: Crear Migración

```bash
python manage.py makemigrations taller --name add_country_to_extras_vehiculo
```

### Campos a agregar:
1. `ColorVehiculo.country` (CharField, default="CL", db_index=True)
2. `MotorVehiculo.country` (CharField, default="CL", db_index=True)
3. `CajaVehiculo.country` (CharField, default="CL", db_index=True)

### Constraints a modificar:
1. **Quitar**: `unique=True` de `ColorVehiculo.nombre`
2. **Agregar**: `UniqueConstraint(Lower("nombre"), "country", name="uniq_color_country_lowernombre")`
3. **Agregar**: `UniqueConstraint(Lower("nombre"), "country", name="uniq_motor_country_lowernombre")`
4. **Agregar**: `UniqueConstraint(Lower("nombre"), "country", name="uniq_caja_country_lowernombre")`

---

## 🗃️ Paso 2: Data Migration (Asignar `country` a registros existentes)

```bash
python manage.py makemigrations taller --name assign_country_to_existing_extras --empty
```

### Script de Data Migration:

```python
# taller/migrations/XXXX_assign_country_to_existing_extras.py

from django.db import migrations

def assign_country_to_extras(apps, schema_editor):
    ColorVehiculo = apps.get_model('taller', 'ColorVehiculo')
    MotorVehiculo = apps.get_model('taller', 'MotorVehiculo')
    CajaVehiculo = apps.get_model('taller', 'CajaVehiculo')

    # Colores en inglés → US, resto → CL
    colores_us = [
        "White", "Black", "Red", "Blue", "Green", "Yellow",
        "Gray", "Silver", "Gold", "Brown", "Purple", "Orange"
    ]

    ColorVehiculo.objects.filter(nombre__in=colores_us).update(country="US")
    ColorVehiculo.objects.exclude(nombre__in=colores_us).update(country="CL")

    # Si tienes lógica para detectar motores/cajas US vs CL, aplícala aquí
    # Por defecto, todos a CL (ajusta según tu caso)
    MotorVehiculo.objects.all().update(country="CL")
    CajaVehiculo.objects.all().update(country="CL")

    print(f"✅ Asignado country a {ColorVehiculo.objects.count()} colores")
    print(f"✅ Asignado country a {MotorVehiculo.objects.count()} motores")
    print(f"✅ Asignado country a {CajaVehiculo.objects.count()} cajas")

def reverse_assign(apps, schema_editor):
    # Rollback: country vuelve a NULL (si aplica)
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('taller', 'XXXX_add_country_to_extras_vehiculo'),
    ]

    operations = [
        migrations.RunPython(assign_country_to_extras, reverse_assign),
    ]
```

---

## 🔍 Paso 3: Verificar Datos Incoherentes

Antes de aplicar constraints, verifica duplicados:

```python
# Script: verificar_duplicados_extras.py

from django.db.models import Count
from django.db.models.functions import Lower
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo

# Duplicados de colores por país (case-insensitive)
duplicados_color = (
    ColorVehiculo.objects
    .values('country')
    .annotate(lower_nombre=Lower('nombre'))
    .values('country', 'lower_nombre')
    .annotate(count=Count('id'))
    .filter(count__gt=1)
)

if duplicados_color:
    print("⚠️ Duplicados en ColorVehiculo:")
    for dup in duplicados_color:
        print(f"  {dup['country']}: {dup['lower_nombre']} ({dup['count']} veces)")
        # Resuelve manualmente: elimina o fusiona
else:
    print("✅ No hay duplicados en ColorVehiculo")

# Similar para MotorVehiculo y CajaVehiculo
```

**Solución de duplicados:**
- Fusiona registros duplicados (actualiza FKs en `Vehiculo` para apuntar al que mantienes)
- Elimina los duplicados

---

## 🛡️ Paso 4: Aplicar Migración y Constraints

```bash
python manage.py migrate taller
```

Esto:
1. Agrega campos `country`
2. Asigna valores default a registros existentes
3. Aplica `UniqueConstraint` (fallará si hay duplicados no resueltos)

---

## 🔗 Paso 5: Actualizar Stack Completo

### 5.1. Forms (`vehiculos/forms.py`)

Ya está corregido en los cambios anteriores:

```python
def _configurar_color(self, pais):
    empresa = getattr(self.user, "empresa", None)
    # ✅ Ahora usa get_colores_para_pais() que devuelve scoped
    colores = ColorVehiculo.get_colores_para_pais(pais, empresa)
    # ...
```

En `save()`:

```python
if getattr(self, "_color_nuevo", False) and request.POST.get("color_nuevo"):
    kwargs = {"nombre": request.POST["color_nuevo"], "country": pais}
    # if empresa: kwargs["empresa"] = empresa
    ColorVehiculo.objects.get_or_create(**kwargs)
```

### 5.2. AJAX Views (`ajax_views.py`)

Ya actualizado para filtrar por `country`:

```python
@login_required
@require_http_methods(["GET"])
def ajax_motores(request):
    empresa, pais = _scope(request)
    modelo = Modelo.objects.get(pk=modelo_id, country=pais)

    qs = MotorVehiculo.objects.filter(modelos=modelo, country=pais)
    # Si MotorVehiculo tiene empresa:
    # if hasattr(MotorVehiculo, "empresa") and empresa:
    #     qs = qs.filter(empresa=empresa)
```

### 5.3. Admin (`admin.py`)

Agrega filtros por `country`:

```python
# taller/admin.py

@admin.register(ColorVehiculo)
class ColorVehiculoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'country', 'hex']
    list_filter = ['country']
    search_fields = ['nombre']

@admin.register(MotorVehiculo)
class MotorVehiculoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'country']
    list_filter = ['country']
    search_fields = ['nombre']
    filter_horizontal = ['modelos']

@admin.register(CajaVehiculo)
class CajaVehiculoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'country']
    list_filter = ['country']
    search_fields = ['nombre']
    filter_horizontal = ['modelos']
```

---

## 🧪 Paso 6: Smoke Tests

### Test 1: Colores por País
```python
from taller.models.extras_vehiculo import ColorVehiculo

# CL debe tener colores en español
colores_cl = ColorVehiculo.get_colores_para_pais("CL")
assert "Blanco" in [c.nombre for c in colores_cl]
assert "White" not in [c.nombre for c in colores_cl]

# US debe tener colores en inglés
colores_us = ColorVehiculo.get_colores_para_pais("US")
assert "White" in [c.nombre for c in colores_us]
assert "Blanco" not in [c.nombre for c in colores_us]
```

### Test 2: Unicidad Case-Insensitive
```python
# Crear "Rojo" en CL
ColorVehiculo.objects.create(nombre="Rojo", country="CL")

# Intentar crear "rojo" (minúsculas) → debe fallar
try:
    ColorVehiculo.objects.create(nombre="rojo", country="CL")
    assert False, "Debería haber fallado por constraint"
except Exception as e:
    print(f"✅ Constraint funcionó: {e}")
```

### Test 3: Scoping por País
```python
# Crear motor en CL y US con mismo nombre
motor_cl = MotorVehiculo.objects.create(nombre="V8 5.0L", country="CL")
motor_us = MotorVehiculo.objects.create(nombre="V8 5.0L", country="US")

# Ambos deben existir sin conflicto
assert MotorVehiculo.objects.filter(nombre="V8 5.0L").count() == 2
assert MotorVehiculo.scoped("CL").filter(nombre="V8 5.0L").count() == 1
assert MotorVehiculo.scoped("US").filter(nombre="V8 5.0L").count() == 1
```

### Test 4: Validador HEX
```python
# Válidos
ColorVehiculo.objects.create(nombre="Rojo Custom", country="CL", hex="#FF0000")
ColorVehiculo.objects.create(nombre="Azul Custom", country="CL", hex="#00F")

# Inválido
try:
    ColorVehiculo.objects.create(nombre="Verde Custom", country="CL", hex="FF0000")  # Sin #
    assert False, "Debería fallar validación HEX"
except Exception:
    print("✅ Validador HEX funcionó")
```

---

## 🚀 Paso 7: Migración a Multi-Tenant Completo (Opcional)

Cuando tengas FK `Empresa` lista:

1. **Agregar campo `empresa`**:
   ```python
   empresa = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.CASCADE)
   ```

2. **Data Migration**:
   - Asigna colores/motores/cajas a empresas según lógica de negocio
   - Backfill basado en modelos asociados o vehículos existentes

3. **Actualizar Constraints**:
   ```python
   models.UniqueConstraint(
       Lower("nombre"), "country", "empresa",
       name="uniq_color_empresa_country_lowernombre",
   )
   ```

4. **Actualizar Forms/Views**:
   - Descomenta filtros por `empresa` en `forms.py`, `ajax_views.py`

---

## 📊 Comparación Antes/Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Unicidad** | Global (nombre único en todo el sistema) | Por país + nombre (case-insensitive) |
| **Scoping** | Sin filtrado automático | `scoped(country, empresa)` |
| **Validación HEX** | Ninguna | `RegexValidator` |
| **Índices** | Solo en `nombre` | `(country, nombre)` compuesto |
| **Multi-tenant** | ❌ Mezcla datos entre países | ✅ Aislamiento por país |
| **Seed** | Crea global sin control | `ensure_defaults_for_country()` controlado |
| **M2M Coherencia** | No valida país/empresa | Preparado para validar en through models |

---

## ⚠️ Rollback Plan

Si necesitas revertir:

```bash
# Paso 1: Rollback migraciones
python manage.py migrate taller XXXX_previous_migration

# Paso 2: Restaurar código anterior
git checkout HEAD~1 -- taller/models/extras_vehiculo.py

# Paso 3: Verificar integridad
python manage.py check
```

---

## 📝 Checklist de Implementación

- [ ] Crear migración `add_country_to_extras_vehiculo`
- [ ] Crear data migration `assign_country_to_existing_extras`
- [ ] Ejecutar script de verificación de duplicados
- [ ] Resolver duplicados manualmente
- [ ] Aplicar migraciones: `python manage.py migrate`
- [ ] Actualizar admin.py con filtros por `country`
- [ ] Ejecutar smoke tests
- [ ] Probar creación de vehículo en CL y US
- [ ] Verificar que color "Rojo"/"rojo" no se duplica
- [ ] Verificar que "Blanco" (CL) y "White" (US) coexisten
- [ ] Revisar logs de errores en producción

---

## 🎯 Resultado Final

Con este parche:

✅ **CL y US tienen catálogos separados** sin colisiones
✅ **Unicidad case-insensitive** evita "Rojo"/"rojo"
✅ **Scoping automático** en forms/endpoints
✅ **Seed controlado** sin basura global
✅ **Preparado para empresa** cuando migres a multi-tenant completo
✅ **Stack 100% consistente** con forms.py, ajax_views.py, JS

---

**Siguiente paso recomendado**: Ejecutar migración en ambiente de desarrollo y probar el flujo completo de creación/edición de vehículos en ambos países.
