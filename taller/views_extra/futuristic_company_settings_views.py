import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from taller.context_processors import invalidate_company_cache
from taller.forms.company_settings_forms import (
    CompanyProfileForm,
    CompanySettingsForm,
    FinancialSettingsForm,
    ThemeSettingsForm,
)
from taller.models import Tecnico
from taller.models.company_settings import CompanySettings
from taller.utils.empresa import get_or_create_empresa
from taller.utils.pais_utils import get_configuracion_pais


@login_required(login_url=None)
def futuristic_company_settings_view(request):
    """
    Vista futurista para configuración de empresa y gestión de técnicos
    Usa el mismo template que company_settings_view para mantener consistencia
    """
    empresa = get_or_create_empresa(request)

    # Usar CompanySettings en lugar de ConfiguracionEmpresa (igual que company_settings_view)
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

    # Usar el mismo template que company_settings_view
    if empresa.pais in {"CL", "MX", "PE", "VE", "BR"}:
        template_name = "settings/company_settings_es.html"
    else:
        template_name = "settings/company_settings.html"

    return render(
        request,
        template_name,
        {"form": form, "tecnicos": tecnicos, "config": config, "empresa": empresa},
    )


def handle_company_settings(request, company_settings):
    """
    Maneja la actualización de configuración de empresa
    """
    try:
        # Actualizar campos básicos
        company_settings.company_name = request.POST.get("company_name", "")
        company_settings.tagline = request.POST.get("tagline", "")
        company_settings.address = request.POST.get("address", "")
        company_settings.phone = request.POST.get("phone", "")
        company_settings.email = request.POST.get("email", "")
        company_settings.website = request.POST.get("website", "")
        company_settings.primary_color = request.POST.get("primary_color", "#00ffff")
        company_settings.currency = request.POST.get("currency", "USD")

        # Manejar logo
        if "logo" in request.FILES:
            company_settings.logo = request.FILES["logo"]

        company_settings.save()

        # Actualizar también la empresa principal
        empresa = company_settings.user.empresa
        empresa.nombre_taller = company_settings.company_name
        empresa.telefono = company_settings.phone
        empresa.email = company_settings.email
        empresa.direccion = company_settings.address
        empresa.save()

        # Invalidar caché para actualizar la cabecera
        invalidate_company_cache(request.user)

        messages.success(request, "✅ Company profile updated successfully!")

    except Exception as e:
        messages.error(request, f"❌ Error updating company profile: {str(e)}")

    return redirect(request.path)


def handle_technician_management(request, empresa):
    """
    Maneja la gestión de técnicos (agregar, editar, activar/desactivar, eliminar)
    """
    action = request.POST.get("action")

    try:
        if action == "add":
            return add_technician(request, empresa)
        elif action == "toggle":
            return toggle_technician(request, empresa)
        elif action == "delete":
            return delete_technician(request, empresa)
        elif action == "edit":
            return edit_technician(request, empresa)

    except Exception as e:
        messages.error(request, f"❌ Error in technician management: {str(e)}")

    return redirect(request.path)


def add_technician(request, empresa):
    """
    Agrega un nuevo técnico
    """
    nombre = request.POST.get("nombre", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    direccion = request.POST.get("direccion", "").strip()

    if not nombre or len(nombre) < 2:
        messages.error(request, "❌ Technician name must be at least 2 characters long.")
        return redirect(request.path)

    # Verificar si ya existe un técnico con ese nombre
    if Tecnico.objects.filter(empresa=empresa, nombre__iexact=nombre).exists():
        messages.error(request, f"❌ A technician named '{nombre}' already exists.")
        return redirect(request.path)

    tecnico = Tecnico.objects.create(
        empresa=empresa,
        nombre=nombre,
        telefono=telefono if telefono else None,
        direccion=direccion if direccion else None,
        activo=True,
    )

    messages.success(request, f"✅ Technician '{nombre}' added successfully!")
    return redirect(request.path)


def toggle_technician(request, empresa):
    """
    Activa o desactiva un técnico
    """
    technician_id = request.POST.get("technician_id")
    activate = request.POST.get("activate") == "true"

    try:
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        tecnico.activo = activate
        tecnico.save()

        status = "activated" if activate else "deactivated"
        messages.success(request, f"✅ Technician '{tecnico.nombre}' {status} successfully!")

    except Tecnico.DoesNotExist:
        messages.error(request, "❌ Technician not found.")

    return redirect(request.path)


def delete_technician(request, empresa):
    """
    Elimina un técnico
    """
    technician_id = request.POST.get("technician_id")

    try:
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        nombre = tecnico.nombre
        tecnico.delete()

        messages.success(request, f"✅ Technician '{nombre}' deleted successfully!")

    except Tecnico.DoesNotExist:
        messages.error(request, "❌ Technician not found.")

    return redirect(request.path)


def edit_technician(request, empresa):
    """
    Edita un técnico existente
    """
    technician_id = request.POST.get("technician_id")
    nombre = request.POST.get("nombre", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    direccion = request.POST.get("direccion", "").strip()

    if not nombre or len(nombre) < 2:
        messages.error(request, "❌ Technician name must be at least 2 characters long.")
        return redirect(request.path)

    try:
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        tecnico.nombre = nombre
        tecnico.telefono = telefono if telefono else None
        tecnico.direccion = direccion if direccion else None
        tecnico.save()

        messages.success(request, f"✅ Technician '{nombre}' updated successfully!")

    except Tecnico.DoesNotExist:
        messages.error(request, "❌ Technician not found.")

    return redirect(request.path)


@csrf_exempt
@require_http_methods(["POST"])
def api_technician_toggle(request):
    """
    API endpoint para toggle de técnicos via AJAX
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
        technician_id = data.get("technician_id")
        activate = data.get("activate", False)

        empresa = request.user.empresa
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        tecnico.activo = activate
        tecnico.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Technician {tecnico.nombre} {'activated' if activate else 'deactivated'} successfully!",
                "technician": {
                    "id": tecnico.id,
                    "nombre": tecnico.nombre,
                    "activo": tecnico.activo,
                },
            }
        )

    except Tecnico.DoesNotExist:
        return JsonResponse({"error": "Technician not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_technician_delete(request):
    """
    API endpoint para eliminar técnicos via AJAX
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
        technician_id = data.get("technician_id")

        empresa = request.user.empresa
        tecnico = Tecnico.objects.get(id=technician_id, empresa=empresa)
        nombre = tecnico.nombre
        tecnico.delete()

        return JsonResponse(
            {"success": True, "message": f"Technician '{nombre}' deleted successfully!"}
        )

    except Tecnico.DoesNotExist:
        return JsonResponse({"error": "Technician not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
