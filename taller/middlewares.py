# taller/middlewares.py
"""
Middleware personalizado para activación automática de idioma basado en:
1. Preferencia explícita del usuario (si existe)
2. País de la empresa (Chile → es, USA → en)
3. Fallback a español por defecto
"""
from django.utils import translation


def activate_language(get_response):
    """
    Middleware para activar idioma automáticamente según país/usuario
    Se ejecuta en cada request antes del procesamiento de la vista
    """
    def middleware(request):
        lang = None
        user = getattr(request, 'user', None)

        # 1) Preferencia explícita del usuario (si la tienes en el futuro)
        if (user and user.is_authenticated and 
            hasattr(user, 'preferencia_idioma') and 
            user.preferencia_idioma):
            lang = user.preferencia_idioma

        # 2) Fallback por empresa/país  
        if not lang and user and user.is_authenticated:
            try:
                empresa = getattr(user, 'empresa', None)
                if empresa:
                    country = getattr(empresa, 'pais', None)
                    if country == 'CL':
                        lang = 'es'  # Chile → Español
                    elif country == 'US':
                        lang = 'en'  # USA → English
            except AttributeError:
                pass  # Si no tiene empresa, continuar con fallback

        # 3) Fallback global
        if not lang:
            lang = 'es'  # Español por defecto

        # Activar idioma para este request
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        
        # Procesar request
        response = get_response(request)
        
        # Limpiar estado de idioma
        translation.deactivate()
        
        return response
    
    return middleware
