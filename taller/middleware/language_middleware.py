from django.utils import translation
from django.conf import settings

class LanguageFromUrlMiddleware:
    """
    Middleware para activar el idioma basado en el parámetro 'lang' en la URL
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtener el parámetro lang de la URL
        lang = request.GET.get('lang')
        
        # Clave de sesión para el idioma (compatible con Django's LocaleMiddleware)
        language_session_key = settings.LANGUAGE_COOKIE_NAME
        
        if lang and lang in [code for code, name in settings.LANGUAGES]:
            # Activar el idioma
            translation.activate(lang)
            # Guardar en sesión para persistencia
            request.session[language_session_key] = lang
        elif language_session_key in request.session:
            # Usar el idioma guardado en sesión
            translation.activate(request.session[language_session_key])
        
        response = self.get_response(request)
        return response
