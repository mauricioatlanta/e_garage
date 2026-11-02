from taller.utils.empresa import get_user_empresa_safe


def get_empresa(request):
    """Devuelve la empresa activa estandarizada en el request.

    Preferencia:
    1) request.empresa inyectada por middleware
    2) fallback seguro a request.user.empresa para compatibilidad
    """
    empresa = getattr(request, "empresa", None)
    if empresa is not None:
        return empresa

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None

    return get_user_empresa_safe(user)
