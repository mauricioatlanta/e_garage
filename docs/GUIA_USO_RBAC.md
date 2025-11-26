# 🔒 Guía de Uso: Sistema RBAC (Roles y Permisos)

## 🎯 Resumen Ejecutivo

El sistema RBAC protege secciones sensibles del sistema basándose en roles. Solo dueños y administradores pueden ver el Dashboard de BI y configuraciones sensibles.

## ⚡ Uso Rápido

### 1. Crear Roles

Ejecutar el comando para crear los roles estándar:

```bash
python manage.py setup_roles
```

Esto crea los grupos:
- **Owner** (Dueño)
- **Admin** (Administrador)
- **Vendedor** (Sales)
- **Tecnico** (Tech)

### 2. Asignar Roles a Usuarios

En el admin de Django:
1. Ir a `Admin > Users > [Usuario]`
2. Seleccionar grupo(s) en "Groups"
3. Guardar

O mediante código:

```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='dueno')
owner_group = Group.objects.get(name='Owner')
user.groups.add(owner_group)
```

### 3. Proteger Vistas

#### Vistas Basadas en Clases (CBV)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from taller.auth.decorators_role import RoleRequiredMixin

class DashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = ['Owner', 'Admin']  # 🔒 Solo estos roles
    template_name = 'dashboard.html'
```

#### Vistas Funcionales (FBV)

```python
from django.contrib.auth.decorators import login_required
from taller.auth.decorators_role import role_required

@login_required
@role_required('Owner', 'Admin')
def configuracion_empresa(request):
    # Solo Owner y Admin pueden acceder
    ...
```

### 4. Usar en Templates

```django
{% load role_tags %}

<!-- Menú para todos -->
<a href="{% url 'crear_documento' %}">Nuevo Documento</a>

<!-- Menú solo para Owner/Admin -->
{% if request.user|is_staff_member %}
    <a href="{% url 'taller:dashboard_bi' %}">
        📊 Inteligencia de Negocios
    </a>
    <a href="{% url 'configuracion_empresa' %}">
        ⚙️ Configuración
    </a>
{% endif %}

<!-- Solo Owner -->
{% if request.user|is_owner %}
    <a href="{% url 'gestion_usuarios' %}">
        👥 Gestión de Usuarios
    </a>
{% endif %}
```

## 📋 Roles Definidos

### Owner (Dueño)
**Acceso total:**
- ✅ Dashboard de BI
- ✅ Configuración de empresa
- ✅ Gestión de usuarios
- ✅ Todos los documentos
- ✅ Inventario completo
- ✅ Anular facturas

### Admin (Administrador)
**Gestión operativa:**
- ✅ Dashboard de BI (solo lectura)
- ✅ Documentos (crear, editar, eliminar, anular)
- ✅ Inventario
- ✅ Clientes y vehículos
- ❌ Configuración sensible
- ❌ Gestión de usuarios

### Vendedor
**Ventas:**
- ✅ Crear cotizaciones
- ✅ Crear y editar documentos
- ✅ Ver clientes y vehículos
- ✅ Ver repuestos (sin precios de compra)
- ❌ Ver Dashboard de BI
- ❌ Borrar documentos
- ❌ Anular facturas

### Tecnico
**Trabajos asignados:**
- ✅ Ver sus OTs asignadas
- ✅ Actualizar estado de sus OTs
- ✅ Ver clientes y vehículos (solo lectura)
- ✅ Ver repuestos (sin precios de compra)
- ❌ Ver Dashboard de BI
- ❌ Ver ganancias
- ❌ Anular facturas

## 🎨 Template Tags Disponibles

### `has_role`
Verifica si el usuario tiene un rol específico:

```django
{% if request.user|has_role:'Owner' %}
    ...
{% endif %}
```

### `has_any_role`
Verifica si el usuario tiene alguno de los roles especificados:

```django
{% if request.user|has_any_role:'Owner,Admin' %}
    ...
{% endif %}
```

### `is_owner`
Verifica si el usuario es Owner:

```django
{% if request.user|is_owner %}
    ...
{% endif %}
```

### `is_staff_member` / `is_admin_or_owner`
Verifica si el usuario es Owner o Admin:

```django
{% if request.user|is_staff_member %}
    ...
{% endif %}
```

### `is_vendedor`
Verifica si el usuario es Vendedor o superior:

```django
{% if request.user|is_vendedor %}
    ...
{% endif %}
```

### `is_tecnico`
Verifica si el usuario es solo Técnico (sin roles superiores):

```django
{% if request.user|is_tecnico %}
    ...
{% endif %}
```

## 🔒 Seguridad

### Multi-Tenant + RBAC

Los roles son globales, pero el acceso a datos sigue siendo multi-tenant:

```python
# ✅ Siempre filtrar por empresa Y verificar rol
if not is_staff_member(request.user):
    raise PermissionDenied()

documento = Documento.objects.filter(
    empresa=request.user.empresa,  # 🔒 Multi-tenant
    id=documento_id
).first()
```

### Superuser

Los superusers siempre tienen acceso (para soporte técnico):

```python
# Superuser siempre pasa
if request.user.is_superuser:
    return view_func(request, *args, **kwargs)
```

## ✅ Resultado

Con este sistema:
- ✅ El Dashboard de BI está protegido (solo Owner/Admin)
- ✅ Los técnicos no ven información financiera
- ✅ Los menús se ocultan según el rol
- ✅ Es multi-tenant seguro
- ✅ Registra accesos denegados en logs

**¡Sistema RBAC completo y funcionando!** 🔒

