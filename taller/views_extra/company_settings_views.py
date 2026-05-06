from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)

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

    try:

        config = CompanySettings.objects.get(user=request.user)

    except CompanySettings.DoesNotExist:

        country_config = get_configuracion_pais(empresa)

        config = CompanySettings.objects.create(
            user=request.user,
            company_name=empresa.nombre_taller or "Mi Empresa",
            tagline="",
            primary_color="#00ffff",
            secondary_color="#b026ff",
            currency=country_config.get("currency", "CLP"),
        )

    if request.method == "POST":

        if "crear_tecnico" in request.POST:

            nombre = request.POST.get("nombre", "").strip()

            if nombre:

                Tecnico.objects.create(
                    nombre=nombre,
                    empresa=empresa,
                )

                messages.success(request, "Empleado creado correctamente.")

            return redirect(request.path)

        profile_form = CompanyProfileForm(
            request.POST,
            request.FILES,
            instance=config,
        )

        financial_form = FinancialSettingsForm(
            request.POST,
            instance=config,
        )

        theme_form = ThemeSettingsForm(
            request.POST,
            instance=config,
        )

        forms_valid = (
            profile_form.is_valid() and financial_form.is_valid() and theme_form.is_valid()
        )

        if forms_valid:

            profile_form.save()
            financial_form.save()
            theme_form.save()

            config.refresh_from_db()

            config_empresa.nombre_publico = config.company_name
            config_empresa.tagline = config.tagline
            config_empresa.telefono = config.phone
            config_empresa.email_contacto = config.email
            config_empresa.sitio_web = config.website
            config_empresa.direccion = config.address
            config_empresa.moneda = config.currency
            config_empresa.tasa_impuesto = config.tax_rate
            config_empresa.aplicar_impuesto_por_defecto = config.apply_tax_by_default

            config_empresa.brand_color = config.primary_color

            config_empresa.dividir_por_tecnico = config.separate_by_technician

            if config.logo:
                config_empresa.logo = config.logo

            config_empresa.save()

            messages.success(request, "Configuracion guardada correctamente.")

            return redirect(request.path)

        messages.error(request, "Error al guardar configuracion.")

    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    return render(
        request,
        "taller/company/settings.html",
        {
            "empresa": empresa,
            "tecnicos": tecnicos,
            "config": config,
            "config_empresa": config_empresa,
        },
    )
