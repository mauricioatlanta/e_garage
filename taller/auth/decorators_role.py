"""
Decoradores y Mixins para control de acceso basado en roles (RBAC)

Permite proteger vistas basándose en la pertenencia a grupos de Django.
"""

import logging
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

log = logging.getLogger(__name__)


def role_required(*roles):
    """
    Decorador para Vistas Funcionales (FBV).

    Verifica que el usuario tenga AL MENOS UNO de los roles especificados.

    Args:
        *roles: Nombres de roles/grupos permitidos (ej: 'Owner', 'Admin')

    Usage:
        @login_required
        @role_required('Owner', 'Admin')
        def vista_sensible(request):
            ...

    Raises:
        PermissionDenied: Si el usuario no tiene ningún rol permitido
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Si no está autenticado, dejar que @login_required lo maneje
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)

            # Superuser siempre pasa (para soporte técnico)
            if request.user.is_superuser:
                log.debug(f"[RBAC] Superuser {request.user.id} accediendo a {view_func.__name__}")
                return view_func(request, *args, **kwargs)

            # Fallback Owner legacy: usuarios que son dueños directos de una Empresa
            # (creados antes de TeamMember/Groups). Sin esto quedarían bloqueados
            # aunque sean los dueños del taller.
            if "Owner" in roles:
                try:
                    from taller.models.empresa import Empresa
                    if Empresa.objects.filter(user=request.user).exists():
                        return view_func(request, *args, **kwargs)
                except Exception:
                    pass

            # Obtener grupos del usuario
            user_groups = set(request.user.groups.values_list("name", flat=True))
            allowed_roles = set(roles)

            # Verificar si el usuario tiene AL MENOS UNO de los roles permitidos
            if user_groups.intersection(allowed_roles):
                log.debug(
                    f"[RBAC] Usuario {request.user.id} ({list(user_groups)}) "
                    f"tiene acceso a {view_func.__name__} (roles requeridos: {list(allowed_roles)})"
                )
                return view_func(request, *args, **kwargs)

            # No tiene permisos
            log.warning(
                f"[RBAC] Usuario {request.user.id} ({list(user_groups)}) "
                f"DENEGADO acceso a {view_func.__name__} (roles requeridos: {list(allowed_roles)})"
            )
            raise PermissionDenied(
                f"No tienes permisos para acceder a esta sección. "
                f"Roles requeridos: {', '.join(roles)}"
            )

        return _wrapped_view

    return decorator


class RoleRequiredMixin(AccessMixin):
    """
    Mixin para Vistas Basadas en Clases (CBV).

    Verifica que el usuario tenga AL MENOS UNO de los roles especificados.

    Attributes:
        allowed_roles: Lista de nombres de roles/grupos permitidos

    Usage:
        class DashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
            allowed_roles = ['Owner', 'Admin']
            template_name = 'dashboard.html'

    Raises:
        PermissionDenied: Si el usuario no tiene ningún rol permitido
    """

    allowed_roles = []
    permission_denied_message = "No tienes acceso a esta vista."

    def dispatch(self, request, *args, **kwargs):
        """Verifica permisos antes de despachar la vista"""
        # Si no está autenticado, dejar que LoginRequiredMixin lo maneje
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Superuser siempre pasa (para soporte técnico)
        if request.user.is_superuser:
            log.debug(f"[RBAC] Superuser {request.user.id} accediendo a {self.__class__.__name__}")
            return super().dispatch(request, *args, **kwargs)

        # Verificar si se definieron roles
        if not self.allowed_roles:
            log.warning(
                f"[RBAC] Vista {self.__class__.__name__} sin roles definidos. "
                "Se asume acceso restringido."
            )
            raise PermissionDenied("Vista sin roles definidos.")

        # Obtener grupos del usuario
        user_groups = set(request.user.groups.values_list("name", flat=True))
        allowed_roles = set(self.allowed_roles)

        # Verificar si el usuario tiene AL MENOS UNO de los roles permitidos
        if user_groups.intersection(allowed_roles):
            log.debug(
                f"[RBAC] Usuario {request.user.id} ({list(user_groups)}) "
                f"tiene acceso a {self.__class__.__name__} "
                f"(roles requeridos: {list(allowed_roles)})"
            )
            return super().dispatch(request, *args, **kwargs)

        # No tiene permisos
        log.warning(
            f"[RBAC] Usuario {request.user.id} ({list(user_groups)}) "
            f"DENEGADO acceso a {self.__class__.__name__} "
            f"(roles requeridos: {list(allowed_roles)})"
        )
        raise PermissionDenied(
            f"{self.permission_denied_message} "
            f"Roles requeridos: {', '.join(self.allowed_roles)}"
        )


def is_owner(user):
    """
    Helper function para verificar si un usuario es Owner.

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Owner o superuser
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name="Owner").exists()


def is_admin_or_owner(user):
    """
    Helper function para verificar si un usuario es Admin u Owner.

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Admin, Owner o superuser
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["Owner", "Admin"]).exists()


def is_staff_member(user):
    """
    Helper function para verificar si un usuario es staff (Owner o Admin).
    Alias de is_admin_or_owner para compatibilidad.

    Args:
        user: Usuario a verificar

    Returns:
        bool: True si el usuario es Admin, Owner o superuser
    """
    return is_admin_or_owner(user)


def has_role(user, role_name):
    """
    Helper function para verificar si un usuario tiene un rol específico.

    Args:
        user: Usuario a verificar
        role_name: Nombre del rol/grupo

    Returns:
        bool: True si el usuario tiene el rol o es superuser
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=role_name).exists()


def has_any_role(user, *role_names):
    """
    Helper function para verificar si un usuario tiene alguno de los roles especificados.

    Args:
        user: Usuario a verificar
        *role_names: Nombres de roles/grupos

    Returns:
        bool: True si el usuario tiene alguno de los roles o es superuser
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=role_names).exists()
