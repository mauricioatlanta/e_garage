"""
Middleware para configurar idioma automáticamente según el país
Chile: español fijo
USA: selector ES/EN (guarda en sesión)
"""

from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
import re


class CountryLanguageMiddleware(MiddlewareMixin):
    """
    Middleware que configura el idioma automáticamente según el país
    """
    
    COUNTRY_LANGUAGE_MAP = {
        'cl': 'es',  # Chile: español fijo
        'us': None,  # USA: usar selector de idioma
    }
    
    def process_request(self, request):
        """Configura el idioma según el país detectado en la URL"""
        path = request.path.lower()
        
        # Detectar país desde URL
        country = self.get_country_from_path(path)
        
        # Agregar el país detectado al request para uso en templates
        if country == 'cl':
            request.current_country = 'chile'
        elif country == 'us':
            request.current_country = 'usa'
        else:
            request.current_country = None
        
        if country == 'cl':
            # Chile: forzar español
            translation.activate('es')
            request.LANGUAGE_CODE = 'es'
            
        elif country == 'us':
            # USA: usar selector de idioma (sesión/cookie)
            # Si no hay idioma guardado en sesión, usar inglés por defecto
            user_language = request.session.get('django_language', 'en')
            
            # Permitir cambio vía parámetro ?lang=
            if 'lang' in request.GET:
                requested_lang = request.GET['lang']
                if requested_lang in ['es', 'en']:
                    user_language = requested_lang
                    request.session['django_language'] = user_language
            
            translation.activate(user_language)
            request.LANGUAGE_CODE = user_language
        
        else:
            # Rutas sin país: usar configuración por defecto
            translation.activate('en')
            request.LANGUAGE_CODE = 'en'
    
    def get_country_from_path(self, path):
        """Extrae el código de país de la URL"""
        # Buscar /cl/ o /us/ al inicio de la ruta
        match = re.match(r'^/([a-z]{2})/', path)
        if match:
            return match.group(1)
        return None
    
    def process_response(self, request, response):
        """Limpia la configuración de idioma"""
        translation.deactivate()
        return response
