from django.conf import settings

def debug_flags(request):
    """Context processor para exponer bandera de debug visible sólo a staff en DEBUG."""
    show = bool(getattr(settings, 'DEBUG', False) and getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_staff)
    return {"SHOW_DEBUG": show}
