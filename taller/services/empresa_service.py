def get_empresa_safe(request):
    if not request.user.is_authenticated:
        return None
    try:
        return request.user.empresa
    except Exception:
        return None
