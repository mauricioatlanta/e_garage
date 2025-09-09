from django.shortcuts import render
from django.utils.translation import activate
from django.views.generic import TemplateView


class LandingChileView(TemplateView):
    template_name = (
        "us/en/landing_usa.html"  # Usar el mismo template pero con traducciones
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "eGarage Chile - Gestión Profesional Automotriz",
                "meta_description": "La plataforma integral para talleres mecánicos, tiendas de repuestos, talleres de neumáticos y autolavados en Chile. Sistema profesional de gestión automotriz.",
                "is_chile_market": True,
            }
        )
        return context


def landing_chile(request):
    """
    Landing page optimizada para Chile con diseño futurista
    Chile siempre en español - sin opción de cambio de idioma
    """
    # Chile siempre en español - sin opción de cambio
    activate("es")
    request.session["django_language"] = "es"

    context = {
        "page_title": "eGarage Chile - Gestión Profesional Automotriz",
        "meta_description": "La plataforma integral para talleres mecánicos, tiendas de repuestos, talleres de neumáticos y autolavados en Chile.",
        "is_chile_market": True,
        "seo_title": "eGarage Chile | Sistema Profesional de Gestión Automotriz",
        "seo_description": "Prueba eGarage, la plataforma más avanzada de gestión automotriz para Chile. Características profesionales, cumplimiento tributario y diseño moderno.",
        "og_image": "/static/img/og_chile_landing.png",
        "current_language": "es",  # Siempre español para Chile
        "spanish_only": True,  # Flag para ocultar selector de idioma
    }
    return render(request, "public/landing_chile.html", context)
