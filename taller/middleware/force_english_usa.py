from django.utils import translation


class ForceEnglishUSA:
    """
    Middleware que fuerza el idioma inglés en la ruta /usa/ ignorando cookies previas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/usa/") or request.path == "/usa/":
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        response = self.get_response(request)
        return response
