from django.template.response import TemplateResponse
from django.utils.translation import get_language

from .utils.templates import select_country_lang_template


class CountryLangTemplateMixin:
    """
    Mixin para vistas que necesitan resolución automática de templates
    basada en país e idioma del usuario.
    """

    base_template_name = None  # ej: "documentos/crear_documento.html"
    response_class = TemplateResponse

    def get_template_names(self):
        """
        Sobrescribe el método estándar de Django para resolución de templates
        basada en país e idioma.
        """
        # Si hay template_name definido, usarlo como base_template_name
        if hasattr(self, "template_name") and self.template_name:
            base_template = self.template_name
        elif self.base_template_name:
            base_template = self.base_template_name
        else:
            # Usar el comportamiento estándar de Django
            return super().get_template_names()

        # Obtener datos de país e idioma
        request = getattr(self, "request", None)
        if not request:
            # Fallback a template estándar si no hay request
            return [f"taller/{base_template}"]

        empresa = (
            getattr(request.user, "empresa", None)
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        )
        country = getattr(empresa, "pais", "CL") if empresa else "CL"
        lang = get_language() or "es"

        # Seleccionar template apropiado
        try:
            template_name = select_country_lang_template(base_template, country, lang)
            return [template_name]
        except Exception as e:
            # Fallback a template base si hay problemas
            return [f"taller/common/{base_template}", f"taller/{base_template}"]

    def render_country_lang(self, request, context):
        """
        Renderiza usando template específico por país e idioma.

        Resuelve automáticamente el template usando la jerarquía:
        1. taller/{country}/{lang}/{base_template_name}
        2. taller/{country}/{base_template_name}
        3. taller/common/{lang}/{base_template_name}
        4. taller/common/{base_template_name}
        """
        if not self.base_template_name:
            raise ValueError("base_template_name debe estar definido en la vista")

        # Obtener datos de país e idioma
        empresa = (
            getattr(request.user, "empresa", None)
            if hasattr(request, "user") and request.user.is_authenticated
            else None
        )
        country = getattr(empresa, "pais", "CL") if empresa else "CL"
        lang = get_language() or "es"

        # Seleccionar template apropiado
        try:
            template_name = select_country_lang_template(
                self.base_template_name, country, lang
            )
        except Exception as e:
            # Fallback a template base si hay problemas
            template_name = f"taller/common/{self.base_template_name}"

        return self.response_class(
            request=request, template=template_name, context=context
        )
