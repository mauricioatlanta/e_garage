from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render

from taller.forms.configuracion_empresa import ConfiguracionEmpresaForm
from taller.forms.company_settings_forms import (
    CompanySettingsForm, CompanyProfileForm, FinancialSettingsForm, ThemeSettingsForm
)
from taller.models.company_settings import CompanySettings
from taller.models import Tecnico
from taller.utils.empresa import get_or_create_empresa  # tu helper


@login_required(login_url=None)  # usa tu LOGIN_URL global
def company_settings_view(request):
    empresa = get_or_create_empresa(request)
    
    # Usar CompanySettings en lugar de ConfiguracionEmpresa
    try:
        config = CompanySettings.objects.get(user=request.user)
    except CompanySettings.DoesNotExist:
        # Crear configuración nueva si no existe
        config = CompanySettings.objects.create(
            user=request.user,
            company_name=empresa.nombre_taller or "Mi Empresa",
            tagline="",
            primary_color="#0d6efd",
            secondary_color="#6c757d",
            currency="CLP" if empresa.pais == "CL" else "USD"
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
                    messages.success(
                        request, f"✅ Técnico '{nombre}' creado exitosamente."
                    )
                except Exception as e:
                    messages.error(request, f"❌ Error al crear técnico: {str(e)}")
            else:
                messages.error(request, "❌ El nombre del técnico es obligatorio.")

            return redirect(request.path)

        # Manejar toggle de técnico
        elif "toggle_tecnico" in request.POST:
            tecnico_id = request.POST.get("toggle_tecnico")
            try:
                tecnico = Tecnico.objects.get(id=tecnico_id, empresa=empresa)
                tecnico.activo = not tecnico.activo
                tecnico.save()
                estado = "activado" if tecnico.activo else "desactivado"
                messages.success(
                    request, f"✅ Técnico '{tecnico.nombre}' {estado} exitosamente."
                )
            except Tecnico.DoesNotExist:
                messages.error(request, "❌ Técnico no encontrado.")
            except Exception as e:
                messages.error(request, f"❌ Error al actualizar técnico: {str(e)}")

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

                    messages.success(
                        request,
                        f"✅ {section.title()} configuration updated successfully. Changes will be reflected across all pages.",
                    )
                    return redirect(request.path)
                except Exception as e:
                    messages.error(
                        request, f"❌ Error saving configuration: {str(e)}"
                    )
            else:
                # Mostrar errores específicos del formulario
                error_messages = []
                for field, errors in form.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                
                messages.error(
                    request, f"❌ Please check the form fields: {'; '.join(error_messages)}"
                )
    else:
        form = CompanySettingsForm(instance=config)

    # Obtener técnicos de la empresa
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

    return render(
        request, "settings/company_settings.html", {"form": form, "tecnicos": tecnicos, "config": config}
    )
