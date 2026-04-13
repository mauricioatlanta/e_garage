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
from taller.utils.empresa import get_or_create_empresa
from taller.utils.pais_utils import get_configuracion_pais


@login_required(login_url=None)
def company_settings_view(request):
    empresa = get_user_empresa_safe(request.user)
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
            currency=country_config.get("moneda", "CLP"),
        )

    is_spanish = empresa.pais in {"CL", "MX", "PE", "VE", "BR"}

    if request.method == "POST":
        # Manejar creación de técnico
        if "crear_tecnico" in request.POST:
            nombre = request.POST.get("nombre", "").strip()
            telefono = request.POST.get("telefono", "").strip()
            direccion = request.POST.get("direccion", "").strip()

            if nombre:
                try:
                    Tecnico.objects.create(
                        nombre=nombre,
                        telefono=telefono,
                        direccion=direccion,
                        empresa=empresa,
                        activo=True,
                    )
                    if is_spanish:
                        messages.success(request, f"✅ Técnico '{nombre}' creado exitosamente.")
                    else:
                        messages.success(request, f"✅ Technician '{nombre}' created successfully.")
                except Exception as e:
                    if is_spanish:
                        messages.error(request, f"❌ Error al crear técnico: {str(e)}")
                    else:
                        messages.error(request, f"❌ Error creating technician: {str(e)}")
            else:
                if is_spanish:
                    messages.error(request, "❌ El nombre del técnico es obligatorio.")
                else:
                    messages.error(request, "❌ Technician name is required.")
            return redirect(request.path)

        # Manejar toggle de técnico
        elif "toggle_tecnico" in request.POST:
            tecnico_id = request.POST.get("toggle_tecnico")
            try:
                tecnico = Tecnico.objects.get(id=tecnico_id, empresa=empresa)
                tecnico.activo = not tecnico.activo
                tecnico.save()
                estado = "activado" if tecnico.activo else "desactivado"
                estado_en = "activated" if tecnico.activo else "deactivated"
                if is_spanish:
                    messages.success(
                        request, f"✅ Técnico '{tecnico.nombre}' {estado} exitosamente."
                    )
                else:
                    messages.success(
                        request, f"✅ Technician '{tecnico.nombre}' {estado_en} successfully."
                    )
            except Tecnico.DoesNotExist:
                if is_spanish:
                    messages.error(request, "❌ Técnico no encontrado.")
                else:
                    messages.error(request, "❌ Technician not found.")
            except Exception as e:
                if is_spanish:
                    messages.error(request, f"❌ Error al actualizar técnico: {str(e)}")
                else:
                    messages.error(request, f"❌ Error updating technician: {str(e)}")
            return redirect(request.path)

        # Manejar formularios de configuración
        else:
            section = request.POST.get("section", "profile")
            rubro_form = ConfiguracionRubroForm(
                request.POST if section == "modules" else None,
                instance=config_empresa,
                request=request,
            )

            # Crear formularios con datos POST
            profile_form = CompanyProfileForm(
                request.POST or None, request.FILES or None, instance=config
            )
            empresa_form = ConfiguracionEmpresaForm(
                request.POST or None,
                request.FILES or None,
                instance=config_empresa,
            )
            financial_form = FinancialSettingsForm(request.POST or None, instance=config)
            theme_form = ThemeSettingsForm(request.POST or None, instance=config)

            # Validar y guardar según la sección
            if section == "profile":
                ok_profile = profile_form.is_valid()
                ok_empresa = empresa_form.is_valid()

                if ok_profile and ok_empresa:
                    profile_form.save()

                    # ?? SYNC EMPRESA (FIX CRITICO)
                    empresa.nombre_taller = profile_form.cleaned_data.get(
                        "company_name", empresa.nombre_taller
                    )
                    empresa.save(update_fields=["nombre_taller"])

                    # ?? SYNC EMPRESA (FIX CRITICO)
                    empresa.nombre_taller = profile_form.cleaned_data.get(
                        "company_name", empresa.nombre_taller
                    )
                    empresa.save(update_fields=["nombre_taller"])
                    empresa_form.save()  # <-- aquí se guarda logo en ConfiguracionEmpresa
                    cache.delete(f"company_branding_{request.user.id}")

                    messages.success(
                        request,
                        (
                            "✅ Información de empresa guardada exitosamente."
                            if is_spanish
                            else "✅ Company information saved."
                        ),
                    )
                    return redirect(request.path)
                else:
                    messages.error(
                        request,
                        (
                            "❌ Corrige los errores en Información de Empresa."
                            if is_spanish
                            else "❌ Please fix the errors in Company Information."
                        ),
                    )
            elif section == "financial":
                if financial_form.is_valid():
                    financial_form.save()
                    if is_spanish:
                        messages.success(
                            request, "✅ Configuración financiera guardada exitosamente."
                        )
                    else:
                        messages.success(request, "✅ Financial settings saved.")
                    return redirect(request.path)
                else:
                    if is_spanish:
                        messages.error(
                            request, "❌ Por favor corrija los errores en Impuestos y Finanzas."
                        )
                    else:
                        messages.error(request, "❌ Please fix the errors in Taxes & Finance.")
            elif section == "theme":
                if theme_form.is_valid():
                    theme_form.save()
                    cache_key = f"company_branding_{request.user.id}"
                    cache.delete(cache_key)
                    if is_spanish:
                        messages.success(request, "✅ Tema y colores guardados exitosamente.")
                    else:
                        messages.success(request, "✅ Theme and colors saved.")
                    return redirect(request.path)
                else:
                    if is_spanish:
                        messages.error(
                            request, "❌ Por favor corrija los errores en Tema y Colores."
                        )
                    else:
                        messages.error(request, "❌ Please fix the errors in Theme & Colors.")
            elif section == "modules":
                if rubro_form.is_valid():
                    rubro_form.save()
                    if is_spanish:
                        messages.success(request, "✅ Rubro y módulos actualizados.")
                    else:
                        messages.success(request, "✅ Industry and modules updated.")
                    return redirect(request.path)
                else:
                    if is_spanish:
                        messages.error(
                            request, "❌ Por favor corrija los errores en Rubro y Módulos."
                        )
                    else:
                        messages.error(request, "❌ Please fix the errors in Industry & Modules.")
    else:
        # GET request - crear formularios limpios
        profile_form = CompanyProfileForm(instance=config)
        empresa_form = ConfiguracionEmpresaForm(instance=config_empresa)
        financial_form = FinancialSettingsForm(instance=config)
        theme_form = ThemeSettingsForm(instance=config)
        rubro_form = ConfiguracionRubroForm(instance=config_empresa, request=request)

    # Obtener técnicos
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    # Preparar contexto
    context = {
        "tecnicos": tecnicos,
        "config": config,
        "config_empresa": config_empresa,
        "empresa": empresa,
        "profile_form": profile_form,
        "empresa_form": empresa_form,
        "financial_form": financial_form,
        "theme_form": theme_form,
        "rubro_form": rubro_form,
    }

    # Usar template compacto
    template_name = "taller/settings/centro_ajustes_compacto.html"
    return render(request, template_name, context)
