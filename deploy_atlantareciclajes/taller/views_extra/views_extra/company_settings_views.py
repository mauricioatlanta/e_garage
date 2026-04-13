from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render

from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.forms.configuracion_forms import ConfiguracionRubroForm
from taller.models import Tecnico
from taller.models.company_settings import CompanySettings
from taller.models.configuracion import ConfiguracionEmpresa
from taller.utils.empresa import get_or_create_empresa
from taller.utils.pais_utils import get_configuracion_pais


@login_required(login_url=None)
def company_settings_view(request):
    empresa = get_user_empresa_safe(request.user)
    config_empresa, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)

    # Obtener o crear configuración
    try:
        config = CompanySettings.objects.get(user=request.user)
        # Sincronizar datos desde ConfiguracionEmpresa si están disponibles
        # Solo actualizar campos vacíos en CompanySettings si hay datos en ConfiguracionEmpresa
        if config_empresa:
            needs_save = False
            if config_empresa.telefono and not config.phone:
                config.phone = config_empresa.telefono
                needs_save = True
            if config_empresa.email_contacto and not config.email:
                config.email = config_empresa.email_contacto
                needs_save = True
            if config_empresa.sitio_web and not config.website:
                config.website = config_empresa.sitio_web
                needs_save = True
            if config_empresa.direccion and not config.address:
                config.address = config_empresa.direccion
                needs_save = True
            if config_empresa.tagline and not config.tagline:
                config.tagline = config_empresa.tagline
                needs_save = True
            if needs_save:
                config.save()
    except CompanySettings.DoesNotExist:
        country_config = get_configuracion_pais(empresa)
        # Sincronizar datos desde ConfiguracionEmpresa si están disponibles
        config = CompanySettings.objects.create(
            user=request.user,
            company_name=empresa.nombre_taller or "Mi Empresa",
            tagline=config_empresa.tagline if config_empresa else "",
            address=config_empresa.direccion if config_empresa and config_empresa.direccion else "",
            phone=config_empresa.telefono if config_empresa and config_empresa.telefono else "",
            email=(
                config_empresa.email_contacto
                if config_empresa and config_empresa.email_contacto
                else ""
            ),
            website=config_empresa.sitio_web if config_empresa and config_empresa.sitio_web else "",
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
            financial_form = FinancialSettingsForm(request.POST or None, instance=config)
            theme_form = ThemeSettingsForm(request.POST or None, instance=config)

            # Validar y guardar según la sección
            if section == "profile":
                if profile_form.is_valid():
                    profile_form.save()
                    # Recargar config para obtener los valores actualizados
                    config.refresh_from_db()
                    # Sincronizar datos de vuelta a ConfiguracionEmpresa
                    if config_empresa:
                        config_empresa.tagline = config.tagline
                        config_empresa.direccion = config.address
                        config_empresa.telefono = config.phone
                        config_empresa.email_contacto = config.email
                        config_empresa.sitio_web = config.website
                        config_empresa.save()
                    cache_key = f"company_branding_{request.user.id}"
                    cache.delete(cache_key)
                    if is_spanish:
                        messages.success(
                            request, "✅ Información de empresa guardada exitosamente."
                        )
                    else:
                        messages.success(request, "✅ Company information saved.")
                    return redirect(request.path)
                else:
                    if is_spanish:
                        messages.error(
                            request, "❌ Por favor corrija los errores en Información de Empresa."
                        )
                    else:
                        messages.error(request, "❌ Please fix the errors in Company Information.")
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
        financial_form = FinancialSettingsForm(instance=config)
        theme_form = ThemeSettingsForm(instance=config)
        rubro_form = ConfiguracionRubroForm(instance=config_empresa, request=request)

    # Obtener técnicos
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    # Preparar contexto
    context = {
        "tecnicos": tecnicos,
        "config": config,
        "empresa": empresa,
        "profile_form": profile_form,
        "financial_form": financial_form,
        "theme_form": theme_form,
        "rubro_form": rubro_form,
    }

    # Usar template compacto (hub de navegación)
    template_name = "taller/settings/centro_ajustes.html"
    return render(request, template_name, context)
