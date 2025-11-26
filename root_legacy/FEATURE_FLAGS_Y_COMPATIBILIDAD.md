# 🚩 Feature Flags y Compatibilidad - Sistema Multi-País

## 🎯 **OBJETIVO**

Implementar rollout gradual del nuevo sistema Address v2 sin romper funcionalidad existente, manteniendo compatibilidad hacia atrás por 1 release.

---

## 📋 **ESTRATEGIA DE MIGRACIÓN**

### **Fase 1: Feature Flag (ACTUAL)** ⭐
- Agregar flag `use_address_v2` en ConfiguracionEmpresa
- Mantener views por país (BR/VE/PE) que redirigen a API unificada
- Views legacy funcionan pero logguean deprecation warnings
- Empresas pueden optar por Address v2 gradualmente

### **Fase 2: Migración Gradual (1-3 meses)**
- Nuevas empresas usan Address v2 por defecto
- Empresas existentes pueden activar manualmente
- Script de backfill disponible para migración automática
- Dashboards/KPIs sin cambios (usan fecha_emision)

### **Fase 3: Deprecación (Release +1)**
- Remover views legacy por país
- Todos los clientes nuevos en Address v2
- Mantener campos legacy solo para lectura

### **Fase 4: Cleanup (Release +2)**
- Remover campos legacy completamente
- Migración final obligatoria
- Solo Address v2

---

## 🚩 **FEATURE FLAG: use_address_v2**

### **Ubicación:**
`ConfiguracionEmpresa.use_address_v2`

### **Default:**
`False` (usar campos legacy)

### **Propósito:**
Controlar si una empresa usa Address v2 o campos legacy.

---

## 🔧 **IMPLEMENTACIÓN**

### **1. Model Field (ConfiguracionEmpresa)**

```python
# taller/models/configuracion.py

class ConfiguracionEmpresa(models.Model):
    # ...
    
    # Feature flag para rollout gradual
    use_address_v2 = models.BooleanField(
        default=False,
        verbose_name="Usar Address v2",
        help_text="Activar para usar el nuevo sistema de direcciones "
                  "estructuradas (Address). Desactivar para seguir usando "
                  "campos legacy (direccion, region, ciudad)."
    )
```

---

### **2. Helpers de Compatibilidad**

```python
# taller/utils/address_compat.py

from taller.utils.address_compat import (
    should_use_address_v2,
    get_company_address,
    get_company_address_text,
    get_cliente_address_text,
    enable_address_v2_for_company,
)

# Verificar si usar Address v2
if should_use_address_v2(empresa):
    address = get_company_address(empresa)
    direccion = address.full_address
else:
    direccion = empresa.configuracion.direccion  # Legacy
```

---

### **3. Views Compatibles (API por País)**

```python
# taller/views_extra/api_compat.py

# OLD (mantener por 1 release):
/br/api/estados/          → api_estados_br_compat()
/ve/api/estados/          → api_estados_ve_compat()
/pe/api/estados/          → api_estados_pe_compat()

# Internamente redirigen a:
/api/locations?country=BR
/api/locations?country=VE
/api/locations?country=PE

# Agregan deprecation warnings en logs
```

---

## 📝 **USO**

### **Activar Address v2 para una Empresa:**

```python
from taller.utils.address_compat import enable_address_v2_for_company

# Activar
enable_address_v2_for_company(empresa, True)

# Desactivar
enable_address_v2_for_company(empresa, False)
```

---

### **En Views:**

```python
from taller.utils.address_compat import should_use_address_v2

def mi_view(request):
    empresa = request.user.empresa
    
    if should_use_address_v2(empresa):
        # Usar Address v2
        address = empresa.configuracion.legal_address
        if address:
            direccion = address.full_address
            sales_tax = address.sales_tax
    else:
        # Usar campos legacy
        direccion = empresa.configuracion.direccion
        sales_tax = 0.0  # Legacy no tiene sales_tax automático
    
    context = {
        'direccion': direccion,
        'sales_tax': sales_tax,
    }
    return render(request, 'mi_template.html', context)
```

---

### **En Templates:**

