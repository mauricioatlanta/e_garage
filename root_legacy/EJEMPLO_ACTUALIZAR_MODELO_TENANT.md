# 📝 Ejemplo: Actualizar Modelo para Multi-Tenant Hardening

## Ejemplo con Modelo `Cliente`

### ANTES (Inseguro):

```python
# taller/models/cliente.py
from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    objects = models.Manager()  # ❌ Peligroso: permite consultas sin filtro
    
    def __str__(self):
        return self.nombre
```

**Problemas:**
- ❌ `Cliente.objects.all()` devuelve TODOS los clientes de TODAS las empresas
- ❌ `Cliente.objects.get(id=123)` puede devolver clientes de otras empresas
- ❌ Fácil olvidar filtrar por empresa

---

### DESPUÉS (Seguro):

```python
# taller/models/cliente.py
from django.db import models
from taller.managers.empresa_aware import EmpresaAwareManagerStrict

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_index=True)
    
    objects = EmpresaAwareManagerStrict()  # ✅ Manager estricto
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'clientes'
        indexes = [
            models.Index(fields=['empresa', 'nombre']),
        ]
```

**Ventajas:**
- ✅ `Cliente.objects.all()` lanza `PermissionDenied` - fuerza usar `para_empresa()`
- ✅ `Cliente.objects.get(id=123)` requiere filtro explícito
- ✅ Imposible olvidar filtrar por empresa

---

## Actualizar Vistas

### ANTES (Inseguro):

```python
# taller/clientes/views.py
from django.views.generic import ListView
from taller.models import Cliente

class ClienteListView(ListView):
    model = Cliente
    
    def get_queryset(self):
        # ❌ Peligroso: si olvidas filtrar, devuelve todos
        return Cliente.objects.all()
```

---

### DESPUÉS (Seguro):

```python
# taller/clientes/views.py
from django.views.generic import ListView
from taller.models import Cliente
from taller.mixins.empresa_required import EmpresaScopedMixin

class ClienteListView(EmpresaScopedMixin, ListView):
    model = Cliente
    # ✅ Automáticamente filtra por empresa
    # ✅ Incluye empresa en contexto para templates
```

**O con método explícito:**

```python
class ClienteListView(EmpresaScopedMixin, ListView):
    model = Cliente
    
    def get_queryset(self):
        # ✅ Explícito y seguro
        return Cliente.objects.para_usuario(self.request.user)
```

---

## Actualizar Vistas de Detalle

### ANTES (Inseguro):

```python
class ClienteDetailView(DetailView):
    model = Cliente
    # ❌ Cualquiera puede acceder a /clientes/123/ aunque no sea de su empresa
```

---

### DESPUÉS (Seguro):

```python
from taller.mixins.empresa_required import EmpresaRequiredMixin

class ClienteDetailView(EmpresaRequiredMixin, DetailView):
    model = Cliente
    # ✅ Automáticamente verifica que cliente.empresa == request.user.empresa
    # ✅ Si no pertenece, devuelve 404 (oculta existencia de objetos de otras empresas)
```

---

## Actualizar Vistas de Creación

### ANTES (Inseguro):

```python
class ClienteCreateView(CreateView):
    model = Cliente
    fields = ['nombre', 'email']
    
    def form_valid(self, form):
        # ❌ Si olvidas asignar empresa, el objeto puede quedar sin empresa
        return super().form_valid(form)
```

---

### DESPUÉS (Seguro):

```python
from taller.mixins.empresa_required import EmpresaScopedMixin

class ClienteCreateView(EmpresaScopedMixin, CreateView):
    model = Cliente
    fields = ['nombre', 'email']
    # ✅ Empresa se asigna automáticamente en form_valid()
```

---

## Actualizar Vistas Funcionales

### ANTES (Inseguro):

```python
from django.shortcuts import get_object_or_404

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    # ❌ Puede ser cliente de otra empresa
    # ...
```

---

### DESPUÉS (Seguro):

**Opción 1: Usar manager**
```python
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

@login_required
def editar_cliente(request, cliente_id):
    # ✅ Solo obtiene clientes de la empresa del usuario
    cliente = get_object_or_404(
        Cliente.objects.para_usuario(request.user),
        id=cliente_id
    )
    # ...
```

**Opción 2: Verificación explícita**
```python
from django.shortcuts import get_object_or_404
from taller.utils.tenant_audit import verify_object_ownership
from django.core.exceptions import PermissionDenied

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # ✅ Verificar pertenencia
    if not verify_object_ownership(cliente, request.user):
        raise PermissionDenied("Este cliente no pertenece a tu empresa")
    
    # ...
```

---

## Checklist de Actualización

Al actualizar un modelo para multi-tenant:

- [ ] Importar `EmpresaAwareManagerStrict` o `EmpresaAwareManager`
- [ ] Reemplazar `objects = models.Manager()` por manager apropiado
- [ ] Verificar que campo `empresa` tenga `db_index=True`
- [ ] Agregar índices compuestos si es necesario
- [ ] Actualizar vistas para usar `EmpresaScopedMixin` o `EmpresaRequiredMixin`
- [ ] Actualizar vistas funcionales para usar `para_usuario()` o `para_empresa()`
- [ ] Actualizar tests para verificar aislamiento
- [ ] Actualizar documentación

---

## Modelos Prioritarios para Actualizar

1. **Cliente** - Datos críticos de clientes
2. **Documento** - Facturas y órdenes de trabajo
3. **Vehiculo** - Vehículos de clientes
4. **DocumentoItem** - Items de documentos
5. **Repuesto** - Inventario por empresa
6. **Servicio** - Servicios por empresa (si aplica)

Comenzar con estos modelos y luego extender a otros según necesidad.

