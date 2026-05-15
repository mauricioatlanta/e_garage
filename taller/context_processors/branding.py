from taller.utils.empresa import get_user_empresa_safe


def branding(request):
    empresa = getattr(request, "empresa", None)
    if empresa is None:
        user = getattr(request, "user", None)
        empresa = get_user_empresa_safe(user)

    return {
        "branding_color": getattr(empresa, "color", "#06b6d4") if empresa else "#06b6d4",
        "branding_logo": getattr(empresa, "logo", None) if empresa else None,
    }
