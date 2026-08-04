from django.template.response import TemplateResponse
from django.utils.translation import get_language

from taller.auth.decorators import country_login_required
from taller.services.centro_operaciones_service import CentroOperacionesService
from taller.utils.empresa import get_or_create_empresa
from taller.utils.templates import select_country_lang_template


@country_login_required
def dashboard_centro_operaciones(request):
    empresa = get_or_create_empresa(request)
    context = CentroOperacionesService.build_context(empresa)
    template_name = select_country_lang_template(
        "dashboard/centro_operaciones.html",
        getattr(empresa, "pais", "cl").lower(),
        get_language(),
    )
    return TemplateResponse(request, template_name, context)


@country_login_required
def dashboard_centro_operaciones_espacial(request):
    empresa = get_or_create_empresa(request)
    context = CentroOperacionesService.build_context(
        empresa, user=request.user, include_charts=True
    )
    context["es_dashboard_espacial"] = True

    if (hasattr(empresa, "pais") and empresa.pais == "US") or request.path.startswith("/us/"):
        template_name = "us/en/dashboard/centro_operaciones_espacial.html"
        context["use_usa_base"] = True
    else:
        template_name = select_country_lang_template(
            "dashboard/centro_operaciones_espacial.html",
            getattr(empresa, "pais", "cl").lower(),
            get_language(),
        )

    return TemplateResponse(request, template_name, context)
