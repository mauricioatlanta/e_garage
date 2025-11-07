"""
Middleware de prueba para verificar que el idioma se establezca correctamente para USA
"""

from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class TestLanguageMiddleware(MiddlewareMixin):
    """
    Middleware de prueba para establecer idioma en inglés para URLs de USA
    """

    def process_request(self, request):
        path = request.path or ""
        print(f"🔍 TestLanguageMiddleware: Processing request for path: {path}")
        
        # Si la URL es de USA, determinar idioma basado en la ruta
        if path.startswith("/us/"):
            from django.utils import translation
            
            # Si la URL contiene /es/, establecer español
            if "/es/" in path:
                print(f"🇪🇸 TestLanguageMiddleware: Setting language to 'es' for path: {path}")
                logger.info(f"🇪🇸 TestLanguageMiddleware: Setting language to 'es' for path: {path}")
                translation.activate("es")
                request.LANGUAGE_CODE = "es"
            else:
                # Por defecto, establecer inglés para USA
                print(f"🇺🇸 TestLanguageMiddleware: Setting default language to 'en' for path: {path}")
                logger.info(f"🇺🇸 TestLanguageMiddleware: Setting default language to 'en' for path: {path}")
                translation.activate("en")
                request.LANGUAGE_CODE = "en"
        else:
            print(f"🌍 TestLanguageMiddleware: Path {path} - no language change")
            logger.info(f"🌍 TestLanguageMiddleware: Path {path} - no language change")

    def process_response(self, request, response):
        if request.path and request.path.startswith("/us/"):
            # Determinar idioma basado en la ruta
            if "/es/" in request.path:
                response.headers["Content-Language"] = "es"
                logger.info(f"🇪🇸 TestLanguageMiddleware: Set Content-Language to 'es' for {request.path}")
            else:
                response.headers["Content-Language"] = "en"
                logger.info(f"🇺🇸 TestLanguageMiddleware: Set Content-Language to 'en' for {request.path}")
        return response
