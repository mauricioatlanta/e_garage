from django.template.response import TemplateResponse
from django.utils.translation import get_language
from .utils.templates import select_country_lang_template
from django.views.generic import TemplateView
from taller.utils.templates import country_lang_template

class CountryLangTemplateMixin:
    """
    Mixin para vistas que necesitan selección automática de templates por país e idioma.
    
    Requiere que la vista tenga:
    - self.request.COUNTRY o self.request.user.empresa.pais
    - self.request.LANGUAGE_CODE
    """
    
    def get_template_names(self):
        """
        Retorna lista de nombres de templates con fallbacks por país e idioma.
        """
        # Obtener país del request o del usuario
        country = getattr(self.request, 'COUNTRY', None)
        if not country and hasattr(self.request.user, 'empresa'):
            country = getattr(self.request.user.empresa, 'pais', 'cl')
        
        # Obtener idioma del request
        lang = getattr(self.request, 'LANGUAGE_CODE', 'es')[:2]
        
        # Obtener la ruta base del template
        template_path = self.get_template_path()
        
        # Usar el helper de selección de templates
        template = country_lang_template(template_path, country, lang)
        
        return [template.template.name]
    
    def get_template_path(self):
        """
        Retorna la ruta del template sin país/idioma.
        Debe ser implementado por las subclases.
        """
        raise NotImplementedError("Subclases deben implementar get_template_path()")
