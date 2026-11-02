from django.utils import translation

class RegionalLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if "/en/" in path or path.startswith("/us/en/"):
            lang = "en"
        elif "/es/" in path or path.startswith("/cl/es/") or path.startswith("/us/es/"):
            lang = "es"
        else:
            lang = "en" if request.session.get("django_language") == "en" else "es"

        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        if hasattr(request, "session"):
            request.session["django_language"] = lang

        with translation.override(lang):
            response = self.get_response(request)

        response.set_cookie("django_language", lang, max_age=365*24*60*60)
        return response
