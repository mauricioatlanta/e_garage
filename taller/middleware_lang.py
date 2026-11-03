from django.utils import translation

class RegionalLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # 1. Determinar idioma
        if "/es/" in path or path.startswith("/us/es/") or path.startswith("/cl/es/"):
            lang = "es"
        elif "/en/" in path or path.startswith("/us/en/"):
            lang = "en"
        else:
            lang = request.session.get("django_language") or request.COOKIES.get("django_language") or "es"

        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        if hasattr(request, "session"):
            request.session["django_language"] = lang

        # 2. Excepción para Superusuario en Modo Soporte
        if hasattr(request, "user") and request.user.is_authenticated and request.user.is_superuser:
            request.session["modo_soporte_activo"] = True
            if path.startswith("/us/"):
                request.session["support_country"] = "us"
                request.session["modo_soporte_pais"] = "us"

        with translation.override(lang):
            response = self.get_response(request)

        if response is not None and hasattr(response, "set_cookie"):
            response.set_cookie("django_language", lang, max_age=365*24*60*60, domain=".egarage.cl", path="/")
        return response
