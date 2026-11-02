"""
Template tags para verificar roles y permisos en templates

Usage:
    {% load role_tags %}

    {% if request.user|has_role:'Owner' %}
        ...
    {% endif %}

    {% if request.user|is_staff_member %}
        ...
    {% endif %}
"""

from django import template

register = template.Library()


@register.filter(name="has_role")
def has_role(user, role_name):
    """
    Verifica si un usuario tiene un rol específico.

    Args:
        user: Usuario a verificar
        role_name: Nombre del rol/grupo

    Returns:
        bool: True si el usuario tiene el rol o es superuser

    Usage:
        {% if request.user|has_role:'Owner' %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name=role_name).exists()


@register.filter(name="has_any_role")
def has_any_role(user, role_names):
    """
    Verifica si un usuario tiene alguno de los roles especificados.

    Args:
        user: Usuario a verificar
        role_names: String con nombres de roles separados por coma (ej: 'Owner,Admin')

    Returns:
        bool: True si el usuario tiene alguno de los roles o es superuser

    Usage:
        {% if request.user|has_any_role:'Owner,Admin' %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # Separar roles por coma y limpiar espacios
    role_list = [role.strip() for role in str(role_names).split(",")]
    return user.groups.filter(name__in=role_list).exists()


@register.filter(name="is_owner")
def is_owner(user):
    """
    Verifica si un usuario es Owner.

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Owner o superuser

    Usage:
        {% if request.user|is_owner %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.groups.filter(name="Owner").exists():
        return True

    # Fallback: users who own an Empresa directly (pre-TeamMember legacy owners)
    try:
        from taller.models.empresa import Empresa
        return Empresa.objects.filter(user=user).exists()
    except Exception:
        return False


@register.filter(name="is_admin_or_owner")
def is_admin_or_owner(user):
    """
    Verifica si un usuario es Admin u Owner.

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Admin, Owner o superuser

    Usage:
        {% if request.user|is_admin_or_owner %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name__in=["Owner", "Admin"]).exists()


@register.filter(name="is_staff_member")
def is_staff_member(user):
    """
    Verifica si un usuario es staff (Owner o Admin).
    Alias de is_admin_or_owner para compatibilidad.

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Admin, Owner o superuser

    Usage:
        {% if request.user|is_staff_member %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(name__in=["Owner", "Admin"]).exists()


@register.filter(name="is_vendedor")
def is_vendedor(user):
    """
    Verifica si un usuario es Vendedor.

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Vendedor o superior

    Usage:
        {% if request.user|is_vendedor %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # Vendedor o superior (Owner, Admin también pueden vender)
    return user.groups.filter(name__in=["Owner", "Admin", "Vendedor"]).exists()


@register.filter(name="is_tecnico")
def is_tecnico(user):
    """
    Verifica si un usuario es Técnico (sin otros roles superiores).

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Técnico (solo, sin roles superiores)

    Usage:
        {% if request.user|is_tecnico %}
            ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return False  # Superuser no es "solo técnico"

    user_groups = set(user.groups.values_list("name", flat=True))

    # Si tiene otros roles superiores, no es "solo técnico"
    superior_roles = {"Owner", "Admin", "Vendedor"}
    if user_groups.intersection(superior_roles):
        return False

    # Es técnico si tiene el rol Tecnico y no tiene roles superiores
    return "Tecnico" in user_groups
