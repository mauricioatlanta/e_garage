from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.translation import gettext as _
from django.conf import settings

def set_language_from_url(request):
    """
    Cambia el idioma basado en el parámetro 'lang' en la URL
    """
    lang = request.GET.get('lang')
    if lang and lang in [code for code, name in settings.LANGUAGES]:
        # Activar el idioma
        translation.activate(lang)
        # Guardar en sesión para persistencia
        request.session[translation.LANGUAGE_SESSION_KEY] = lang
        
    # Obtener la URL actual sin el parámetro lang
    next_url = request.get_full_path()
    if '?lang=' in next_url:
        next_url = next_url.split('?lang=')[0]
        if '&' in request.get_full_path():
            # Mantener otros parámetros GET
            other_params = request.get_full_path().split('?')[1]
            other_params = '&'.join([p for p in other_params.split('&') if not p.startswith('lang=')])
            if other_params:
                next_url += '?' + other_params
    
    return HttpResponseRedirect(next_url)
