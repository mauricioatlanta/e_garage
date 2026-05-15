# taller/middleware/login_country_fix.py
# Regla: país en path ✅, país en GET ❌. No añadir ni preservar country= en querystring.
# Reescribe redirects a /accounts/login/ → /<cc>/accounts/login/ o /<cc>/<lang>/accounts/login/
# para que el primer redirect ya sea country-aware (evita loops y rebotes CL/US).

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

_PATH_LANGS = ("en", "es")
_PATH_COUNTRY_CODES = ("us", "cl", "mx", "co", "ec", "pe", "ve", "br", "uy", "ar")


def _country_from_path(path: str) -> str | None:
    if not path or len(path) < 4:
        return None
    if path[0] == "/" and path[3] == "/":
        cc = path[1:3].lower()
        if cc.isalpha():
            return cc
    return None


def _cc_lang_from_path(path: str) -> tuple[str | None, str | None]:
    """
    Extrae (cc, lang) del path, ej: /cl/es/settings/ → (cl, es), /us/centro/ → (us, None).
    """
    path = (path or "").strip().lower().lstrip("/")
    parts = path.split("/")
    if len(parts) < 1:
        return (None, None)
    cc = parts[0] if parts[0] in _PATH_COUNTRY_CODES else None
    if not cc or len(parts) < 2:
        return (cc, None)
    lang = parts[1] if parts[1] in _PATH_LANGS else None
    return (cc, lang)


def _cc_lang_from_next_url(location: str) -> tuple[str | None, str | None]:
    """Extrae (cc, lang) del parámetro next= en la URL de Location."""
    parsed = urlparse(location)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    next_url = (qs.get("next") or [""])[0]
    if not next_url or not next_url.startswith("/"):
        return (None, None)
    return _cc_lang_from_path(next_url)


class FixLoginCountryRedirectMiddleware:
    """
    Si Django redirige a /accounts/login/ (sin prefijo), reescribe el Location
    a /<cc>/accounts/login/ o /<cc>/<lang>/accounts/login/ usando el path del request
    o el parámetro next=, para que el redirect sea country-aware desde el primer 302.
    DESHABILITADO para /accounts/*: allauth debe generar siempre /accounts/* sin prefijo
    de país; el contexto de país se maneja por sesión, middleware y country_aware_login.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _rewrite_login_location(self, location: str, cc: str, lang: str | None = None) -> str:
        """Reemplaza path por /cc/accounts/login/ o /cc/lang/accounts/login/ y quita country= del query."""
        parsed = urlparse(location)
        path = parsed.path
        if path.startswith("/accounts/login/"):
            if lang:
                new_path = f"/{cc}/{lang}/accounts/login/"
            else:
                new_path = f"/{cc}/accounts/login/"
        elif path.startswith(f"/{cc}/accounts/login/"):
            if lang and not path.startswith(f"/{cc}/{lang}/"):
                new_path = f"/{cc}/{lang}/accounts/login/"
            else:
                return location
        else:
            return location
        qs = parse_qs(parsed.query, keep_blank_values=True)
        qs.pop("country", None)
        new_query = urlencode(qs, doseq=True)
        if not parsed.scheme and not parsed.netloc:
            return new_path + ("?" + new_query if new_query else "")
        return urlunparse(
            (parsed.scheme, parsed.netloc, new_path, parsed.params, new_query, parsed.fragment)
        )

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code not in (301, 302, 303, 307, 308):
            return response

        location = response.get("Location", "")
        if not location:
            return response

        # No reescribir /accounts/*: allauth debe generar siempre /accounts/* sin prefijo
        # de país para evitar loops, 500 y pérdida de contexto en password reset
        if location.startswith("/accounts/"):
            return response

        # Derivar cc (y opcionalmente lang) del path del request o del next= en Location
        req_cc, req_lang = _cc_lang_from_path(request.path)
        if not req_cc:
            loc_cc, loc_lang = _cc_lang_from_next_url(location)
            req_cc, req_lang = loc_cc or req_cc, loc_lang or req_lang
        if not req_cc:
            return response

        # Reescribir /accounts/login/ → /cc/accounts/login/ o /cc/lang/accounts/login/
        if location.startswith("/accounts/login/"):
            response["Location"] = self._rewrite_login_location(location, req_cc, req_lang)
            return response

        # Reescribir /cl/accounts/login/ a otro país o añadir lang si tenemos request con lang
        if location.startswith("/cl/accounts/login/") and req_cc != "cl":
            response["Location"] = self._rewrite_login_location(location, req_cc, req_lang)
            return response

        # Si request era /cl/es/... y Location es /cl/accounts/login/, subir a /cl/es/accounts/login/
        if req_lang and location.startswith(f"/{req_cc}/accounts/login/"):
            response["Location"] = self._rewrite_login_location(location, req_cc, req_lang)
            return response

        return response
