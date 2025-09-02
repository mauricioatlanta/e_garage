from django.template.loader import select_template
from django.template.response import TemplateResponse
from django.utils.translation import get_language

def select_country_lang_template(base_path: str, country: str, lang: str, fallback_lang="es"):
    country = (country or "CL").lower()
    lang = (lang or fallback_lang).lower()
    candidates = [
        f"taller/{country}/{lang}/{base_path}",
        f"taller/{country}/{base_path}",
        f"taller/common/{lang}/{base_path}",
        f"taller/common/{base_path}",
    ]
    return select_template(candidates)

class CountryLangTemplateMixin:
    base_template_name = None  # e.g. "documentos/crear_documento.html"
    response_class = TemplateResponse

    def render_country_lang(self, request, context):
        empresa = getattr(request.user, "empresa", None)
        country = getattr(empresa, "pais", "CL") if empresa else "CL"
        lang = get_language() or "es"
        tpl = select_country_lang_template(self.base_template_name, country, lang)
        return self.response_class(request=request, template=tpl.template.name, context=context)