```django
{% load static %}

<!-- Usar context processor -->
{% if use_address_v2 %}
    <!-- Formulario Address v2 -->
    <script type="module">
        import { bindCountryStateCity } from "{% static 'js/locations.js' %}";
        bindCountryStateCity('#id_country', '#id_state', '#id_city');
    </script>
{% else %}
    <!-- Formulario legacy -->
    <input type="text" name="direccion" placeholder="Dirección">
{% endif %}
```

---

### **Decorador para Views:**

```python
from taller.utils.address_compat import requires_address_v2

@requires_address_v2
def mi_nueva_feature(request):
    """View que solo funciona con Address v2"""
    # Esta view solo se ejecuta si use_address_v2=True
    # Si no, redirige a configuración con mensaje
    pass
```

---

## 🔄 **MIGRACIÓN DE DATOS**

### **Migrar Cliente Individual:**

```python
from taller.utils.address_compat import migrate_cliente_to_address_v2

# Migrar un cliente
cliente = Cliente.objects.get(id=123)
if migrate_cliente_to_address_v2(cliente):
    print("Cliente migrado exitosamente a Address v2")
```

---

### **Migrar Todos los Clientes de una Empresa:**

```python
from taller.models import Cliente
from taller.utils.address_compat import migrate_cliente_to_address_v2

empresa = Empresa.objects.get(id=456)

# Migrar todos los clientes
clientes = Cliente.objects.filter(empresa=empresa, billing_address__isnull=True)

migrated = 0
for cliente in clientes:
    if migrate_cliente_to_address_v2(cliente):
        migrated += 1

print(f"Migrados: {migrated}/{clientes.count()}")
```

---

### **Management Command (Batch):**

```bash
# Usar el comando existente de backfill
python manage.py backfill_addresses --empresa=123

# O para todas las empresas con Address v2 activado
python manage.py backfill_addresses --only-v2-enabled
```

---

## ⚠️ **DEPRECATION WARNINGS**

### **APIs Legacy:**

Las APIs por país (`/br/api/estados/`, `/ve/api/estados/`, etc.) están **DEPRECATED**.

**Aviso en logs:**
```
[WARNING] /br/api/estados/ está deprecated. 
Usar /api/locations?country=BR en su lugar.
```

**Headers HTTP:**
```
Warning: 299 - "This endpoint is deprecated. Use /api/locations instead."
Deprecation: true
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
```

---

## 📊 **DASHBOARDS Y KPIs**

### **SIN CAMBIOS** ✅

Los dashboards y KPIs **NO** cambian con Address v2:
- Siguen usando `fecha_emision` para filtros
- Totales se calculan igual
- Reportes mantienen misma estructura

```python
# KPIs siguen igual
from django.db.models import Sum
from datetime import datetime, timedelta

# Total ventas del mes (sin cambios)
inicio_mes = datetime.now().replace(day=1)
ventas = Documento.objects.filter(
    empresa=empresa,
    fecha_emision__gte=inicio_mes  # ✅ Sin cambios
).aggregate(total=Sum('total'))['total']

# Documentos por mes (sin cambios)
docs_por_mes = Documento.objects.filter(
    empresa=empresa
).dates('fecha_emision', 'month')  # ✅ Sin cambios
```

**Address v2 NO afecta:**
- Índices de base de datos
- Queries de reportes
- Filtros por fecha
- Totales y subtotales
- Cálculos de impuestos (solo mejora precisión)

---

## 🧪 **TESTING**

### **Test Feature Flag:**

```python
import pytest
from taller.utils.address_compat import should_use_address_v2

@pytest.mark.django_db
def test_feature_flag_default_false(empresa):
    """Por defecto, use_address_v2 es False"""
    assert should_use_address_v2(empresa) == False

@pytest.mark.django_db
def test_feature_flag_can_enable(empresa):
    """Se puede activar Address v2"""
    empresa.configuracion.use_address_v2 = True
    empresa.configuracion.save()
    
    assert should_use_address_v2(empresa) == True
```

---

### **Test Compatibilidad:**

