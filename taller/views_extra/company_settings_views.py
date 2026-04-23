from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render

from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.forms.configuracion_empresa_form import ConfiguracionEmpresaForm
from taller.forms.configuracion_forms import ConfiguracionRubroForm
from taller.models import Tecnico
from taller.models.company_settings import CompanySettings
from taller.models.configuracion import ConfiguracionEmpresa
from taller.utils.pais_utils import get_configuracion_pais


@login_required(login_url=None)
def company_settings_view(request):
    empresa = request.user.empresa

    config_empresa, _ = ConfiguracionEmpresa.objects.get_or_create(
        empresa=empresa,
        defaults={"sales_tax_rate": Decimal("0")},
    )

    # Obtener o crear configuración
    try:
        config = CompanySettings.objects.get(user=request.user)
    except CompanySettings.DoesNotExist:
        country_config = get_configuracion_pais(empresa)
        config = CompanySettings.objects.create(
            user=request.user,
            company_name=empresa.nombre_taller or "Mi Empresa",
            tagline="",
            primary_color="#0d6efd",
            secondary_color="#6c757d",
            currency=country_config.get("currency", "CLP"),
            language=country_config.get("language", "es"),
            country=country_config.get("country_code", "CL"),
        )

    is_spanish = empresa.pais in {"CL", "MX", "PE", "VE", "BR"}

    if request.method == "POST":
        if "crear_tecnico" in request.POST:
            nombre = request.POST.get("nombre", "").strip()

            if nombre:
                try:
                    Tecnico.objects.create(
                        nombre=nombre,
                        empresa=empresa,
                    )
                    messages.success(request, f"Técnico '{nombre}' creado correctamente.")
                except Exception as e:
                    messages.error(request, f"Error al crear técnico: {e}")
            else:
                messages.error(request, "El nombre es obligatorio.")

    return render(
        request,
        "settings/company_settings.html",
        {
            "empresa": empresa,
            "config": config,
            "config_empresa": config_empresa,
        },
    )
