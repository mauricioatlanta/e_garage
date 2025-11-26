from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render

from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    CompanySettingsForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.models import Tecnico
from taller.models.company_settings import CompanySettings
from taller.utils.empresa import get_or_create_empresa  # tu helper
from taller.utils.pais_utils import get_configuracion_pais


@login_required(login_url=None)  # usa tu LOGIN_URL global
def company_settings_view(request):
    empresa = get_or_create_empresa(request)

    # Usar CompanySettings en lugar de ConfiguracionEmpresa
    try:
        config = CompanySettings.objects.get(user=request.user)
    except CompanySettings.DoesNotExist:
        # Crear configuración nueva si no existe
        country_config = get_configuracion_pais(empresa)
        config = CompanySettings.objects.create(
            user=request.user,
            company_name=empresa.nombre_taller or "Mi Empresa",
            tagline="",
            primary_color="#0d6efd",
            secondary_color="#6c757d",
            currency=country_config.get("moneda", "CLP"),
        )

    if request.method == "POST":
        # Verificar si es un formulario de técnico
        if "crear_tecnico" in request.POST:
            # Manejar creación de técnico
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
                    is_spanish = empresa.pais in {"CL", "MX", "PE", "VE", "BR"}
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
                if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
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

                is_spanish = empresa.pais in {"CL", "MX", "PE", "VE", "BR"}
                if is_spanish:
                    estado = "activado" if tecnico.activo else "desactivado"
                    messages.success(
                        request, f"✅ Técnico '{tecnico.nombre}' {estado} exitosamente."
                    )
                else:
                    estado = "activated" if tecnico.activo else "deactivated"
                    messages.success(
                        request,
                        f"✅ Technician '{tecnico.nombre}' {estado} successfully.",
                    )
            except Tecnico.DoesNotExist:
                if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
                    messages.error(request, "❌ Técnico no encontrado.")
                else:
                    messages.error(request, "❌ Technician not found.")
            except Exception as e:
                if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
                    messages.error(request, f"❌ Error al actualizar técnico: {str(e)}")
                else:
                    messages.error(request, f"❌ Error updating technician: {str(e)}")

            return redirect(request.path)

        # Manejar formulario de configuración de empresa
        else:
            # Obtener la sección del formulario
            section = request.POST.get("section", "profile")

            # Seleccionar el formulario apropiado según la sección
            if section == "profile":
                form = CompanyProfileForm(request.POST, request.FILES, instance=config)
            elif section == "financial":
                form = FinancialSettingsForm(request.POST, instance=config)
            elif section == "theme":
                form = ThemeSettingsForm(request.POST, instance=config)
            else:
                # Fallback al formulario completo
                form = CompanySettingsForm(request.POST, request.FILES, instance=config)

            if form.is_valid():
                try:
                    cfg = form.save()

                    # Invalidar caché de branding para que se actualice en todas las páginas
                    cache_key = f"company_branding_{request.user.id}"
                    cache.delete(cache_key)

                    # Mensaje específico si se subió logo
                    if section == "profile" and "logo" in request.FILES:
                        if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
                            messages.success(
                                request,
                                "✅ ¡Logo subido exitosamente! Su logo ahora aparecerá en todas las páginas. Refresque las páginas abiertas para verlo.",
                            )
                        else:
                            messages.success(
                                request,
                                "✅ Logo uploaded successfully! Your logo will now appear across all pages. Refresh any open pages to see it.",
                            )
                    else:
                        if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
                            section_names = {
                                "profile": "Perfil",
                                "financial": "Financiera",
                                "theme": "Tema",
                            }
                            section_name = section_names.get(section, section.title())
                            messages.success(
                                request,
                                f"✅ Configuración {section_name} actualizada exitosamente. Los cambios se reflejarán en todas las páginas.",
                            )
                        else:
                            messages.success(
                                request,
                                f"✅ {section.title()} configuration updated successfully. Changes will be reflected across all pages.",
                            )
                    return redirect(request.path)
                except Exception as e:
                    if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
                        messages.error(request, f"❌ Error al guardar la configuración: {str(e)}")
                    else:
                        messages.error(request, f"❌ Error saving configuration: {str(e)}")
            else:
                # Mostrar errores específicos del formulario
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")

                if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
                    messages.error(
                        request,
                        f"❌ Por favor revise los campos del formulario: {'; '.join(error_messages)}",
                    )
                else:
                    messages.error(
                        request,
                        f"❌ Please check the form fields: {'; '.join(error_messages)}",
                    )
    else:
        form = CompanySettingsForm(instance=config)

    # Obtener técnicos de la empresa
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    # Seleccionar el template apropiado según el país
    if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
        template_name = "settings/company_settings_es.html"
    else:
        template_name = "settings/company_settings.html"

    return render(
        request,
        template_name,
        {"form": form, "tecnicos": tecnicos, "config": config, "empresa": empresa},
    )
