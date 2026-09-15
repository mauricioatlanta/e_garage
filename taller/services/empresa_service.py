from taller.utils.empresa import get_user_empresa_safe


def get_empresa_safe(request):
    empresa = getattr(request, "empresa", None)
    if empresa is not None:
        return empresa

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None

    return get_user_empresa_safe(user)
