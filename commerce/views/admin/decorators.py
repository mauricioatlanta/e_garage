from functools import wraps

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def commerce_admin_required(view_func):
    """
    Exige login + empresa propietaria activa.
    Un técnico/vendedor autenticado sin empresa propietaria recibe 403.
    Más restrictivo que @login_required: filtra usuarios sin empresa asignada.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            login_url = getattr(settings, "LOGIN_URL", "/accounts/login/")
            return redirect(f"{login_url}?next={request.get_full_path()}")
        try:
            _ = request.user.empresa
        except ObjectDoesNotExist:
            return HttpResponseForbidden(
                "Acceso restringido al administrador de la empresa."
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
