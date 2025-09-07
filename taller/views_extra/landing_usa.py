from django.shortcuts import render
from django.utils.translation import activate
from django.utils.translation import gettext as _
from django.views.generic import TemplateView


class LandingUSAView(TemplateView):
    template_name = "us/en/landing_usa.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "eGarage USA - Professional Automotive Management",
                "meta_description": "The all-in-one platform for auto repair shops, parts stores, tire shops and car washes in the United States. Professional automotive management system.",
                "is_usa_market": True,
            }
        )
        return context


def landing_usa(request):
    """
    Landing page optimizada para USA con diseño futurista
    """
    # Handle language switching
    lang = request.GET.get("lang", "en")
    if lang in ["en", "es"]:
        activate(lang)
        request.session["django_language"] = lang

    context = {
        "page_title": "eGarage USA - Professional Automotive Management",
        "meta_description": "The all-in-one platform for auto repair shops, parts stores, tire shops and car washes in the United States.",
        "is_usa_market": True,
        "seo_title": "eGarage USA | Professional Automotive Management System",
        "seo_description": "Try eGarage, the most advanced automotive management platform for the US. Professional features, sales tax compliance, and modern design.",
        "og_image": "/static/img/og_usa_landing.png",
        "current_language": lang,
    }
    return render(request, "us/en/landing_usa_enhanced.html", context)
