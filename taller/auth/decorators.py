from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from taller.utils.country import prefix_from_path


def _get_login_url() -> str:
    # No acceder a settings a nivel de módulo (permite importar sin Django inicializado)
    return getattr(settings, "LOGIN_URL", "/accounts/login/")


def _country_from_request(request) -> str | None:
    """
    Intenta inferir país desde:
    - request.country / request.country_code (middleware)
    - prefijo de URL (/us/, /cl/, /ar/, etc.)
    """
    c = getattr(request, "country", None) or getattr(request, "country_code", None)
    if isinstance(c, str) and c:
        return c.upper()

    path = (getattr(request, "path", "") or "").lower()
    if path.startswith("/us/"):
        return "US"
    if path.startswith("/cl/"):
        return "CL"
    if path.startswith("/ar/"):
        return "AR"
    if path.startswith("/br/"):
        return "BR"
    if path.startswith("/pe/"):
        return "PE"
    if path.startswith("/mx/"):
        return "MX"
    if path.startswith("/uy/"):
        return "UY"
    return None


_NS_MAP = {
    "CL": "chile",
    "US": "usa",
    "AR": "argentina",
    "BR": "brasil",
    "PE": "peru",
    "MX": "mexico",
    "UY": "uruguay",
}


def country_login_required(view_func=None, *, country: str | None = None):
    """
    Decorador de compatibilidad:
    - Exige login
    - Si `country` se especifica, valida que coincida con el país del request.
    - Redirige al login correcto por país (usa namespaces si existen).
    """

    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kwargs):
            # 1) Requiere autenticación
            if not request.user.is_authenticated:
                c = _country_from_request(request)
                next_url = request.get_full_path()

                if not url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    next_url = "/"

                # Si el path tiene prefijo país+idioma (/us/en/, /cl/es/), preservar en login y next
                prefix = prefix_from_path(request.path)
                if "/" in prefix:
                    login_url = f"/{prefix}/accounts/login/"
                    return redirect(f"{login_url}?next={next_url}")

                ns = _NS_MAP.get(c or "", "")
                if ns:
                    try:
                        login_url = reverse(f"{ns}:account_login")
                        return redirect(f"{login_url}?next={next_url}")
                    except Exception:
                        pass

                login_url = _get_login_url()
                return redirect(f"{login_url}?next={next_url}")

            # 2) Validación opcional de país
            if country:
                c = _country_from_request(request)
                if c and c != country.upper():
                    ns = _NS_MAP.get(c or "", "")
                    if ns:
                        try:
                            return redirect(reverse(f"{ns}:home"))
                        except Exception:
                            pass
                    return redirect("/")

            return fn(request, *args, **kwargs)

        return _wrapped

    return decorator(view_func) if view_func else decorator


def login_required_default(view_func):
    """
    Compatibilidad: mismo comportamiento que antes pero sin leer settings al importar.
    Usa _get_login_url() (lazy) cuando se aplica el decorador.
    """
    from django.contrib.auth.decorators import login_required

    return login_required(login_url=_get_login_url())(view_func)
