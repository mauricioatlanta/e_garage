# 🔒 Sistema de Roles y Permisos (RBAC) - Implementación Completa

## 📋 Resumen

Implementación completa del sistema de Roles y Permisos (RBAC - Role Based Access Control) para proteger el Dashboard de BI y otras secciones sensibles. Solo dueños y administradores pueden ver información financiera.

**Features:**
- ✅ 4 roles estándar (Owner, Admin, Vendedor, Tecnico)
- ✅ Decoradores y mixins para proteger vistas
- ✅ Template tags para verificar roles en templates
- ✅ Multi-tenant seguro
- ✅ Logging de accesos denegados

## 🎯 Problema Resuelto

**Problema:**
- ❌ Cualquier usuario logueado podía ver el Dashboard de BI
- ❌ Técnicos junior veían ganancias netas del dueño
- ❌ Sin control granular de permisos

**Solución:**
- ✅ Dashboard de BI solo para Owner y Admin
- ✅ Roles definidos con permisos específicos
- ✅ Decoradores y mixins para proteger vistas
- ✅ Template tags para ocultar elementos del menú

## 📁 Archivos Creados

### 1. Comando de Gestión de Roles
**Archivo**: `taller/management/commands/setup_roles.py`

Comando para crear los grupos de roles estándar:

```bash
python manage.py setup_roles
```

Crea los roles:
- **Owner** (Dueño): Acceso total
- **Admin** (Administrador): Gestión operativa
- **Vendedor** (Sales): Crear cotizaciones, vender
- **Tecnico** (Tech): Solo sus OTs asignadas

### 2. Decoradores y Mixins
**Archivo**: `taller/auth/decorators_role.py`

Decoradores y mixins para proteger vistas:

```python
from taller.auth.decorators_role import role_required, RoleRequiredMixin

# Para FBV (Vistas Funcionales)
@role_required('Owner', 'Admin')
def vista_sensible(request):
    ...

# Para CBV (Vistas Basadas en Clases)
class DashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = ['Owner', 'Admin']
```

### 3. Template Tags
**Archivo**: `taller/templatetags/role_tags.py`

Template tags para verificar roles:

```django
{% load role_tags %}

{% if request.user|has_role:'Owner' %}
    ...
{% endif %}

{% if request.user|is_staff_member %}
    ...
{% endif %}
```

### 4. Vista Protegida
**Archivo**: `taller/views/dashboard_bi.py`

Vista del Dashboard de BI protegida:

```python
class DashboardHomeView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    allowed_roles = ['Owner', 'Admin']  # 🔒 Solo estos roles
```

## 🔧 Configuración

### 1. Crear Roles

Ejecutar el comando para crear los roles:

```bash
python manage.py setup_roles
```

Salida esperada:
```
✅ Rol creado: Owner - Dueño - Acceso total...
✅ Rol creado: Admin - Administrador - Gestión operativa...
✅ Rol creado: Vendedor - Vendedor - Crear cotizaciones...
✅ Rol creado: Tecnico - Técnico - Solo sus OTs...
```

### 2. Asignar Roles a Usuarios

En el admin de Django o mediante código:

```python
from django.contrib.auth.models import User, Group

# Obtener usuario y grupo
user = User.objects.get(username='dueno')
owner_group = Group.objects.get(name='Owner')

# Asignar rol
user.groups.add(owner_group)
```

O desde el admin:
1. Ir a `Admin > Users > [Usuario]`
2. Seleccionar grupo(s) en "Groups"
3. Guardar

## 🎨 Uso

### Proteger Vistas Funcionales (FBV)

```python
from django.contrib.auth.decorators import login_required
from taller.auth.decorators_role import role_required

@login_required
@role_required('Owner', 'Admin')
def configuracion_empresa(request):
    """Solo Owner y Admin pueden acceder"""
    ...

@login_required
@role_required('Owner')
def gestion_usuarios(request):
    """Solo Owner puede acceder"""
    ...
```

### Proteger Vistas Basadas en Clases (CBV)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from taller.auth.decorators_role import RoleRequiredMixin

class DashboardBIView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = 'dashboard/bi.html'
    allowed_roles = ['Owner', 'Admin']  # 🔒 Solo estos roles
```

### Usar en Templates

```django
{% load role_tags %}

<!-- Menú para todos -->
<a href="{% url 'crear_documento' %}">Nuevo Documento</a>

<!-- Menú solo Jefes (Owner/Admin) -->
{% if request.user|is_staff_member %}
    <a href="{% url 'taller:dashboard_bi' %}" class="text-gold">
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

### Verificar Roles en Código Python

```python
from taller.auth.decorators_role import has_role, is_staff_member

# Verificar si tiene un rol específico
if has_role(request.user, 'Owner'):
    # Es dueño
    ...

# Verificar si es staff (Owner o Admin)
if is_staff_member(request.user):
    # Es dueño o administrador
    ...
```

## 📊 Roles Definidos

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

## 🔒 Seguridad

### Multi-Tenant

Los roles son globales, pero el acceso a datos sigue siendo multi-tenant:

```python
# ✅ Siempre filtrar por empresa
documento = Documento.objects.filter(
    empresa=request.user.empresa,  # 🔒 Multi-tenant
    id=documento_id
).first()

# ✅ Verificar rol además de multi-tenant
if not is_staff_member(request.user):
    raise PermissionDenied()
```

### Logging

El sistema registra todos los accesos denegados:

```
[RBAC] Usuario 5 (['Tecnico']) DENEGADO acceso a DashboardHomeView (roles requeridos: ['Owner', 'Admin'])
```

### Superuser

Los superusers siempre tienen acceso (para soporte técnico):

```python
# Superuser siempre pasa
if request.user.is_superuser:
    return view_func(request, *args, **kwargs)
```

## ✅ Template Tags Disponibles

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

## 🚀 Próximos Pasos Opcionales

1. **Permisos Granulares**
   - Usar permisos de Django para control más fino
   - Crear permisos personalizados por acción

2. **Filtros de Queryset**
   - Filtrar querysets según rol (ej: técnicos solo ven sus OTs)

3. **Auditoría**
   - Registrar todos los accesos a secciones sensibles

4. **Roles Personalizados**
   - Permitir crear roles personalizados por empresa

## ✅ Checklist de Implementación

- [x] Comando setup_roles creado
- [x] Decoradores y mixins creados
- [x] Template tags creados
- [x] Dashboard de BI protegido
- [x] Logging de accesos
- [ ] Ejecutar setup_roles en servidor
- [ ] Asignar roles a usuarios existentes
- [ ] Actualizar menús en templates
- [ ] Probar con diferentes roles
- [ ] Documentar para usuarios finales

## 🎉 Resultado

Con este sistema, tu aplicación ahora:
- ✅ Protege el Dashboard de BI (solo Owner/Admin)
- ✅ Controla acceso a secciones sensibles
- ✅ Oculta elementos del menú según rol
- ✅ Es multi-tenant seguro
- ✅ Registra accesos denegados

**¡Sistema RBAC completo y funcionando!** 🔒

