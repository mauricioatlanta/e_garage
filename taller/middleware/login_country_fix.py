# taller/middleware/login_country_fix.py


def _country_from_path(path: str) -> str | None:
    if not path or len(path) < 4:
        return None
    if path[0] == "/" and path[3] == "/":
        cc = path[1:3].lower()
        if cc.isalpha():
            return cc
    return None


class FixLoginCountryRedirectMiddleware:
    """
    Si el request viene con prefijo país (/us/..., /cl/...)
    y Django redirige a /accounts/login/ (o /cl/accounts/login/),
    reescribe a /<pais>/accounts/login/ preservando querystring.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code not in (301, 302, 303, 307, 308):
            return response

        location = response.get("Location", "")
        if not location:
            return response

        req_cc = _country_from_path(request.path)
        if not req_cc:
            return response

        # Caso 1: /accounts/login/...
        if location.startswith("/accounts/login/"):
            response["Location"] = location.replace(
                "/accounts/login/",
                f"/{req_cc}/accounts/login/",
                1,
            )
            return response

        # Caso 2: /cl/accounts/login/... (legacy)
        if location.startswith("/cl/accounts/login/") and req_cc != "cl":
            response["Location"] = location.replace(
                "/cl/accounts/login/",
                f"/{req_cc}/accounts/login/",
                1,
            )
            return response

        return response
