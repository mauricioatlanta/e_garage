"""
Login country-aware: /accounts/login/ (sin prefijo) → /<cc>/accounts/login/ o /<cc>/<lang>/accounts/login/.

- Opción A: next=/us/centro-operaciones-espacial/ → /us/accounts/login/?next=...
- Opción B: next=/us/en/... → /us/en/accounts/login/?next=...; next=/us/es/... → /us/es/accounts/login/?next=...
  Igual para /cl/es/... → /cl/es/accounts/login/.

Debe ir después de SessionMiddleware.
"""

from django.shortcuts import redirect

# Códigos de país de 2 letras soportados en path (/us/, /cl/, ...)
_PATH_COUNTRY_CODES = ("us", "cl", "mx", "co", "ec", "pe", "ve", "br", "uy", "ar")
# Idiomas en path para login país+idioma (Opción B)
_PATH_LANGS = ("en", "es")
# Idioma por defecto por país (evita redirigir a /cc/accounts/login/ que hace redirect de vuelta → loop)
_DEFAULT_LANG_BY_CC = {
    "us": "en",
    "cl": "es",
    "mx": "es",
    "co": "es",
    "ec": "es",
    "pe": "es",
    "ve": "es",
    "br": "pt",
    "uy": "es",
    "ar": "es",
}


def _country_from_login_request(request):
    """
    Determina el país para /accounts/login/ sin prefijo.
    Orden: next (path del next) → from= → default CL.
    No usar sesión: genera el bug de mostrar login USA a usuarios CL con sesión obsoleta.
    """
    next_url = (request.GET.get("next") or "").strip()
    if next_url.startswith("/") and len(next_url) >= 4 and next_url[3] == "/":
        cc = next_url[1:3].lower()
        if cc in _PATH_COUNTRY_CODES:
            return cc

    from_param = (request.GET.get("from") or "").strip().lower()
    if from_param in _PATH_COUNTRY_CODES:
        return from_param
    if from_param in ("usa",):
        return "us"

    return "cl"


def _login_path_with_lang(cc: str, next_url: str) -> str:
    """
    Devuelve la ruta que SIRVE el login (/<cc>/<lang>/accounts/login/), no la que redirige.
    /cl/accounts/login/ en la app redirige a /accounts/login/ → loop. Por eso usamos siempre
    /cc/lang/accounts/login/ (p. ej. /cl/es/accounts/login/) que allauth sirve bajo cl/es/.
    """
    next_url = (next_url or "").strip()
    default_lang = _DEFAULT_LANG_BY_CC.get(cc, "es")
    if not next_url.startswith("/") or len(next_url) < 6:
        return f"/{cc}/{default_lang}/accounts/login/"
    # next = "/us/en/..." o "/cl/es/..." → parts[0]=cc, parts[1]=lang
    parts = next_url.lstrip("/").split("/")
    if len(parts) >= 2 and parts[0] == cc and parts[1] in _PATH_LANGS:
        return f"/{cc}/{parts[1]}/accounts/login/"
    return f"/{cc}/{default_lang}/accounts/login/"


class ForceAccountsToCLMiddleware:
    """
    Redirige TODAS las rutas /accounts/* → /<cc>/<lang>/accounts/* para GET/HEAD.
    Ejemplos:
    - /accounts/login/ → /cl/es/accounts/login/
    - /accounts/password/reset/ → /cl/es/accounts/password/reset/
    - /accounts/signup/ → /us/en/accounts/signup/

    No redirige a /cc/accounts/* porque esas rutas redirigen de vuelta → ERR_TOO_MANY_REDIRECTS.
    IMPORTANTÍSIMO: NO tocar POST, porque rompe el login/signup real.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip("/")

        # Solo redirigir navegación (GET/HEAD). Nunca POST.
        if request.method in ("GET", "HEAD") and path.startswith("/accounts/"):
            # Verificar que NO tenga ya prefijo de país
            if not any(path.startswith(f"/{cc}/") for cc in _PATH_COUNTRY_CODES):
                cc = _country_from_login_request(request)
                next_url = (request.GET.get("next") or "").strip()
                default_lang = _DEFAULT_LANG_BY_CC.get(cc, "es")

                # Determinar idioma del next_url si existe
                lang = default_lang
                if next_url.startswith("/") and len(next_url) >= 6:
                    parts = next_url.lstrip("/").split("/")
                    if len(parts) >= 2 and parts[0] == cc and parts[1] in _PATH_LANGS:
                        lang = parts[1]

                # Construir nueva ruta: /<cc>/<lang>/accounts/...
                new_path = f"/{cc}/{lang}{path}"

                # Preservar query params excepto 'country'
                params = request.GET.copy()
                params.pop("country", None)
                url = f"{new_path}?{params.urlencode()}" if params else new_path
                return redirect(url)

        return self.get_response(request)