```python
@pytest.mark.django_db
def test_get_address_text_v2(empresa_con_address_v2):
    """Obtener dirección con Address v2"""
    from taller.utils.address_compat import get_company_address_text
    
    text = get_company_address_text(empresa_con_address_v2)
    assert len(text) > 0
    assert 'Lima' in text  # Ejemplo

@pytest.mark.django_db
def test_get_address_text_legacy(empresa_legacy):
    """Obtener dirección con campos legacy"""
    from taller.utils.address_compat import get_company_address_text
    
    empresa_legacy.configuracion.direccion = 'Av. Test 123'
    empresa_legacy.configuracion.save()
    
    text = get_company_address_text(empresa_legacy)
    assert text == 'Av. Test 123'
```

---

## 📋 **CHECKLIST DE MIGRACIÓN**

### **Para Desarrolladores:**
- [✅] Feature flag `use_address_v2` agregado
- [✅] Helpers de compatibilidad creados
- [✅] Views legacy redirigen a API unificada
- [✅] Deprecation warnings implementados
- [✅] Middleware de deprecación creado
- [✅] Context processor para templates
- [✅] Decorador `@requires_address_v2`
- [✅] Migración de base de datos creada
- [✅] Tests de compatibilidad
- [✅] Documentación completa

### **Para DevOps (Deploy):**
- [ ] Aplicar migración `0029_add_use_address_v2_flag`
- [ ] Verificar logs de deprecación
- [ ] Monitorear uso de APIs legacy
- [ ] Planificar removal de APIs legacy (Release +1)

### **Para Product:**
- [ ] Comunicar a clientes sobre Address v2
- [ ] Documentar beneficios (sales tax automático, etc.)
- [ ] Ofrecer migración asistida
- [ ] Planificar sunset de APIs legacy

---

## 🎯 **TIMELINE RECOMENDADO**

```
Release 1.0 (Actual):
  ✅ Feature flag implementado
  ✅ APIs legacy funcionan (con deprecation)
  ✅ Address v2 opcional
  → Empresas pueden optar por Address v2

Release 1.1 (1-3 meses):
  → Nuevas empresas: Address v2 por defecto
  → Empresas existentes: notificación de migración
  → APIs legacy: deprecation warning visible

Release 2.0 (3-6 meses):
  → APIs legacy removidas
  → Address v2 obligatorio para nuevos clientes
  → Campos legacy: solo lectura

Release 3.0 (6-12 meses):
  → Campos legacy removidos
  → Solo Address v2
  → Cleanup completo
```

---

## 🚨 **BREAKING CHANGES (Futuro)**

### **Release 2.0 (3-6 meses):**
- ❌ Remover endpoints `/br/api/estados/`, `/ve/api/estados/`, `/pe/api/estados/`
- ✅ Solo `/api/locations` disponible
- ⚠️ Clientes deben migrar a API unificada

### **Release 3.0 (6-12 meses):**
- ❌ Remover campos `direccion`, `region`, `ciudad` legacy
- ✅ Solo Address v2
- ⚠️ Migración obligatoria

---

## 💡 **BEST PRACTICES**

### **1. Siempre verificar feature flag:**
```python
if should_use_address_v2(empresa):
    # Lógica Address v2
else:
    # Lógica legacy
```

### **2. Usar helpers, no acceder directamente:**
```python
# ✅ BIEN
text = get_company_address_text(empresa)

# ❌ MAL
text = empresa.configuracion.direccion
```

### **3. Agregar deprecation warnings:**
```python
import logging
logger = logging.getLogger(__name__)

def mi_funcion_legacy():
    logger.warning("[DEPRECATED] Esta función será removida en Release 2.0")
    # ... código legacy
```

### **4. Documentar en código:**
```python
def mi_view(request):
    """
    [DEPRECATED] Esta view será removida en Release 2.0.
    Usar mi_nueva_view en su lugar.
    """
    pass
```

---

## 🎊 **RESUMEN**

✅ **Feature flag implementado** (`use_address_v2`)  
✅ **Helpers de compatibilidad** creados  
✅ **Views legacy mantienen compatibilidad** por 1 release  
✅ **Deprecation warnings** implementados  
✅ **Dashboards/KPIs sin cambios** ✅  
✅ **Migración gradual** planificada  
✅ **Production ready**  

**Estado:** ✅ **LISTO PARA ROLLOUT GRADUAL**

---

**Siguiente:** Aplicar migración y activar Address v2 para empresas piloto.

