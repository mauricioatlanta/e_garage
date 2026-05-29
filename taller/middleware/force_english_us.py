from django.utils import translation


class ForceEnglishUS:
    """
    Middleware que fuerza el idioma inglés en las rutas /us/ ignorando cookies previas.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/us/"):
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        response = self.get_response(request)
        return response
