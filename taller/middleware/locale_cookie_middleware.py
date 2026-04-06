from __future__ import annotations


class LocaleCookieMiddleware:
    """
    Persiste la preferencia de país e idioma a partir del prefijo canónico en la URL.
    """

    COOKIE_MAX_AGE = 60 * 60 * 24 * 180

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        path = (request.path or "").strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            country = parts[0].upper()
            lang = parts[1].lower()
            if country in {"CL", "US", "PE", "BR"} and lang in {"es", "en", "pt"}:
                response.set_cookie(
                    "eg_country",
                    country,
                    max_age=self.COOKIE_MAX_AGE,
                    samesite="Lax",
                    secure=True,
                )
                response.set_cookie(
                    "eg_lang",
                    lang,
                    max_age=self.COOKIE_MAX_AGE,
                    samesite="Lax",
                    secure=True,
                )

        return response
