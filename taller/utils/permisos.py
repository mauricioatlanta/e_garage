# utils/permisos.py
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from taller.models.auditoria import LogAuditoria
from taller.models.perfil_usuario import PerfilUsuario


RUBRO_ALIASES = {
    "TALLER": "WORKSHOP",
    "TALLER_MECANICO": "WORKSHOP",
    "DESARME": "DESARMADURIA",
    "DESARMADURIA": "DESARMADURIA",
    "REPUESTOS": "PARTS",
    "CASA_REPUESTOS": "PARTS",
    "GRUAS": "TOWING",
    "GRUA": "TOWING",
}


def normalizar_rubro(value):
    """Devuelve la clave canónica de un rubro, tolerando aliases públicos."""
    value = str(value or "").strip().upper()
    return RUBRO_ALIASES.get(value, value)


def normalizar_rubros(values):
    """Normaliza una colección conservando orden y eliminando duplicados."""
    if isinstance(values, str):
        values = [values]
    result = []
    for value in values or []:
        rubro = normalizar_rubro(value)
        if rubro and rubro not in result:
            result.append(rubro)
    return result


def rubros_estan_activos(request, rubros_requeridos):
    """Comprueba acceso a cualquier rubro activo de la empresa o soporte."""
    requeridos = set(normalizar_rubros(rubros_requeridos))
    if not requeridos or not getattr(request, "user", None) or not request.user.is_authenticated:
        return False

    if request.user.is_superuser:
        session = getattr(request, "session", {})
        soporte = session.get("modo_soporte_rubros")
        if soporte is None:
            soporte = session.get("support_rubros")
        if soporte is None and session.get("support_rubro"):
            soporte = [session.get("support_rubro")]
        # Sin selección explícita, el superusuario conserva acceso de soporte total.
        if not soporte:
            return True
        return bool(requeridos.intersection(normalizar_rubros(soporte)))

    empresa = getattr(request, "empresa", None)
    if empresa is None:
        try:
            empresa = getattr(request.user, "empresa", None)
        except Exception:
            empresa = None
    try:
        config = getattr(empresa, "config", None) if empresa else None
    except Exception:
        config = None
    activos = config.get_effective_rubros() if config and hasattr(config, "get_effective_rubros") else []
    return bool(requeridos.intersection(normalizar_rubros(activos)))


def verificar_empresa(view_func):
    """
    Decorador para verificar que el usuario solo accede a datos de su empresa
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")

        # Verificar que tiene perfil
        try:
            perfil = PerfilUsuario.objects.get(user=request.user)
        except PerfilUsuario.DoesNotExist:
            raise PermissionDenied("Usuario sin perfil de empresa")

        # Agregar perfil al request para uso en la vista
        request.perfil_usuario = perfil

        return view_func(request, *args, **kwargs)

    return wrapper


def verificar_objeto_empresa(modelo, campo_empresa="empresa"):
    """
    Decorador para verificar que un objeto pertenece a la empresa del usuario
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obtener ID del objeto desde kwargs
            objeto_id = (
                kwargs.get("pk") or kwargs.get("id") or kwargs.get(f"{modelo.__name__.lower()}_id")
            )

            if objeto_id:
                # Verificar que el objeto existe y pertenece a la empresa
                filtros = {"pk": objeto_id}
                if hasattr(modelo, campo_empresa):
                    perfil = PerfilUsuario.objects.get(user=request.user)
                    filtros[campo_empresa] = perfil.empresa

                objeto = get_object_or_404(modelo, **filtros)

                # Log de acceso
                LogAuditoria.log_accion(
                    usuario=request.user,
                    empresa=perfil.empresa,
                    accion="VIEW",
                    modelo=modelo.__name__.upper(),
                    objeto_id=objeto.pk,
                    descripcion=f"Acceso a {modelo.__name__} ID {objeto.pk}",
                    request=request,
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def log_auditoria(accion, modelo):
    """
    Decorador para log automático de auditoría
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            perfil = PerfilUsuario.objects.get(user=request.user)

            # Ejecutar la vista
            result = view_func(request, *args, **kwargs)

            # Log de la acción
            objeto_id = kwargs.get("pk") or kwargs.get("id")
            descripcion = f"{accion} {modelo}"
            if objeto_id:
                descripcion += f" ID {objeto_id}"

            LogAuditoria.log_accion(
                usuario=request.user,
                empresa=perfil.empresa,
                accion=accion,
                modelo=modelo.upper(),
                objeto_id=objeto_id,
                descripcion=descripcion,
                request=request,
            )

            return result

        return wrapper

    return decorator


class ControlEmpresa:
    """
    Mixin para controlar acceso por empresa en vistas basadas en clase
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Usuario no autenticado")

        try:
            self.perfil_usuario = PerfilUsuario.objects.get(user=request.user)
        except PerfilUsuario.DoesNotExist:
            raise PermissionDenied("Usuario sin perfil de empresa")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filtrar queryset por empresa del usuario"""
        queryset = super().get_queryset()
        if hasattr(queryset.model, "empresa"):
            return queryset.filter(empresa=self.perfil_usuario.empresa)
        return queryset


def verificar_permisos_rol(roles_permitidos):
    """
    Decorador para verificar roles específicos
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            perfil = PerfilUsuario.objects.get(user=request.user)

            if perfil.rol not in roles_permitidos and not perfil.es_superadmin:
                LogAuditoria.log_accion(
                    usuario=request.user,
                    empresa=perfil.empresa,
                    accion="VIEW",
                    modelo="ACCESO_DENEGADO",
                    descripcion=f"Intento de acceso sin permisos. Rol: {perfil.rol}",
                    request=request,
                )
                raise PermissionDenied(f"Rol {perfil.rol} no tiene permisos para esta acción")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
