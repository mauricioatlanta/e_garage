from functools import wraps
from django.contrib.auth.decorators import login_required


def country_login_required(view_func=None, country_code=None):
    """
    Decorador tolerante: exige login.
    Soporta:
      @country_login_required
      @country_login_required()
      @country_login_required("CL")
    """
    # Caso 1: usado como @country_login_required (sin paréntesis)
    if callable(view_func) and country_code is None:
        return country_login_required()(view_func)

    # Caso 2: usado como @country_login_required("CL")
    if isinstance(view_func, str) and country_code is None:
        country_code = view_func
        view_func = None

    def decorator(fn):
        @login_required
        @wraps(fn)
        def _wrapped(request, *args, **kwargs):
            # Aquí podrías validar country_code si quisieras.
            return fn(request, *args, **kwargs)

        return _wrapped

    return decorator if view_func is None else decorator(view_func)
