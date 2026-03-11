import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse

from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.forms.configuracion_empresa import ConfiguracionEmpresaForm
from taller.forms.configuracion_forms import ConfiguracionRubroForm
from taller.models import Tecnico
from taller.models.company_settings import CompanySettings
from taller.models.configuracion import ConfiguracionEmpresa
from taller.context_processors.company_header import invalidate_company_header_cache
from taller.utils.empresa import get_or_create_empresa
from taller.utils.pais_utils import get_configuracion_pais

logger = logging.getLogger(__name__)


def _redirect_on_settings_error(request):
    """Redirige al centro de operaciones simple dentro del contexto del país (no a la raíz)."""
    path = request.path or ""
    if "/us/" in path or path.startswith("/us"):
        try:
            return redirect(reverse("usa:centro_operaciones"))
        except Exception:
            return redirect("/us/centro-operaciones/")
    elif "/cl/" in path or path.startswith("/cl"):
        try:
            return redirect(reverse("chile:centro_operaciones"))
        except Exception:
            return redirect("/cl/es/centro-operaciones/")
    try:
        return redirect(reverse("chile:centro_operaciones"))
    except Exception:
        return redirect("/cl/es/centro-operaciones/")


@login_required(login_url=None)
def company_settings_view(request):
    try:
        empresa = get_or_create_empresa(request)
    except Exception as e:
        logger.exception(
            "company_settings: error en get_or_create_empresa (usuario=%s)",
            getattr(request.user, "pk", None),
        )
        raise  # DEBUG: quitar redirect para ver el error real

    try:
        config_empresa, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
    except Exception as e:
        logger.exception(
            "company_settings: error en ConfiguracionEmpresa (empresa_id=%s)",
            getattr(empresa, "pk", None),
        )
        raise  # DEBUG: quitar redirect para ver el error real

    # Obtener o crear configuración
    try:
        config = CompanySettings.objects.get(user=request.user)
    except CompanySettings.DoesNotExist:
        try:
            try:
                country_config = get_configuracion_pais(empresa)
                currency = country_config.get("currency") or country_config.get("moneda", "CLP")
            except Exception:
                currency = "USD" if ("/us/" in (request.path or "")) else "CLP"
            config = CompanySettings.objects.create(
                user=request.user,
                company_name=empresa.nombre_taller or "Mi Empresa",
                tagline="",
                primary_color="#0d6efd",
                secondary_color="#6c757d",
                currency=currency,
            )
        except Exception as e:
            logger.exception(
                "company_settings: error al crear CompanySettings (user_id=%s)",
                getattr(request.user, "pk", None),
            )
            # Reintentar get por si se creó en paralelo (race)
            try:
                config = CompanySettings.objects.get(user=request.user)
            except CompanySettings.DoesNotExist:
                raise  # DEBUG: quitar redirect para ver el error real
    except Exception as e:
        logger.exception(
            "company_settings: redirect por error al obtener CompanySettings (user_id=%s)",
            getattr(request.user, "pk", None),
        )
        return _redirect_on_settings_error(request)

    # Asegurar que empresa.pais tenga un valor por defecto
    empresa_pais = getattr(empresa, "pais", "CL") or "CL"
    is_spanish = empresa_pais in {"CL", "MX", "PE", "VE", "BR"}

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
                request=request,
            )
            financial_form = FinancialSettingsForm(request.POST or None, instance=config)
            theme_form = ThemeSettingsForm(request.POST or None, instance=config)

            # Validar y guardar según la sección
            if section == "profile":
                # Solo validar el formulario de CompanySettings (nombre, lema, dirección, etc.).
                # NO usar empresa_form.is_valid() aquí: el POST solo trae campos de profile_form
                # y empresa_form tiene otros nombres (nombre_publico, direccion...); guardarlo
                # sobrescribiría ConfiguracionEmpresa con valores vacíos.
                if profile_form.is_valid():
                    profile_form.save()
                    # Logo: si se subió uno nuevo, guardarlo en ConfiguracionEmpresa (sin tocar el resto)
                    logo_file = request.FILES.get("logo")
                    if logo_file:
                        from taller.forms.configuracion_empresa import MAX_LOGO_MB

                        if logo_file.size <= MAX_LOGO_MB * 1024 * 1024:
                            config_empresa.logo = logo_file
                            config_empresa.save(update_fields=["logo"])
                        else:
                            messages.warning(
                                request,
                                (
                                    ("Logo no guardado: tamaño máximo %s MB." % MAX_LOGO_MB)
                                    if is_spanish
                                    else ("Logo not saved: max size %s MB." % MAX_LOGO_MB)
                                ),
                            )
                    # Sincronizar nombre y lema a ConfiguracionEmpresa para el header
                    config_empresa.nombre_publico = (
                        getattr(config, "company_name", "") or ""
                    ).strip()
                    config_empresa.tagline = (getattr(config, "tagline", "") or "").strip()
                    config_empresa.save(update_fields=["nombre_publico", "tagline"])
                    cache.delete(f"company_branding_{request.user.id}")
                    invalidate_company_header_cache(empresa.id)

                    messages.success(
                        request,
                        (
                            "✅ Información de empresa guardada exitosamente."
                            if is_spanish
                            else "✅ Company information saved."
                        ),
                    )
                    return redirect(request.path)

                messages.error(
                    request,
                    (
                        "❌ Corrige los errores en Información de Empresa."
                        if is_spanish
                        else "❌ Please fix the errors in Company Information."
                    ),
                )
                if profile_form.errors:
                    logger.debug("company_settings profile errors: %s", profile_form.errors)
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
                    cache.delete(f"company_branding_{request.user.id}")
                    invalidate_company_header_cache(empresa.id)
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
        try:
            profile_form = CompanyProfileForm(instance=config)
            empresa_form = ConfiguracionEmpresaForm(
                instance=config_empresa,
                request=request,
            )
            financial_form = FinancialSettingsForm(instance=config)
            theme_form = ThemeSettingsForm(instance=config)
            rubro_form = ConfiguracionRubroForm(instance=config_empresa, request=request)
        except Exception as e:
            logger.exception("company_settings: error al inicializar formularios")
            raise  # DEBUG: quitar redirect para ver el error real

    # Obtener técnicos
    try:
        tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")
    except Exception as e:
        # Si hay error al obtener técnicos, usar lista vacía
        tecnicos = []
        logger.warning("Error al obtener técnicos: %s", e)

    # Preparar contexto (company_settings para base.html footer y otros)
    context = {
        "tecnicos": tecnicos,
        "config": config,
        "config_empresa": config_empresa,
        "empresa": empresa,
        "empresa_pais": empresa_pais,
        "company_settings": config,  # base.html usa company_settings en footer
        "profile_form": profile_form,
        "empresa_form": empresa_form,
        "financial_form": financial_form,
        "theme_form": theme_form,
        "rubro_form": rubro_form,
    }

    # Usar template principal
    template_name = "taller/settings/centro_ajustes.html"
    try:
        return render(request, template_name, context)
    except Exception as e:
        logger.exception("company_settings: error al renderizar centro_ajustes.html")
        raise  # DEBUG: quitar redirect para ver el error real
