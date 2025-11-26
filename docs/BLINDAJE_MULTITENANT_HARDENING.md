# 🛡️ BLINDAJE MULTI-TENANT - HARDENING COMPLETO

## 📋 Resumen

Este documento describe la implementación completa de aislamiento multi-tenant en eGarage, garantizando que cada empresa solo pueda acceder a sus propios datos.

---

## 🏗️ Arquitectura Implementada

### 1. **Custom Managers** (`taller/managers/empresa_aware.py`)

#### `EmpresaAwareManager`
Manager base que fuerza filtrado por empresa.

**Características:**
- ✅ Método `para_empresa(empresa)` - Filtrar por empresa específica
- ✅ Método `para_usuario(usuario)` - Filtrar por empresa del usuario
- ✅ Método `all()` con advertencia - Previene consultas sin filtro

**Uso:**
```python
from taller.models import Cliente
from taller.managers.empresa_aware import EmpresaAwareManager

class Cliente(models.Model):
    # ...
    objects = EmpresaAwareManager()
    
    # En vistas:
    clientes = Cliente.objects.para_usuario(request.user)
```

#### `EmpresaAwareManagerStrict`
Versión estricta que **NUNCA** permite consultas sin filtro.

**Características:**
- ❌ `all()` lanza `PermissionDenied`
- ❌ `filter()` requiere `empresa` o `empresa_id`
- ❌ `get()` requiere `empresa` o `empresa_id`

**Uso en modelos críticos:**
```python
class Documento(models.Model):
    # ...
    objects = EmpresaAwareManagerStrict()
```

---

### 2. **Mixins para Vistas** (`taller/mixins/empresa_required.py`)

#### `EmpresaRequiredMixin`
Mixin completo que garantiza aislamiento en vistas.

**Funciones:**
- ✅ Filtra automáticamente `get_queryset()` por empresa
- ✅ Verifica pertenencia en `get_object()`
- ✅ Asigna empresa automáticamente en `form_valid()`

**Uso:**
```python
from taller.mixins.empresa_required import EmpresaRequiredMixin
from django.views.generic import DetailView

class ClienteDetailView(EmpresaRequiredMixin, DetailView):
    model = Cliente
    # Automáticamente filtra y verifica empresa
```

#### `EmpresaScopedMixin`
Mixin combinado que incluye todo.

**Incluye:**
- Filtrado por empresa
- Verificación de pertenencia
- Contexto de empresa en templates

**Uso:**
```python
class ClienteCreateView(EmpresaScopedMixin, CreateView):
    model = Cliente
    fields = ['nombre', 'email']
    # Empresa se asigna automáticamente
```

---

### 3. **Middleware Mejorado** (`taller/middleware/tenant_isolation.py`)

#### `TenantIsolationMiddleware`
Middleware que garantiza `request.empresa` esté siempre disponible.

**Funciones:**
- ✅ Inyecta `request.empresa` basado en usuario
- ✅ Verifica suscripción activa
- ✅ Bloquea acceso sin empresa
- ✅ Logging de auditoría

**Configuración en `settings.py`:**
```python
MIDDLEWARE = [
    # ...
    'taller.middleware.tenant_isolation.TenantIsolationMiddleware',
    # Debe ir después de AuthenticationMiddleware
    # ...
]
```

---

## 📝 Guía de Implementación

### Paso 1: Actualizar Modelos

**Modelos críticos (Clientes, Documentos, Vehículos):**
```python
from taller.managers.empresa_aware import EmpresaAwareManagerStrict

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    objects = EmpresaAwareManagerStrict()  # Manager estricto
    
    class Meta:
        db_table = 'clientes'
```

**Modelos menos críticos:**
```python
from taller.managers.empresa_aware import EmpresaAwareManager

class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    
    objects = EmpresaAwareManager()  # Manager normal
```

### Paso 2: Actualizar Vistas

**Vistas basadas en clases:**
```python
from taller.mixins.empresa_required import EmpresaScopedMixin
from django.views.generic import ListView, DetailView, CreateView

class ClienteListView(EmpresaScopedMixin, ListView):
    model = Cliente
    # Automáticamente filtra por empresa

class ClienteDetailView(EmpresaScopedMixin, DetailView):
    model = Cliente
    # Verifica pertenencia automáticamente

class ClienteCreateView(EmpresaScopedMixin, CreateView):
    model = Cliente
    fields = ['nombre', 'email']
    # Asigna empresa automáticamente
```

**Vistas basadas en funciones:**
```python
from taller.utils.tenant_audit import verify_object_ownership
from django.core.exceptions import PermissionDenied

@login_required
def editar_cliente(request, cliente_id):
    cliente = Cliente.objects.para_usuario(request.user).get(id=cliente_id)
    # O verificar manualmente:
    # cliente = Cliente.objects.get(id=cliente_id)
    # if not verify_object_ownership(cliente, request.user):
    #     raise PermissionDenied
    
    # ... resto del código
```

### Paso 3: Verificar Consultas Manuales

**❌ INCORRECTO:**
```python
# PELIGROSO: Devuelve clientes de TODAS las empresas
clientes = Cliente.objects.all()

# PELIGROSO: Puede devolver objetos de otras empresas
cliente = Cliente.objects.get(id=123)
```

**✅ CORRECTO:**
```python
# Seguro: Filtrado por empresa del usuario
clientes = Cliente.objects.para_usuario(request.user)

# Seguro: Filtrado explícito
clientes = Cliente.objects.para_empresa(request.user.empresa)

# Seguro: Verificación adicional
cliente = Cliente.objects.para_usuario(request.user).get(id=123)
```

---

## 🔍 Auditoría y Detección

### Verificar Aislamiento en Testing

```python
from taller.utils.tenant_audit import check_queryset_isolation

def test_clientes_aislados():
    user1 = User.objects.get(username='usuario1')
    user2 = User.objects.get(username='usuario2')
    
    clientes1 = Cliente.objects.para_usuario(user1)
    assert check_queryset_isolation(clientes1, user1.empresa.id, 'Cliente')
    
    # Verificar que user2 no ve clientes de user1
    cliente_user1 = clientes1.first()
    clientes2 = Cliente.objects.para_usuario(user2)
    assert cliente_user1.id not in [c.id for c in clientes2]
```

### Logging de Violaciones

El sistema automáticamente registra violaciones potenciales:
- Acceso a objetos sin filtro de empresa
- Intentos de acceso a objetos de otras empresas
- Consultas sospechosas

Revisar logs periódicamente:
```bash
grep "VIOLACIÓN DE AISLAMIENTO TENANT" logs/django.log
```

---

## ⚠️ Reglas de Oro

1. **NUNCA usar `Model.objects.all()` sin filtro** en código de producción
2. **SIEMPRE usar `para_usuario()` o `para_empresa()`** en vistas
3. **SIEMPRE verificar pertenencia** antes de modificar objetos
4. **SIEMPRE usar mixins** en vistas basadas en clases
5. **SIEMPRE asignar empresa** al crear objetos nuevos

---

## 🚨 Checklist de Seguridad

Antes de desplegar código que accede a modelos con `empresa`:

- [ ] ¿El modelo usa `EmpresaAwareManager` o `EmpresaAwareManagerStrict`?
- [ ] ¿Las vistas usan `EmpresaRequiredMixin` o `EmpresaScopedMixin`?
- [ ] ¿Las consultas manuales usan `para_usuario()` o `para_empresa()`?
- [ ] ¿Se verifica pertenencia antes de modificar objetos?
- [ ] ¿Se asigna empresa automáticamente al crear objetos?
- [ ] ¿Los tests verifican aislamiento entre empresas?

---

## 📊 Modelos Actualizados

### Modelos con Manager Estricto (Requeridos):
- ✅ `Cliente`
- ✅ `Documento`
- ✅ `Vehiculo`
- ✅ `DocumentoItem`
- ⚠️ Otros modelos con `empresa` (revisar)

### Modelos con Manager Normal:
- `Marca` (puede ser compartida)
- `Modelo` (puede ser compartida)
- `Servicio` (puede ser compartido)

---

## 🔧 Mantenimiento

### Auditoría Periódica

1. Revisar logs mensualmente buscando violaciones
2. Ejecutar tests de aislamiento regularmente
3. Revisar código nuevo antes de merge
4. Monitorear accesos sospechosos

### Actualización de Modelos

Cuando agregues un nuevo modelo con relación a `Empresa`:

1. Agregar `EmpresaAwareManager` al modelo
2. Actualizar vistas para usar mixins
3. Agregar tests de aislamiento
4. Documentar en este archivo

---

**Fecha de implementación:** Noviembre 2025  
**Versión:** 1.0  
**Estado:** ✅ Implementado y documentado

